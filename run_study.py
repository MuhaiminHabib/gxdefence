"""Pilot-first, resumable experiment orchestration with durable per-case evidence."""
import os,sys,json,time,traceback,subprocess,random
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch_geometric.utils import k_hop_subgraph
from prepare import ROOT,PREP,DEVICE,load,save,sha
from attack_core import CachedSAGE,Context,make_pg,attack,gnn_explain,compare,fidelity

DGL_PY=r'D:\habib dissertation\Projects\AML-GNN-Replication-v2\.venv-subgraphx\Scripts\python.exe'
SOURCE_HASHES={p.name:sha(p) for p in ROOT.glob('*.py')}

class Worker:
    def __init__(self,folder):
        self.folder=folder
        self.log=open(folder/'subgraphx_stderr.log','a',encoding='utf8')
        self.p=subprocess.Popen([DGL_PY,'-u',str(ROOT/'subgraph_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True)
    def explain(self,ctx,edges,ids,s,hidden,expected_logits=None):
        nodes,local,mapping,mask=k_hop_subgraph(ctx.target,2,edges,relabel_nodes=True,num_nodes=ctx.c.n)
        with torch.no_grad():out=ctx.c.model(ctx.c.x,edges)[ctx.target] if expected_logits is None else expected_logits
        path=self.folder/'worker_context.pt'
        torch.save(dict(x=ctx.c.x[nodes].cpu(),edge=local.cpu(),target=int(mapping),hidden=hidden,
            state={k:v.cpu() for k,v in ctx.c.model.state_dict().items()},nodes=nodes.cpu(),ids=[ids[int(i)] for i in mask.nonzero().flatten()],logits=out.cpu(),label=int(out.argmax())),path)
        self.p.stdin.write(json.dumps(dict(path=str(path),seed=s))+'\n');self.p.stdin.flush()
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('DGL worker exited; inspect subgraphx_stderr.log')
        result=json.loads(line)
        if 'error' in result:raise RuntimeError(result['error'])
        return {i:1. for i in result['ids']},result['nodes']
    def close(self):
        self.p.stdin.close();self.p.wait(timeout=30);self.log.close()

def targets(cache,name,phase,folder):
    path=folder/f'{name}_targets.json'
    if path.exists():return json.loads(path.read_text())['selected']
    data=cache.data;illicit=0 if name=='elliptic' else 1
    split=data.val_mask if phase=='pilot' else data.test_mask
    candidates=(split&(data.y==illicit)&(cache.logits.argmax(1)==illicit)).nonzero().flatten().tolist()
    census=[];eligible=[]
    for t in candidates:
        nodes,e,m,mask=k_hop_subgraph(t,2,cache.e,num_nodes=cache.n)
        n=len(nodes);count=e.shape[1];rem=int((e[0]!=e[1]).sum())
        absent=n*(n-1)-len(set((a,b) for a,b in e.T.cpu().tolist() if a!=b))
        ok=4<=n<=100 and 5<=count<=2000 and rem>=3 and absent>=3
        census.append(dict(target=t,nodes=n,edges=count,nonedges=absent,eligible=ok))
        if ok:eligible.append(t)
    selected=random.Random(4242).sample(eligible,min(3 if phase=='pilot' else 50,len(eligible)))
    if not selected:raise RuntimeError(f'No eligible {phase} targets for {name}')
    save(path,dict(split='validation' if phase=='pilot' else 'test',correct_illicit=len(candidates),eligible=len(eligible),selected=selected,census=census))
    return selected

def endpoint_cos(ctx,clean,attacked):
    # Author implementation coalesces parallel transaction scores at endpoints.
    from attack_core import cosine
    def collapse(scores):
        out={}
        for k,v in scores.items():
            pair=tuple(ctx.c.e[:,int(k[1:])].tolist()) if k[0]=='E' else tuple(map(int,k[1:].split(':')))
            out[pair]=out.get(pair,0.)+v
        return out
    a,b=collapse(clean),collapse(attacked);keys=sorted(set(a)|set(b))
    return cosine(torch.tensor([a.get(k,0.) for k in keys]),torch.tensor([b.get(k,0.) for k in keys]))

def case(cache,name,bundle,target,s,folder,worker,phase):
    start=time.time();ctx=Context(cache,target);pg=make_pg(cache.model,name,s)
    checks=ctx.validate(pg)
    before={k:v.clone() for k,v in cache.model.state_dict().items()}
    pg_before={k:v.clone() for k,v in pg.algorithm.state_dict().items()}
    edits,trace=attack(ctx,pg,s*100000+target)
    clean_out,clean_pg,clean_edges,clean_ids=ctx.native_pg([],pg)
    label=int(clean_out[target].argmax());prob=float(clean_out[target].softmax(-1)[label])
    clean_gnn=gnn_explain(ctx,clean_edges,clean_ids,s)
    clean_sub,clean_nodes=worker.explain(ctx,clean_edges,clean_ids,s,bundle['hidden'],clean_out[target])
    clean={'PGExplainer':clean_pg,'GNNExplainer':clean_gnn,'SubgraphX':clean_sub}
    repeat_pg=make_pg(cache.model,name,2026+(s-2026+1)%5)
    _,rpg,_,_=ctx.native_pg([],repeat_pg)
    rgnn=gnn_explain(ctx,clean_edges,clean_ids,s+10000)
    rsub,rnodes=worker.explain(ctx,clean_edges,clean_ids,s+10000,bundle['hidden'],clean_out[target])
    repeated={'PGExplainer':rpg,'GNNExplainer':rgnn,'SubgraphX':rsub}
    rows=[];evidence={};clean_fid={}
    for method,scores in clean.items():
        ks=[len(scores)] if method=='SubgraphX' else [5,10,20]
        for k in ks:
            clean_fid[method,k]=fidelity(ctx,clean_edges,clean_ids,scores,k)
            # Native SubgraphX selections are compared without truncating to clean size.
            control_k=max(len(scores),len(repeated[method])) if method=='SubgraphX' else k
            row=dict(dataset=name,target=target,trial=s,attack='Clean repeat',explainer=method,k=0 if method=='SubgraphX' else k,
                target_lp=1,delta_label=0,delta_prob=0,perturbations=0,**compare(scores,repeated[method],control_k))
            rows.append(row)
    for method,changed in edits.items():
        if len(set(changed))!=6:raise AssertionError('Realized budget mismatch')
        out,pg_scores,edges,ids=ctx.native_pg(changed,pg)
        with torch.no_grad():torch.testing.assert_close(ctx.forward(ctx.weights(changed)),out,atol=3e-4,rtol=3e-4)
        keep=int(out[target].argmax())==label;dp=abs(float(out[target].softmax(-1)[label])-prob)
        scores={'PGExplainer':pg_scores}
        # Transfer is evaluated on GXAttack's one saved graph; baselines also get PG metrics.
        subnodes=[]
        if method=='GXAttack':
            scores['GNNExplainer']=gnn_explain(ctx,edges,ids,s)
            scores['SubgraphX'],subnodes=worker.explain(ctx,edges,ids,s,bundle['hidden'],out[target])
        evidence[method]=dict(edits=[dict(id=ctx.ids[i],source=int(ctx.support[0,i]),destination=int(ctx.support[1,i]),operation='delete' if i<ctx.m else 'add') for i in changed],target_lp=keep,delta_prob=dp,target_probabilities=out[target].softmax(-1).cpu().tolist(),scores=scores,subgraph_nodes=subnodes)
        for explainer,ranking in scores.items():
            ks=[len(ranking)] if explainer=='SubgraphX' else [5,10,20]
            for k in ks:
                old_k=len(clean[explainer]) if explainer=='SubgraphX' else k
                clean_f=clean_fid[explainer,old_k]
                new_f=fidelity(ctx,edges,ids,ranking,k)
                common_k=max(k,old_k) if explainer=='SubgraphX' else k
                row=dict(dataset=name,target=target,trial=s,attack=method,explainer=explainer,k=0 if explainer=='SubgraphX' else k,
                    target_lp=int(keep),delta_label=int(not keep),delta_prob=dp,perturbations=len(changed),additions=sum(i>=ctx.m for i in changed),deletions=sum(i<ctx.m for i in changed),
                    endpoint_cosine=endpoint_cos(ctx,clean[explainer],ranking),**compare(clean[explainer],ranking,common_k))
                row.update({'clean_'+key:value for key,value in clean_f.items()});row.update({'attacked_'+key:value for key,value in new_f.items()});rows.append(row)
    for k,v in before.items():torch.testing.assert_close(v,cache.model.state_dict()[k],atol=0,rtol=0)
    for k,v in pg_before.items():torch.testing.assert_close(v,pg.algorithm.state_dict()[k],atol=0,rtol=0)
    checks['classifier_unchanged']=True
    checks['pg_unchanged']=True
    result=dict(dataset=name,target=target,trial=s,phase=phase,source_hashes=SOURCE_HASHES,seconds=time.time()-start,checks=checks,clean_probability=prob,clean_scores=clean,clean_subgraph_nodes=clean_nodes,repeat_scores=repeated,attacks=evidence,attack_trace=trace,rows=rows)
    save(folder/'cases'/f'{name}_{target}_{s}.json',result)
    print('CASE',phase,name,target,s,'seconds',round(result['seconds'],1),'GX LP',evidence['GXAttack']['target_lp'],flush=True)
    return rows

def summarize(folder):
    rows=[]
    for path in (folder/'cases').glob('*.json'):rows.extend(json.loads(path.read_text())['rows'])
    if not rows:return
    df=pd.DataFrame(rows);df.to_csv(folder/'per_target_metrics.csv',index=False)
    keys=['dataset','attack','explainer','k'];numeric=[c for c in df.select_dtypes(include='number').columns if c not in keys+['target','trial']]
    trials=df.groupby(keys+['trial'],dropna=False)[numeric].mean().reset_index();trials.to_csv(folder/'trial_means.csv',index=False)
    preserved=df[df.target_lp==1];preserved.groupby(keys+['trial'],dropna=False)[numeric].mean().to_csv(folder/'prediction_preserved_trial_means.csv')
    counts=df.groupby(keys,dropna=False).agg(attempted=('target','size'),unique_targets=('target','nunique'),preserved=('target_lp','sum'));counts.to_csv(folder/'counts.csv')
    # Aggregate harmonic fidelity summaries, not a per-target harmonic shortcut.
    for condition in ['clean','attacked']:
        a=condition+'_necessity';b=condition+'_sufficiency_failure'
        if a in trials:
            den=trials[a]+1-trials[b]
            trials[condition+'_harmonic_fidelity']=np.where(den>0,2*trials[a]*(1-trials[b])/den,0)
    trials.to_csv(folder/'trial_means.csv',index=False)
    metrics=[c for c in trials.select_dtypes(include='number').columns if c not in keys+['trial']]
    trials.groupby(keys,dropna=False)[metrics].agg(['mean','std']).to_csv(folder/'summary.csv')

def run(phase,names):
    folder=ROOT/'results'/phase;folder.mkdir(parents=True,exist_ok=True);(folder/'cases').mkdir(exist_ok=True)
    manifest=dict(phase=phase,protocol_sha256=sha(ROOT/'PROTOCOL.md'),source_hashes=SOURCE_HASHES,python=sys.version,torch=torch.__version__,device=DEVICE,datasets=names)
    save(folder/'manifest.json',manifest);save(folder/f'manifest_{time.time_ns()}.json',manifest)
    worker=Worker(folder)
    try:
        for name in names:
            data,model,b=load(name);cache=CachedSAGE(data,model)
            selected=targets(cache,name,phase,folder)
            for s in range(2026,2028 if phase=='pilot' else 2031):
                for target in selected:
                    path=folder/'cases'/f'{name}_{target}_{s}.json'
                    if path.exists():continue
                    save(folder/'status.json',dict(state='running',dataset=name,target=target,trial=s))
                    case(cache,name,b,target,s,folder,worker,phase);summarize(folder)
            del cache,data,model;torch.cuda.empty_cache()
        summarize(folder);save(folder/'status.json',dict(state='complete',datasets=names,technical_gates_passed=True))
    except Exception:
        save(folder/'failure.json',dict(traceback=traceback.format_exc()));save(folder/'status.json',dict(state='failed'));raise
    finally:worker.close()

if __name__=='__main__':
    phase=sys.argv[1] if len(sys.argv)>1 else 'pilot'
    names=sys.argv[2:] or ['elliptic','amlsim','hi_small']
    if phase=='full':
        status=json.loads((ROOT/'results/pilot/status.json').read_text())
        if status.get('state')!='complete' or set(status['datasets'])!=set(names):raise RuntimeError('Full study requires completed pilot on these datasets')
    run(phase,names)
