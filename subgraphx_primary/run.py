"""AMLSim-only discrete SubgraphX attack; pilot gate then three full trials."""
import argparse, json, random, sys, time
from pathlib import Path
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'complete_graphs'
sys.path.insert(0,str(OLD))
from prepare import load, save, sha
from attack_core import CachedSAGE, Context, make_pg, gnn_explain, compare, binary_top25, fidelity
from run_study import Worker

PRIMARY='SubgraphX-targeted search'
METHODS=[PRIMARY,'Random flipping','Random rewiring','Random search']
PARAMS=dict(dataset='amlsim',budget=6,queries=40,full_trials=3,pilot_trials=2,
            algorithm='label-preserving incumbent mutation; independent restart every tenth proposal',
            selection='preserved label first, then maximum native-set cosine distance',
            subgraphx=dict(num_hops=2,num_child=6,num_rollouts=5,node_min=3,shapley_steps=5))

def sources():
    files=list(ROOT.glob('*.py'))+[OLD/n for n in ['prepare.py','attack_core.py','run_study.py','subgraph_worker.py']]
    return {str(p.relative_to(ROOT.parent)):sha(p) for p in files}

def propose(rng,total,incumbent,index):
    if incumbent is None or index%10==0:
        return sorted(rng.sample(range(total),6))
    keep=list(incumbent)
    removed=keep.pop(rng.randrange(6))
    # Replacement must be different, and retain exactly six distinct edits.
    available=[i for i in range(total) if i not in incumbent]
    if not available:return sorted(keep+[removed])
    return sorted(keep+[rng.choice(available)])

def case(cache,bundle,target,trial,worker,pg,folder):
    started=time.time();ctx=Context(cache,target)
    frozen={k:v.clone() for k,v in cache.model.state_dict().items()}
    label=int(cache.logits[target].argmax());prob=float(cache.logits[target].softmax(-1)[label])
    edges,ids=ctx.physical([])
    clean_sub,clean_nodes=worker.explain(ctx,edges,ids,trial,bundle['hidden'],cache.logits[target])
    repeat,repeat_nodes=worker.explain(ctx,edges,ids,trial+10000,bundle['hidden'],cache.logits[target])
    # Same-seed reproducibility check separates seeded stochasticity from implementation errors.
    again,again_nodes=worker.explain(ctx,edges,ids,trial,bundle['hidden'],cache.logits[target])
    assert clean_sub==again and clean_nodes==again_nodes
    clean={ 'SubgraphX':clean_sub, 'GNNExplainer':gnn_explain(ctx,edges,ids,trial) }
    _,clean['PGExplainer'],_,_=ctx.native_pg([],pg)
    memo={};trace=[]
    def evaluate(edits):
        key=tuple(sorted(edits))
        assert len(key)==len(set(key))==6 and all(0<=i<len(ctx.base) for i in key)
        if key in memo:return memo[key]
        edited,eids=ctx.physical(list(key))
        with torch.no_grad():logit=ctx.forward(ctx.weights(list(key)))[target]
        scores,nodes=worker.explain(ctx,edited,eids,trial,bundle['hidden'],logit)
        result=dict(edits=list(key),edge_ids=[ctx.ids[i] for i in key],scores=scores,nodes=nodes,
                    preserved=int(logit.argmax())==label,probability=float(logit.softmax(-1)[label]),
                    distance=1-binary_top25(clean_sub,scores,True)['binary_top25_cosine'])
        memo[key]=result
        return result
    def rank(r):return (r['preserved'],r['distance'])
    rng=random.Random(trial*100000+target+71)
    incumbent=None
    for i in range(PARAMS['queries']):
        proposed=propose(rng,len(ctx.base),None if incumbent is None else incumbent['edits'],i)
        result=evaluate(proposed)
        if incumbent is None or rank(result)>rank(incumbent):incumbent=result
        trace.append(dict(proposal=i,edits=proposed,preserved=result['preserved'],distance=result['distance'],incumbent_distance=incumbent['distance']))
        if (i+1)%10==0:print('amlsim',target,trial,'search proposals',i+1,flush=True)
    rng=random.Random(trial*100000+target+51)
    draws=[rng.sample(range(len(ctx.base)),6) for _ in range(PARAMS['queries'])]
    random_results=[evaluate(x) for x in draws]
    chosen={PRIMARY:incumbent,'Random flipping':random_results[0],
            'Random search':max(random_results,key=rank),
            'Random rewiring':evaluate(rng.sample(range(ctx.m),3)+rng.sample(range(ctx.m,len(ctx.base)),3))}
    rows=[];clean_fid={}
    clean_edges,clean_ids=ctx.physical([])
    for method,result in chosen.items():
        edited,eids=ctx.physical(result['edits'])
        with torch.no_grad():
            full=cache.model(cache.x,edited)[target]
            fast=ctx.forward(ctx.weights(result['edits']))[target]
            torch.testing.assert_close(full,fast,atol=3e-4,rtol=3e-4)
        scores={'SubgraphX':result['scores']}
        if method==PRIMARY:
            scores['GNNExplainer']=gnn_explain(ctx,edited,eids,trial)
            _,scores['PGExplainer'],_,_=ctx.native_pg(result['edits'],pg)
        result['all_scores']=scores
        for ex,ranking in scores.items():
            selections=[('native',len(ranking))] if ex=='SubgraphX' else [('top5',5),('top10',10),('top20',20)]
            for selection,k in selections:
                ck=len(clean[ex]) if ex=='SubgraphX' else k
                if (ex,ck) not in clean_fid:clean_fid[ex,ck]=fidelity(ctx,clean_edges,clean_ids,clean[ex],ck)
                cf=clean_fid[ex,ck];af=fidelity(ctx,edited,eids,ranking,k)
                r=dict(dataset='amlsim',target=target,trial=trial,method=method,explainer=ex,selection=selection,
                       delta_label=int(not result['preserved']),delta_prob=abs(prob-result['probability']),
                       **compare(clean[ex],ranking,max(ck,k) if ex=='SubgraphX' else k),
                       **binary_top25(clean[ex],ranking,ex=='SubgraphX'))
                for prefix,v in [('clean',cf),('attacked',af)]:
                    for new,old in [('hard_plus','necessity'),('hard_minus','sufficiency_failure'),('soft_plus','removed_probability_drop'),('soft_minus','kept_probability_gap')]:r[prefix+'_'+new]=v[old]
                rows.append(r)
    rows.append(dict(dataset='amlsim',target=target,trial=trial,method='Clean repeat',explainer='SubgraphX',selection='native',
                     delta_label=0,delta_prob=0,**compare(clean_sub,repeat,max(len(clean_sub),len(repeat))),**binary_top25(clean_sub,repeat,True)))
    for k,v in frozen.items():torch.testing.assert_close(v,cache.model.state_dict()[k],atol=0,rtol=0)
    return dict(dataset='amlsim',target=target,trial=trial,params=PARAMS,sources=sources(),seconds=time.time()-started,
                clean=clean,clean_nodes=clean_nodes,clean_repeat=repeat,repeat_nodes=repeat_nodes,attacks=chosen,rows=rows,
                trace=trace,unique_candidate_evaluations=len(memo),checks=dict(model_unchanged=True,full_predictor_equivalence=True,same_seed_subgraphx_repeat=True))

def report(folder,expected):
    records=[json.loads(p.read_text()) for p in (folder/'cases').glob('*.json')]
    if not records:return
    d=pd.DataFrame([r for c in records for r in c['rows']]);d.to_csv(folder/'per_target.csv',index=False)
    metrics=['binary_top25_cosine','jaccard','delta_label','delta_prob']+[p+'_'+m for p in ['clean','attacked'] for m in ['hard_plus','hard_minus','soft_plus','soft_minus']]
    t=d.groupby(['method','explainer','selection','trial'])[metrics].mean().reset_index()
    t.to_csv(folder/'trial_means.csv',index=False)
    t.groupby(['method','explainer','selection'])[metrics].agg(['mean','std']).to_csv(folder/'summary.csv')
    done={(c['target'],c['trial']) for c in records};assert done<=expected
    complete=done==expected
    lines=['# SubgraphX-primary AMLSim results','',f'{len(done)} / {len(expected)} evaluations saved. '+('COMPLETE.' if complete else 'IN PROGRESS; final tables withheld.'),'',
           'Direct discrete SubgraphX-targeted search, not original GXAttack or its gradient objective. Six edits; 40 adaptive proposals versus 40 independent random candidates. Native SubgraphX sets, not top-10 or top-25% truncations. Fixed features and model.']
    if complete:
        def vals(method,metric,ex='SubgraphX'):
            return t[(t.method==method)&(t.explainer==ex)&(t.selection==('native' if ex=='SubgraphX' else 'top10'))][metric]
        def fmt(v):return f'{v.mean():.4f} ± {v.std(ddof=1):.4f}'
        lines+=['','## Table II — Attack results','','| Method | Similarity ↓ | Edge edits | ΔLabel ↓ | ΔProb ↓ |','|---|---:|---:|---:|---:|']
        for m in METHODS:lines.append('| '+m+' | '+fmt(vals(m,'binary_top25_cosine'))+' | 6 | '+fmt(vals(m,'delta_label'))+' | '+fmt(vals(m,'delta_prob'))+' |')
        lines+=['','## Table III — Harmonic fidelity before → after','','| Explainer | Clean | Attacked |','|---|---:|---:|']
        for ex in ['SubgraphX','GNNExplainer','PGExplainer']:
            cells=[]
            for pre in ['clean','attacked']:
                a=vals(PRIMARY,pre+'_hard_plus',ex);b=1-vals(PRIMARY,pre+'_hard_minus',ex);cells.append(fmt((2*a*b/(a+b)).fillna(0)))
            lines.append('| '+ex+' | '+' | '.join(cells)+' |')
        lines+=['','Our harmonic summary combines Fidelity+ with 1 − Fidelity−; it is not ground-truth explanation accuracy. PG/GNN use top-10 edges; SubgraphX uses its native set.','',
                '## Table IV — Native SubgraphX fidelity and overlap','','| Metric | Clean | Targeted search | Random flipping | Random rewiring | Random search |','|---|---:|---:|---:|---:|---:|']
        for metric in ['jaccard','hard_plus','hard_minus','soft_plus','soft_minus']:
            clean='1.0000 (self-reference)' if metric=='jaccard' else fmt(vals(PRIMARY,'clean_'+metric))
            cells=[fmt(vals(m,metric if metric=='jaccard' else 'attacked_'+metric)) for m in METHODS]
            lines.append('| '+metric+' | '+clean+' | '+' | '.join(cells)+' |')
        lines+=['','Clean-repeat native similarity: '+fmt(vals('Clean repeat','binary_top25_cosine'))+'. Clean-repeat native Jaccard: '+fmt(vals('Clean repeat','jaccard'))+'.',
                'Means ± sample SD across trial means. Hard fidelity values are fractions; soft values are signed probability differences, with negative meaning increased confidence. Similarity change alone does not establish poorer fidelity or human deception.']
    tmp=folder/'REPORT.tmp';tmp.write_text('\n'.join(lines)+'\n',encoding='utf8');tmp.replace(folder/'REPORT.md')
    save(folder/'coverage.json',dict(saved=len(done),expected=len(expected),complete=complete))

def run_phase(phase,cache,bundle):
    folder=ROOT/'results'/phase;(folder/'cases').mkdir(parents=True,exist_ok=True)
    selected=json.loads((OLD/f'results/{phase}/amlsim_targets.json').read_text())['selected']
    trials=[2026,2027] if phase=='pilot' else [2026,2027,2028]
    assert len(selected)==(3 if phase=='pilot' else 166)
    expected={(target,trial) for target in selected for trial in trials}
    manifest=dict(params=PARAMS,sources=sources(),phase=phase,targets=selected,trials=trials)
    if (folder/'manifest.json').exists():assert json.loads((folder/'manifest.json').read_text())==manifest
    save(folder/'manifest.json',manifest)
    if phase=='full':
        pilot=json.loads((ROOT/'results/pilot/status.json').read_text())
        assert pilot['state']=='complete' and pilot['sources']==sources() and pilot['params']==PARAMS
    worker=Worker(folder)
    try:
        for trial in trials:
            pg=make_pg(cache.model,'amlsim',trial)
            for target in selected:
                path=folder/'cases'/f'amlsim_{target}_{trial}.json'
                if path.exists():
                    old=json.loads(path.read_text());assert old['params']==PARAMS and old['sources']==sources() and all(old['checks'].values());continue
                save(folder/'status.json',dict(state='running',target=target,trial=trial,params=PARAMS))
                result=case(cache,bundle,target,trial,worker,pg,folder)
                save(path,result);report(folder,expected)
                print(phase,'amlsim',target,trial,'seconds',round(result['seconds'],1),flush=True)
        report(folder,expected)
        save(folder/'status.json',dict(state='complete',sources=sources(),params=PARAMS,evaluations=len(expected)))
    except Exception:
        import traceback
        save(folder/'status.json',dict(state='failed',traceback=traceback.format_exc()));raise
    finally:worker.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['pilot','full','pipeline']);args=parser.parse_args()
    data,model,bundle=load('amlsim');cache=CachedSAGE(data,model)
    for phase in (['pilot','full'] if args.phase=='pipeline' else [args.phase]):run_phase(phase,cache,bundle)
