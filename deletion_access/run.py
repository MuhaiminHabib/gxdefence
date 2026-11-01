"""Isolated paired SubgraphX access-restriction experiment."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
import argparse,ctypes,json,random,sys,time,traceback,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
import torch
from torch_geometric.utils import k_hop_subgraph

ROOT=Path(__file__).resolve().parent;STUDY=ROOT.parent;OLD=STUDY/'complete_graphs'
sys.path.insert(0,str(OLD))
import prepare
import attack_core
# Process-local CPU routing; do not edit the shared experiment modules.
prepare.DEVICE='cpu';attack_core.DEVICE='cpu'
from prepare import load,save,sha
from attack_core import CachedSAGE,Context,compare,binary_top25,fidelity
from run_study import Worker
torch.set_num_threads(1);torch.set_num_interop_threads(1)
if os.name=='nt':
    ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
    ctypes.windll.kernel32.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint]
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)

RESULTS=ROOT/'results'
PARAMS=dict(datasets=['amlsim','hi_small'],targets_per_dataset=30,subset_seed=271828,trial=2026,
            budget=6,proposals=40,conditions=['deletion_only','mixed'],
            methods=['Adaptive search','Random search','Random flipping'],
            subgraphx=dict(num_hops=2,num_child=6,num_rollouts=5,shapley_steps=5,node_min=3),
            predictor_device='cpu',controller_threads=1,worker_threads=2)

def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def sources():
    paths=[Path(__file__),ROOT/'README.md',OLD/'prepare.py',OLD/'attack_core.py',OLD/'run_study.py',OLD/'subgraph_worker.py',STUDY/'framework/src/models/marasi_models.py']
    return {str(p.relative_to(STUDY)):sha(p) for p in paths}

def manifest():
    path=RESULTS/'manifest.json';src=sources()
    if path.exists():
        d=json.loads(path.read_text());assert d['params']==PARAMS and d['sources']==src,'Source or parameters changed'
        for p,h in d['checkpoints'].items():assert sha(STUDY/p)==h,'Checkpoint changed'
        return d
    rng=np.random.default_rng(PARAMS['subset_seed']);targets={};pilot={};census={};checkpoints={};source_cases={};target_files={}
    for name in PARAMS['datasets']:
        print('SCREENING',name,flush=True)
        checkpoint=OLD/f'prepared/{name}.pt';checkpoints[str(checkpoint.relative_to(STUDY))]=sha(checkpoint)
        b=torch.load(checkpoint,map_location='cpu',weights_only=False);data=b['data']
        eligible_path=OLD/f'results/full/{name}_targets.json'
        registered=json.loads(eligible_path.read_text())['selected'];qualified=[];entries=[]
        target_files[str(eligible_path.relative_to(STUDY))]=sha(eligible_path)
        for t in registered:
            p=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json'
            raw=p.read_bytes();old=json.loads(raw)
            edge_ids=sorted(int(v[1:]) for v in old['clean']['GNNExplainer'])
            ix=torch.tensor(edge_ids,dtype=torch.long)
            removable=int((data.edge_index[0,ix]!=data.edge_index[1,ix]).sum())
            ok=removable>=6
            entries.append(dict(target=t,clean_edges=len(ix),removable=removable,eligible=ok))
            source_cases[str(p.relative_to(STUDY))]=hashlib.sha256(raw).hexdigest()
            if ok:qualified.append(t)
        assert len(qualified)>=30
        targets[name]=sorted(int(x) for x in rng.choice(sorted(qualified),30,replace=False))
        vp=OLD/f'results/pilot/{name}_targets.json';target_files[str(vp.relative_to(STUDY))]=sha(vp)
        vals=json.loads(vp.read_text())['selected'];pilot[name]=[]
        for t in vals:
            _,e,_,_=k_hop_subgraph(t,2,data.edge_index,num_nodes=data.num_nodes)
            if int((e[0]!=e[1]).sum())>=6:pilot[name].append(t);break
        assert len(pilot[name])==1 and not set(pilot[name])&set(targets[name])
        census[name]=dict(original_eligible=len(registered),deletion_feasible=len(qualified),excluded=len(registered)-len(qualified),entries=entries)
        print('SCREENED',name,'feasible',len(qualified),'of',len(registered),'pilot',pilot[name],flush=True)
        del b,data
    d=dict(params=PARAMS,sources=src,checkpoints=checkpoints,screening_source_hashes=source_cases,
           target_file_hashes=target_files,targets=targets,pilot=pilot,census=census,torch=torch.__version__)
    save(path,d);return d

def proposal(rng,total,incumbent,i):
    if incumbent is None or i%10==0:return sorted(rng.sample(range(total),6))
    keep=list(incumbent);keep.pop(rng.randrange(6))
    available=[j for j in range(total) if j not in incumbent]
    return sorted(keep+[rng.choice(available)]) if available else sorted(incumbent)

def rank(r):return (r['preserved'],r['distance'])

def case(name,target,cache,bundle,worker,folder,manifest_id,phase):
    start=time.time();trial=2026;ctx=Context(cache,target);assert ctx.m>=6
    state={k:v.clone() for k,v in cache.model.state_dict().items()}
    clean_edges,clean_ids=ctx.physical([]);clean_logit=cache.logits[target];label=int(clean_logit.argmax());prob=float(clean_logit.softmax(-1)[label])
    # Screening was based on saved full edge support, not selected top-k masks.
    if phase=='full':
        original=STUDY/f'gnn_three_trials/results/full/cases/{name}_{target}_2026.json'
        old=json.loads(original.read_text())
        assert set(old['clean']['GNNExplainer'])=={f'E{int(i)}' for i in ctx.clean_ids}
    clean,clean_nodes=worker.explain(ctx,clean_edges,clean_ids,trial,bundle['hidden'],clean_logit)
    same,same_nodes=worker.explain(ctx,clean_edges,clean_ids,trial,bundle['hidden'],clean_logit)
    assert clean==same and clean_nodes==same_nodes
    repeat,_=worker.explain(ctx,clean_edges,clean_ids,trial+10000,bundle['hidden'],clean_logit)
    clean_fid=fidelity(ctx,clean_edges,clean_ids,clean,len(clean))
    del clean_edges,clean_ids
    memo={};traces={};chosen={};timings={};counts={};rows=[]

    def evaluate(edits,condition):
        key=tuple(sorted(edits));assert len(key)==len(set(key))==6
        assert all(0<=i<len(ctx.base) for i in key)
        if condition=='deletion_only':assert all(i<ctx.m for i in key)
        if key in memo:return memo[key]
        edges,ids=ctx.physical(list(key))
        with torch.no_grad():logit=ctx.forward(ctx.weights(list(key)))[target]
        assert torch.isfinite(logit).all()
        scores,nodes=worker.explain(ctx,edges,ids,trial,bundle['hidden'],logit)
        result=dict(edits=list(key),edge_ids=[ctx.ids[i] for i in key],scores=scores,nodes=nodes,
                    preserved=int(logit.argmax())==label,probability=float(logit.softmax(-1)[label]),
                    distance=1-binary_top25(clean,scores,True)['binary_top25_cosine'],
                    deletions=sum(i<ctx.m for i in key),additions=sum(i>=ctx.m for i in key))
        assert 0<=result['distance']<=1+1e-8
        memo[key]=result;return result

    for condition in PARAMS['conditions']:
        limit=ctx.m if condition=='deletion_only' else len(ctx.base)
        before=len(memo);condition_start=time.time();rng=random.Random(trial*100000+target+71)
        incumbent=None;adaptive=[]
        for i in range(40):
            edits=proposal(rng,limit,None if incumbent is None else incumbent['edits'],i)
            result=evaluate(edits,condition)
            if incumbent is None or rank(result)>rank(incumbent):incumbent=result
            adaptive.append(dict(proposal=i+1,edits=edits,preserved=result['preserved'],distance=result['distance'],
                                 incumbent_edits=incumbent['edits'],incumbent_preserved=incumbent['preserved'],incumbent_distance=incumbent['distance']))
            if (i+1)%10==0:print(name,target,condition,'adaptive',i+1,flush=True)
        adaptive_seconds=time.time()-condition_start
        rng=random.Random(trial*100000+target+51);random_results=[];random_trace=[];random_start=time.time()
        for i in range(40):
            result=evaluate(sorted(rng.sample(range(limit),6)),condition);random_results.append(result)
            random_trace.append(dict(proposal=i+1,edits=result['edits'],preserved=result['preserved'],distance=result['distance']))
            if (i+1)%10==0:print(name,target,condition,'random',i+1,flush=True)
        traces[condition]=dict(adaptive=adaptive,random=random_trace)
        chosen[condition]={'Adaptive search':incumbent,'Random search':max(random_results,key=rank),'Random flipping':random_results[0]}
        counts[condition]=dict(domain_size=limit,adaptive_unique=len({tuple(v['edits']) for v in adaptive}),
                               random_unique=len({tuple(v['edits']) for v in random_trace}),new_evaluations=len(memo)-before)
        timings[condition]=dict(adaptive_seconds=adaptive_seconds,random_seconds=time.time()-random_start)
        for method,result in chosen[condition].items():
            edges,ids=ctx.physical(result['edits'])
            with torch.no_grad():
                full=cache.model(cache.x,edges)[target];fast=ctx.forward(ctx.weights(result['edits']))[target]
                torch.testing.assert_close(full,fast,atol=3e-4,rtol=3e-4)
            attacked_fid=fidelity(ctx,edges,ids,result['scores'],len(result['scores']))
            deleted={ctx.ids[i] for i in result['edits'] if i<ctx.m}
            surviving_clean={k:v for k,v in clean.items() if k not in deleted}
            # Restrict to the unchanged original edge universe (no deleted or added rows).
            surviving_attacked={k:v for k,v in result['scores'].items() if k.startswith('E') and k not in deleted}
            overlap=compare(clean,result['scores'],max(len(clean),len(result['scores'])))
            restricted=binary_top25(surviving_clean,surviving_attacked,True)['binary_top25_cosine']
            row=dict(dataset=name,target=target,trial=trial,condition=condition,method=method,
                     similarity=1-result['distance'],jaccard=overlap['jaccard'],delta_label=int(not result['preserved']),
                     delta_prob=abs(prob-result['probability']),deletions=result['deletions'],additions=result['additions'],
                     clean_size=len(clean),attacked_size=len(result['scores']),clean_empty=int(not clean),attacked_empty=int(not result['scores']),
                     clean_context_edges=len(ctx.clean_ids),edit_fraction_clean_context=6/max(1,len(ctx.clean_ids)),
                     surviving_clean_size=len(surviving_clean),original_attacked_size=len(surviving_attacked),
                     clean_explanation_edges_deleted=len(set(clean)&deleted),common_original_edge_similarity=restricted,
                     repeat_similarity=binary_top25(clean,repeat,True)['binary_top25_cosine'],
                     label_preserved_zero_similarity=int(result['preserved'] and result['distance']>=1-1e-12))
            for prefix,values in [('clean',clean_fid),('attacked',attacked_fid)]:
                for new,old in [('hard_plus','necessity'),('hard_minus','sufficiency_failure'),('soft_plus','removed_probability_drop'),('soft_minus','kept_probability_gap')]:row[prefix+'_'+new]=values[old]
            assert all(np.isfinite(v) for v in row.values() if isinstance(v,(int,float)))
            rows.append(row)
    for key,v in state.items():torch.testing.assert_close(v,cache.model.state_dict()[key],atol=0,rtol=0)
    return dict(dataset=name,target=target,trial=trial,manifest_id=manifest_id,seconds=time.time()-start,
                clean=clean,clean_nodes=clean_nodes,clean_repeat=repeat,clean_probability=prob,clean_label=label,
                removable_rows=ctx.m,mixed_domain_size=len(ctx.base),attacks=chosen,trace=traces,
                candidates=list(memo.values()),unique_candidate_evaluations=len(memo),domain_counts=counts,search_times=timings,rows=rows,
                checks=dict(frozen_model=True,same_seed_repeat=True,full_predictor_parity=True,budget_permissions=True,finite_outputs=True))

def report(folder,expected,mid):
    cases=[json.loads(p.read_text()) for p in (folder/'cases').glob('*.json')]
    if not cases:return
    done={(c['dataset'],c['target']) for c in cases}
    assert len(done)==len(cases) and done<=expected
    assert all(c['manifest_id']==mid for c in cases)
    frame=pd.DataFrame([r for c in cases for r in c['rows']]);frame.to_csv(folder/'per_target.csv',index=False)
    metrics=['similarity','jaccard','delta_label','delta_prob','label_preserved_zero_similarity','deletions','additions',
             'clean_size','attacked_size','clean_empty','attacked_empty','common_original_edge_similarity','clean_explanation_edges_deleted',
             'clean_hard_plus','clean_hard_minus','clean_soft_plus','clean_soft_minus','attacked_hard_plus','attacked_hard_minus','attacked_soft_plus','attacked_soft_minus']
    rng=np.random.default_rng(613);summary=[];paired=[]
    for (name,condition,method),g in frame.groupby(['dataset','condition','method']):
        a=g[metrics].to_numpy();boot=a[rng.integers(0,len(a),(3000,len(a)))].mean(axis=1)
        for i,m in enumerate(metrics):summary.append(dict(dataset=name,condition=condition,method=method,targets=len(a),metric=m,mean=float(a[:,i].mean()),lo=float(np.quantile(boot[:,i],.025)),hi=float(np.quantile(boot[:,i],.975))))
    for (name,method),g in frame.groupby(['dataset','method']):
        a=g[g.condition=='deletion_only'].set_index('target').sort_index();b=g[g.condition=='mixed'].set_index('target').sort_index()
        assert a.index.equals(b.index)
        for population,mask in [('all',np.ones(len(a),dtype=bool)),('both_preserved',((a.delta_label==0)&(b.delta_label==0)).to_numpy())]:
            for m in ['similarity','delta_label','delta_prob','attacked_soft_plus','attacked_hard_plus']:
                values=(a[m]-b[m]).to_numpy()[mask]
                if not len(values):continue
                boot=values[rng.integers(0,len(values),(3000,len(values)))].mean(axis=1)
                paired.append(dict(dataset=name,method=method,population=population,targets=len(values),metric=m,deletion_minus_mixed=float(values.mean()),lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975))))
    pd.DataFrame(summary).to_csv(folder/'summary.csv',index=False);pd.DataFrame(paired).to_csv(folder/'paired_effects.csv',index=False)
    complete=done==expected
    lines=['# SubgraphX: deletion-only versus mixed edit access','',f'**{"COMPLETE" if complete else "PROVISIONAL"}: {len(done)}/{len(expected)} paired target cases.**','',
           'Six edits, 40 proposals per search method and access condition, one trial (2026). Same targets and frozen classifiers/features in both conditions. Predictions that change are retained. No between-trial SD is available.', '',
           '| Dataset | Access | Method | Targets | Similarity | Label change | Probability change |', '|---|---|---|---:|---:|---:|---:|']
    for (name,c,m),g in frame.groupby(['dataset','condition','method']):
        lines.append(f'| {name} | {c} | {m} | {len(g)} | {g.similarity.mean():.4f} | {g.delta_label.mean():.4f} | {g.delta_prob.mean():.5f} |')
    lines+=['','| Dataset | Method | Deletion-minus-mixed similarity | 95% target-resampling interval |','|---|---|---:|---:|']
    for r in paired:
        if r['population']=='all' and r['metric']=='similarity':lines.append(f"| {r['dataset']} | {r['method']} | {r['deletion_minus_mixed']:.4f} | ({r['lo']:.4f}, {r['hi']:.4f}) |")
    lines+=['','Positive paired similarity differences mean less disruption with deletion-only access. Intervals are conditional target resampling; they do not account for dependence between connected nodes or classifier-training variation. All-target tables are primary; paired both-preserved analyses are separately saved. Empty explanations and direct deletion of explanatory edges are reported in CSVs. Restricted common-original-edge overlap is supplementary, not a replacement for native-set overlap.', '',
            'The experiment uses graph-store corruption with frozen transaction-derived features. It does not establish economic feasibility, human deception, explanation accuracy, a defense, or a black-box attack. Both search conditions are newly executed. Proposals and unique explainer evaluations differ because duplicate candidates are cached.', '',
            f'Mean completed paired-case runtime: {np.mean([c["seconds"] for c in cases]):.1f} seconds.']
    (folder/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    save(folder/'coverage.json',dict(saved=len(done),expected=len(expected),complete=complete))

def run_phase(phase,d):
    mid=identity(d);selection=d['pilot'] if phase=='pilot' else d['targets'];expected={(n,t) for n,ids in selection.items() for t in ids}
    folder=RESULTS/phase;(folder/'cases').mkdir(parents=True,exist_ok=True)
    if phase=='full':
        pilot=json.loads((RESULTS/'pilot/status.json').read_text())
        assert pilot['state']=='complete' and pilot['manifest_id']==mid
    worker=Worker(folder)
    try:
        for name in PARAMS['datasets']:
            data,model,bundle=load(name);cache=CachedSAGE(data,model)
            for target in selection[name]:
                dest=folder/f'cases/{name}_{target}_2026.json'
                if dest.exists():
                    old=json.loads(dest.read_text());assert old['manifest_id']==mid and all(old['checks'].values());continue
                save(folder/'status.json',dict(state='running',phase=phase,pid=os.getpid(),dataset=name,target=target,manifest_id=mid))
                print('START',phase,name,target,flush=True)
                result=case(name,target,cache,bundle,worker,folder,mid,phase);save(dest,result);report(folder,expected,mid)
                print('SAVED',phase,name,target,'seconds',round(result['seconds'],1),flush=True)
            del cache,data,model,bundle
        report(folder,expected,mid)
        save(folder/'status.json',dict(state='complete',phase=phase,manifest_id=mid,evaluations=len(expected)))
    except Exception:
        save(folder/'status.json',dict(state='failed',phase=phase,traceback=traceback.format_exc()));raise
    finally:worker.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','pilot','full','pipeline']);args=p.parse_args()
    RESULTS.mkdir(parents=True,exist_ok=True);lock=RESULTS/'controller.lock'
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        d=manifest()
        if args.phase=='prepare':return
        for phase in (['pilot','full'] if args.phase=='pipeline' else [args.phase]):run_phase(phase,d)
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
