import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import argparse, ctypes, hashlib, importlib.util, json, sys, time, traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parent; STUDY=ROOT.parent; OUT=ROOT/'results'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
H=module('resolution_audit_helpers',STUDY/'followup_audit/run.py')
Q=module('resolution_measures',STUDY/'exploratory_multigraph_resolution/run.py')
np,pd,torch,save,sha=H.np,H.pd,H.torch,H.save,H.sha
CONFIG=dict(targets_per_dataset=50,subset_seed=237611,source_trial=2026,seeds=list(range(110001,110006)),
            repeats=list(range(111001,111006)),permutation_seed=112001,bootstrap_seed=113001,bootstrap_draws=5000,
            methods=H.METHODS,selections=['top25','top10'],gpu_fraction=.20)
def identity(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def priority():
    if os.name=='nt':
        k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
        k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint];k.SetPriorityClass(k.GetCurrentProcess(),0x4000)
def freeze():
    paths=[Path(__file__),ROOT/'README.md',STUDY/'followup_audit/run.py',STUDY/'exploratory_multigraph_resolution/run.py',
           STUDY/'complete_graphs/prepare.py',STUDY/'complete_graphs/attack_core.py',STUDY/'framework/src/models/marasi_models.py',
           STUDY/'followup_audit/results/gnn_audit/manifest.json']
    inputs={str(p.relative_to(STUDY)):sha(p) for p in paths}; targets={};rng=np.random.default_rng(CONFIG['subset_seed'])
    old=json.loads((STUDY/'followup_audit/results/gnn_audit/manifest.json').read_text())
    for name in ['amlsim','hi_small']:
        p=STUDY/f'complete_graphs/results/full/{name}_targets.json';inputs[str(p.relative_to(STUDY))]=sha(p)
        ids=sorted(set(json.loads(p.read_text())['selected'])-set(old['targets'][name]))
        targets[name]=sorted(int(t) for t in rng.choice(ids,50,replace=False))
        p=STUDY/f'complete_graphs/prepared/{name}.pt';inputs[str(p.relative_to(STUDY))]=sha(p)
        for t in targets[name]:
            p=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json';inputs[str(p.relative_to(STUDY))]=sha(p)
    d=dict(config=CONFIG,inputs=inputs,targets=targets,torch=torch.__version__,pyg=__import__('torch_geometric').__version__)
    p=OUT/'manifest.json'
    if p.exists():assert json.loads(p.read_text())==d,'Source/config changed; use separate output folder'
    else:save(p,d)
    return d
def one(name,t,data,model,mid,validate):
    start=time.time();source=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json';old=json.loads(source.read_text())
    frozen={k:v.clone() for k,v in model.state_dict().items()};graphs={};checks={};predictions={}
    for method in ['Clean']+H.METHODS:
        edits=[] if method=='Clean' else old['attacks'][method]['edge_ids']
        e,ids=H.physical(data,edits);g=H.local_graph(data,e,ids,t);graphs[method]=g
        saved=old['clean']['GNNExplainer'] if method=='Clean' else old['attacks'][method]['scores']
        original=H.explain(model,g,2026);checks[method]=dict(source_mask_max_error=H.assert_scores(original,saved))
        if validate and method in ['Clean',H.METHODS[0]]:checks[method].update(H.validate_graph(model,data,e,ids,t,g,original,saved))
        logits,label=H.predict(model,g);predictions[method]=dict(logits=logits.cpu().tolist(),label=label)
        if method=='Clean':clean_label=label;clean_prob=float(logits.softmax(-1)[label])
        else:
            assert (label==clean_label)==old['attacks'][method]['preserved']
            assert abs(float(logits.softmax(-1)[clean_label])-old['attacks'][method]['probability'])<3e-4
        del e,ids
    edges=data.edge_index.numpy()
    def endpoint(key):return tuple(int(v) for v in edges[:,int(key[1:])]) if key.startswith('E') else tuple(map(int,key[1:].split(':')))
    rows=[];evidence={};g=graphs['Clean']
    for i,s in enumerate(CONFIG['seeds']):
        scores={m:H.explain(model,v,s) for m,v in graphs.items()};repeat=H.explain(model,g,CONFIG['repeats'][i])
        rng=np.random.default_rng(CONFIG['permutation_seed']+t*17+i)
        order=rng.permutation(len(g['ids']));permuted=dict(g,edge=g['edge'][:,torch.tensor(order,device='cuda')],ids=[g['ids'][j] for j in order])
        po,_=H.predict(model,permuted);co,_=H.predict(model,g);torch.testing.assert_close(po,co,atol=3e-5,rtol=3e-5)
        perm=H.explain(model,permuted,s);fids={m:H.fid_scores(model,v,scores[m]) for m,v in graphs.items()}
        fids.update({'Clean repeat':H.fid_scores(model,g,repeat),'Clean permutation':H.fid_scores(model,g,perm)})
        evidence[str(s)]=dict(scores=scores,repeat_seed=CONFIG['repeats'][i],clean_repeat=repeat,clean_permuted=perm,
                               permutation=order.tolist(),permutation_logit_max_error=float((po-co).abs().max()),fidelity=fids)
        for method,b in list(scores.items())[1:]+[('Clean repeat',repeat),('Clean permutation',perm)]:
            for selection in CONFIG['selections']:
                rows.append(dict(dataset=name,target=t,seed=s,method=method,selection=selection,
                                 **Q.measure(scores['Clean'],b,selection,endpoint)))
        print(name,t,'fresh seed',s,flush=True)
    for k,v in frozen.items():torch.testing.assert_close(model.state_dict()[k],v,atol=0,rtol=0)
    return dict(dataset=name,target=t,manifest_id=mid,seconds=time.time()-start,source_sha256=sha(source),
                predictions=predictions,checks=checks,rows=rows,explanations=evidence,
                graph_details={m:dict(ids=v['ids'],global_nodes=v['global_nodes']) for m,v in graphs.items()})
def report(d):
    cases=[json.loads(p.read_text()) for p in (OUT/'cases').glob('*.json')];mid=identity(d)
    assert all(c['manifest_id']==mid for c in cases)
    rows=[r for c in cases for r in c['rows']];cov=dict(saved=len(cases),expected=100,complete=len(cases)==100)
    save(OUT/'coverage.json',cov)
    if not rows:return cov
    df=pd.DataFrame(rows);df.to_csv(OUT/'per_seed.csv',index=False)
    target=df.groupby(['dataset','target','method','selection'])[['row_similarity','matched_similarity','gap']].mean().reset_index()
    target.to_csv(OUT/'per_target.csv',index=False);target.groupby(['dataset','method','selection'])[['row_similarity','matched_similarity','gap']].mean().to_csv(OUT/'summary.csv')
    paired=[];rng=np.random.default_rng(CONFIG['bootstrap_seed'])
    for (name,selection),g in target.groupby(['dataset','selection']):
        repeat=g[g.method.eq('Clean repeat')].set_index('target')
        for method in H.METHODS:
            a=g[g.method.eq(method)].set_index('target').sort_index();b=repeat.loc[a.index]
            raw=(b.row_similarity-a.row_similarity).to_numpy();matched=(b.matched_similarity-a.matched_similarity).to_numpy()
            delta=matched-raw;boot=delta[rng.integers(0,len(delta),(5000,len(delta)))].mean(1)
            paired.append(dict(dataset=name,selection=selection,method=method,targets=len(a),row_excess=float(raw.mean()),
                               matched_excess=float(matched.mean()),contrast_change=float(delta.mean()),
                               lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975))))
    pd.DataFrame(paired).to_csv(OUT/'paired_effects.csv',index=False)
    lines=['# Additional fresh-randomness resolution audit','',f'**{"COMPLETE" if cov["complete"] else "PROVISIONAL"}: {len(cases)}/100 targets.**','',
           'Targets exclude the original fresh-seed cohort but were part of the retrospective aggregate audit. '
           'All fresh and permutation explanations are newly evaluated. Clean repeats are a variability reference, '
           'not a perfectly matched null. Matching is a conditional diagnostic, not corrected accuracy.', '',
           '| Dataset | Method | Selection | Targets | Row excess disruption | Matched excess | Change, 95% target interval |',
           '|---|---|---|---:|---:|---:|---|']
    for r in paired:lines.append(f'| {r["dataset"]} | {r["method"]} | {r["selection"]} | {r["targets"]} | {r["row_excess"]:.4f} | {r["matched_excess"]:.4f} | {r["contrast_change"]:.4f} ({r["lo"]:.4f}, {r["hi"]:.4f}) |')
    lines+=['','Primary endpoint is GNN-targeted top-25% contrast change; all other endpoints are secondary. '
            'Seeds are averaged within targets. Intervals omit graph-node dependence and training variation. '
            'Permutation outputs, original masks, top-10 fidelity and checks are in individual case files.']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8');return cov
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['pilot','pipeline']);a=p.parse_args()
    priority();assert torch.cuda.is_available();torch.cuda.set_per_process_memory_fraction(CONFIG['gpu_fraction'])
    (OUT/'cases').mkdir(parents=True,exist_ok=True);lock=OUT/'controller.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        d=freeze();mid=identity(d)
        if a.mode=='pipeline':assert json.loads((OUT/'validation.json').read_text())==dict(passed=True,manifest_id=mid)
        for name,targets in d['targets'].items():
            b=torch.load(STUDY/f'complete_graphs/prepared/{name}.pt',map_location='cpu',weights_only=False);data=b['data']
            model=H.MarasiGraphSAGE(data.num_features,b['hidden']).to('cuda');model.load_state_dict(b['state']);model.eval()
            for par in model.parameters():par.requires_grad_(False)
            for i,t in enumerate(targets[:1] if a.mode=='pilot' else targets):
                path=OUT/f'cases/{name}_{t}.json'
                if path.exists():assert json.loads(path.read_text())['manifest_id']==mid;continue
                save(OUT/'status.json',dict(state='running',pid=os.getpid(),dataset=name,target=t,manifest_id=mid))
                print('START',name,t,flush=True);r=one(name,t,data,model,mid,validate=i==0);save(path,r);report(d)
                print('SAVED',name,t,'seconds',round(r['seconds'],1),flush=True);torch.cuda.empty_cache()
            del model,data,b;torch.cuda.empty_cache()
        cov=report(d)
        if a.mode=='pilot':save(OUT/'validation.json',dict(passed=True,manifest_id=mid))
        save(OUT/'status.json',dict(state='complete' if cov['complete'] else 'pilot_complete',manifest_id=mid,**cov))
    except Exception:save(OUT/'status.json',dict(state='failed',traceback=traceback.format_exc()));raise
    finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
