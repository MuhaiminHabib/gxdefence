"""Replay saved attacks on fresh GNNExplainer seeds with random-mask controls."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
import argparse, copy, hashlib, json, random, sys, time, traceback
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import torch
from torch_geometric.utils import k_hop_subgraph
from torch_geometric.explain import Explainer, GNNExplainer

ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent
sys.path.insert(0,str(STUDY/'complete_graphs'))
from prepare import MarasiGraphSAGE, sha, save, seed
from attack_core import EdgeIds, gnn_explain, fidelity, compare, binary_top25
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
OUT=ROOT/'results/gnn_audit'
METHODS=['GNN-targeted GX adaptation','Random search','Random flipping']
CONFIG=dict(datasets=['amlsim','hi_small'],targets_per_dataset=50,subset_seed=314159,
            source_trial=2026,explanation_seeds=list(range(41001,41006)),
            clean_repeat_seeds=list(range(51001,51006)),random_masks=20,k=10,
            gnn_epochs=100,methods=METHODS,device='cuda',cpu_threads=1)
FID=['hard_plus','hard_minus','soft_plus','soft_minus']

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()

def freeze_manifest():
    rng=np.random.default_rng(CONFIG['subset_seed']);targets={};inputs={}
    for name in CONFIG['datasets']:
        census=STUDY/f'complete_graphs/results/full/{name}_targets.json'
        eligible=sorted(json.loads(census.read_text())['selected'])
        targets[name]=sorted(int(v) for v in rng.choice(eligible,50,replace=False))
        inputs[str(census.relative_to(STUDY))]=sha(census)
        checkpoint=STUDY/f'complete_graphs/prepared/{name}.pt'
        inputs[str(checkpoint.relative_to(STUDY))]=sha(checkpoint)
        for target in targets[name]:
            p=STUDY/f'gnn_three_trials/results/full/cases/{name}_{target}_2026.json'
            inputs[str(p.relative_to(STUDY))]=sha(p)
    for p in [Path(__file__),ROOT/'README.md',STUDY/'complete_graphs/attack_core.py',
              STUDY/'complete_graphs/prepare.py',STUDY/'framework/src/models/marasi_models.py']:
        inputs[str(p.relative_to(STUDY))]=sha(p)
    manifest=dict(config=CONFIG,targets=targets,inputs=inputs,
                  torch=torch.__version__,pyg=__import__('torch_geometric').__version__)
    path=OUT/'manifest.json'
    if path.exists():
        assert json.loads(path.read_text())==manifest,'Audit provenance changed; use a separate output folder.'
    else:save(path,manifest)
    return manifest

def physical(data,edit_ids):
    removed=[int(v[1:]) for v in edit_ids if v.startswith('E')]
    added=[v for v in edit_ids if v.startswith('A')]
    assert len(removed)+len(added)==len(edit_ids) and len(set(edit_ids))==len(edit_ids)
    keep=torch.ones(data.edge_index.shape[1],dtype=torch.bool)
    keep[removed]=False
    e=data.edge_index[:,keep]
    if added:
        pairs=torch.tensor([list(map(int,v[1:].split(':'))) for v in added],dtype=torch.long).T
        e=torch.cat([e,pairs],dim=1)
    return e,EdgeIds(keep.nonzero().flatten().numpy(),added)

def local_graph(data,e,ids,target):
    nodes,local,mapping,mask=k_hop_subgraph(target,2,e,relabel_nodes=True,num_nodes=data.num_nodes)
    selected=mask.nonzero().flatten().tolist()
    return dict(x=data.x[nodes].to('cuda'),edge=local.to('cuda'),target=int(mapping),
                ids=[ids[i] for i in selected],global_nodes=nodes.tolist())

def explain(model,g,s):
    seed(s)
    if g['edge'].shape[1]==0:return {}
    ex=Explainer(model=model,algorithm=GNNExplainer(epochs=CONFIG['gnn_epochs']),
                 explanation_type='model',edge_mask_type='object',
                 model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
    explanation=ex(g['x'],g['edge'],index=g['target'])
    scores=dict(zip(g['ids'],explanation.edge_mask.detach().cpu().tolist()))
    assert all(np.isfinite(v) for v in scores.values())
    return scores

@torch.no_grad()
def predict(model,g):
    out=model(g['x'],g['edge'])[g['target']]
    return out,int(out.argmax())

@torch.no_grad()
def fid_indices(model,g,indices):
    selected=torch.zeros(g['edge'].shape[1],device='cuda',dtype=torch.bool)
    selected[indices]=True
    baseline,label=predict(model,g);p=float(baseline.softmax(-1)[label])
    removed=model(g['x'],g['edge'][:,~selected])[g['target']]
    retained=model(g['x'],g['edge'][:,selected])[g['target']]
    return dict(hard_plus=int(removed.argmax()!=label),hard_minus=int(retained.argmax()!=label),
                soft_plus=p-float(removed.softmax(-1)[label]),soft_minus=p-float(retained.softmax(-1)[label]))

def fid_scores(model,g,scores):
    selected=set(sorted(scores,key=lambda i:(-scores[i],i))[:CONFIG['k']])
    return fid_indices(model,g,[j for j,k in enumerate(g['ids']) if k in selected])

def random_control(model,g,s):
    rng=np.random.default_rng(s);n=len(g['ids']);k=min(CONFIG['k'],n)
    samples=[]
    for _ in range(CONFIG['random_masks']):
        indices=sorted(int(v) for v in rng.choice(n,k,replace=False))
        samples.append(dict(selected_ids=[g['ids'][i] for i in indices],**fid_indices(model,g,indices)))
    return dict(seed=s,pool_size=n,selected_size=k,samples=samples,
                mean={m:float(np.mean([r[m] for r in samples])) for m in FID})

def assert_scores(a,b):
    assert a.keys()==b.keys(),'Explanation edge IDs differ'
    keys=sorted(a)
    if keys:
        torch.testing.assert_close(torch.tensor([a[k] for k in keys]),torch.tensor([b[k] for k in keys]),atol=5e-4,rtol=5e-4)
    return max((abs(a[k]-b[k]) for k in keys),default=0.)

def validate_graph(model,data,e,ids,target,g,own_scores,saved_scores):
    full_x=data.x.to('cuda');full_e=e.to('cuda')
    ctx=SimpleNamespace(target=target,c=SimpleNamespace(x=full_x,n=data.num_nodes,model=model))
    native=gnn_explain(ctx,full_e,ids,2026)
    delta=assert_scores(own_scores,native)
    saved_delta=assert_scores(own_scores,saved_scores)
    ref=fidelity(ctx,full_e,ids,own_scores,10);ours=fid_scores(model,g,own_scores)
    mapping=dict(hard_plus='necessity',hard_minus='sufficiency_failure',soft_plus='removed_probability_drop',soft_minus='kept_probability_gap')
    for k,v in mapping.items():assert abs(ours[k]-ref[v])<3e-5,(k,ours[k],ref[v])
    return dict(native_mask_max_error=delta,saved_mask_max_error=saved_delta,native_physical_fidelity_parity=True)

def one_case(name,target,data,model,manifest_id,validate=False):
    started=time.time();path=STUDY/f'gnn_three_trials/results/full/cases/{name}_{target}_2026.json'
    source=json.loads(path.read_text());graphs={};old_scores={};randoms={};validation={}
    frozen={k:v.clone() for k,v in model.state_dict().items()}
    for i,method in enumerate(['Clean']+METHODS):
        edit_ids=[] if method=='Clean' else source['attacks'][method]['edge_ids']
        if method!='Clean':assert len(edit_ids)==6
        e,ids=physical(data,edit_ids);g=local_graph(data,e,ids,target);graphs[method]=g
        saved=source['clean']['GNNExplainer'] if method=='Clean' else source['attacks'][method]['scores']
        old_scores[method]=explain(model,g,2026)
        err=assert_scores(old_scores[method],saved)
        logits,label=predict(model,g)
        if method=='Clean':clean_label=label
        else:
            expected=source['attacks'][method]
            assert (label==clean_label)==bool(expected['preserved'])
            assert abs(float(logits.softmax(-1)[clean_label])-expected['probability'])<3e-4
        validation[method]=dict(saved_mask_max_error=err,saved_prediction_parity=True)
        if validate and method in ['Clean',METHODS[0]]:
            validation[method].update(validate_graph(model,data,e,ids,target,g,old_scores[method],saved))
        randoms[method]=random_control(model,g,60000+target*17+i+(0 if name=='amlsim' else 10000000))
        del e,ids
    rows=[];mask_evidence={}
    all_seeds=[2026]+CONFIG['explanation_seeds']
    for ix,s in enumerate(all_seeds):
        fresh=ix>0
        scores={m:explain(model,g,s) for m,g in graphs.items()} if fresh else old_scores
        fids={m:fid_scores(model,g,scores[m]) for m,g in graphs.items()}
        repseed=CONFIG['clean_repeat_seeds'][ix-1] if fresh else 12026
        repeated=explain(model,graphs['Clean'],repseed)
        clean_repeat=dict(**compare(scores['Clean'],repeated,10),**binary_top25(scores['Clean'],repeated))
        mask_evidence[str(s)]=dict(scores=scores,clean_repeat_seed=repseed,clean_repeat_scores=repeated)
        for method in METHODS:
            overlap=dict(**compare(scores['Clean'],scores[method],10),**binary_top25(scores['Clean'],scores[method]))
            r=dict(dataset=name,target=target,source_trial=2026,explanation_seed=s,stage='fresh' if fresh else 'selection_seed',
                   method=method,preserved=int(source['attacks'][method]['preserved']),
                   delta_prob=abs(float(predict(model,graphs['Clean'])[0].softmax(-1)[clean_label])-source['attacks'][method]['probability']),**overlap)
            for metric in ['cosine','jaccard','binary_top25_cosine']:r['clean_repeat_'+metric]=clean_repeat[metric]
            for metric in FID:
                cf=fids['Clean'][metric];af=fids[method][metric];cr=randoms['Clean']['mean'][metric];ar=randoms[method]['mean'][metric]
                r.update({f'clean_{metric}':cf,f'attacked_{metric}':af,f'random_clean_{metric}':cr,f'random_attacked_{metric}':ar,
                          f'clean_excess_{metric}':cf-cr,f'attacked_excess_{metric}':af-ar,f'delta_excess_{metric}':(af-ar)-(cf-cr)})
            rows.append(r)
    for key,v in frozen.items():torch.testing.assert_close(v,model.state_dict()[key],atol=0,rtol=0)
    torch.cuda.synchronize()
    return dict(dataset=name,target=target,manifest_id=manifest_id,source_sha256=sha(path),seconds=time.time()-started,
                validation=validation,random_controls=randoms,explanations=mask_evidence,rows=rows,
                graph_details={m:dict(nodes=len(g['global_nodes']),edges=len(g['ids']),global_nodes=g['global_nodes'],ids=g['ids']) for m,g in graphs.items()})

def report(manifest_id):
    rows=[];times=[]
    for p in sorted((OUT/'cases').glob('*.json')):
        d=json.loads(p.read_text());assert d['manifest_id']==manifest_id
        rows.extend(d['rows']);times.append(d['seconds'])
    if not rows:return
    df=pd.DataFrame(rows);df.to_csv(OUT/'per_seed.csv',index=False)
    keys=['dataset','target','method','stage']
    metrics=['binary_top25_cosine','jaccard','cosine','clean_repeat_binary_top25_cosine','preserved','delta_prob']
    metrics += [f'{prefix}_{m}' for prefix in ['clean','attacked','random_clean','random_attacked','clean_excess','attacked_excess','delta_excess'] for m in FID]
    target=df.groupby(keys)[metrics].mean().reset_index();target.to_csv(OUT/'per_target.csv',index=False)
    rng=np.random.default_rng(714);summ=[]
    for (name,method,stage),g in target.groupby(['dataset','method','stage']):
        for population,gg in [('all',g),('prediction_preserved',g[g.preserved==1])]:
            if gg.empty:continue
            a=gg[metrics].to_numpy(); draws=rng.integers(0,len(a),(3000,len(a)))
            boot=a[draws].mean(axis=1)
            for j,m in enumerate(metrics):
                summ.append(dict(dataset=name,method=method,stage=stage,population=population,targets=len(a),metric=m,mean=float(a[:,j].mean()),lo=float(np.quantile(boot[:,j],.025)),hi=float(np.quantile(boot[:,j],.975))))
    pd.DataFrame(summ).to_csv(OUT/'summary.csv',index=False)
    # Paired fresh-minus-selection change after averaging the five fresh seeds.
    paired=[]
    for (name,method),g in target.groupby(['dataset','method']):
        table=g.pivot(index='target',columns='stage',values='binary_top25_cosine')
        a=(table['fresh']-table['selection_seed']).to_numpy()
        boot=a[rng.integers(0,len(a),(3000,len(a)))].mean(axis=1)
        paired.append(dict(dataset=name,method=method,targets=len(a),fresh_minus_selection=float(a.mean()),lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975))))
    pd.DataFrame(paired).to_csv(OUT/'seed_generalization.csv',index=False)
    n=len(times);complete=n==100
    lines=['# Fresh-seed and random-explanation audit','',f'**{"COMPLETE" if complete else "PROVISIONAL"}: {n}/100 preselected targets saved.**','',
           'Source attack trial 2026; five fresh paired explanation seeds per target. One classifier per dataset. Target-subset selection was independent of attack outcomes. No attack optimization was repeated. Technical validation checks native-mask, saved-mask, probability and physical-fidelity parity. All results remain conditional on these frozen graphs and classifiers.', '',
           '| Dataset | Method | Targets | Selection-seed similarity | Fresh-seed similarity | Fresh clean-repeat similarity |', '|---|---|---:|---:|---:|---:|']
    for (name,m),g in target.groupby(['dataset','method']):
        old=g[g.stage=='selection_seed'];new=g[g.stage=='fresh']
        lines.append(f"| {name} | {m} | {len(new)} | {old.binary_top25_cosine.mean():.4f} | {new.binary_top25_cosine.mean():.4f} | {new.clean_repeat_binary_top25_cosine.mean():.4f} |")
    lines+=['','Fresh-seed similarity compares clean/attacked graphs using the same unseen seed. Clean-repeat similarity uses independent seeds on the unchanged graph; it is a variability reference, not a perfectly matched null for the paired statistic. Higher fresh-minus-selection similarity indicates reduced disruption under fresh randomness. It does not alone establish attack failure.', '',
            '| Dataset | Method | Clean excess soft necessity (pp) | Attacked excess soft necessity (pp) | Paired change (pp) |', '|---|---|---:|---:|---:|']
    for (name,m),g in target[target.stage=='fresh'].groupby(['dataset','method']):
        lines.append(f"| {name} | {m} | {100*g.clean_excess_soft_plus.mean():.4f} | {100*g.attacked_excess_soft_plus.mean():.4f} | {100*g.delta_excess_soft_plus.mean():.4f} |")
    lines+=['','Excess soft necessity is explainer removal-induced probability drop minus the mean for 20 uniform size-matched edge sets on the same graph. Negative paired change means a smaller advantage over random edges after attack. This controls size, not connectivity or degree, and does not fix distribution-shift concerns of edge-removal fidelity. Signed values are retained. The 20 subsets are Monte Carlo controls, not independent targets.', '',
            'CSV summaries include hard/soft necessity and sufficiency-failure, unconditional and label-preserved results, and 95% target-resampling intervals. Repeated seeds are averaged before resampling; graph-node dependence and model-training uncertainty are not represented. Do not infer statistical superiority from overlapping/unpaired marginal intervals.', '',
            f'Mean saved target runtime: {np.mean(times):.1f} seconds. Existing HI-Small SubgraphX source and output files were not modified.']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    save(OUT/'coverage.json',dict(saved=n,expected=100,complete=complete))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0)
    args=parser.parse_args()
    assert torch.cuda.is_available(),'CUDA is required for this isolated audit'
    torch.cuda.set_per_process_memory_fraction(.25)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'cases').mkdir(exist_ok=True)
    lock=OUT/'controller.lock'
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        manifest=freeze_manifest();manifest_id=digest(manifest)
        for name in CONFIG['datasets']:
            selected=manifest['targets'][name]
            if args.limit:selected=selected[:args.limit]
            bundle=torch.load(STUDY/f'complete_graphs/prepared/{name}.pt',map_location='cpu',weights_only=False)
            data=bundle['data'];model=MarasiGraphSAGE(data.num_features,bundle['hidden']).to('cuda')
            model.load_state_dict(bundle['state']);model.eval()
            for p in model.parameters():p.requires_grad_(False)
            for index,t in enumerate(selected):
                path=OUT/f'cases/{name}_{t}.json'
                if path.exists():
                    existing=json.loads(path.read_text());assert existing['manifest_id']==manifest_id
                    continue
                save(OUT/'status.json',dict(state='running',pid=os.getpid(),dataset=name,target=t,manifest_id=manifest_id,limit=args.limit))
                print('START',name,t,flush=True)
                result=one_case(name,t,data,model,manifest_id,validate=index==0)
                save(path,result)
                print('SAVED',name,t,'seconds',round(result['seconds'],1),'GPU_peak_MB',round(torch.cuda.max_memory_allocated()/1024**2),flush=True)
                if len(list((OUT/'cases').glob('*.json')))%10==0:report(manifest_id)
                torch.cuda.empty_cache()
            del model,data,bundle;torch.cuda.empty_cache()
        report(manifest_id)
        coverage=json.loads((OUT/'coverage.json').read_text())
        save(OUT/'status.json',dict(state='complete' if coverage['complete'] else 'pilot_complete',pid=os.getpid(),manifest_id=manifest_id,**coverage))
    except Exception:
        save(OUT/'status.json',dict(state='failed',pid=os.getpid(),traceback=traceback.format_exc()))
        raise
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':main()
