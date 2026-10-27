"""Separate GNNExplainer-primary pilot/full runner; no Elliptic option."""
import argparse,json,time,random,hashlib
from pathlib import Path
import torch
import pandas as pd
from core import optimize
from prepare import load,save,sha
from attack_core import CachedSAGE,Context,gnn_explain,make_pg,compare,binary_top25,fidelity
from run_study import Worker

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'complete_graphs'

def compatible_sources(old,new):
    if old==new:return True
    # Only an explicitly recorded, independently tested runtime-only migration
    # can reuse previous cases. Never accept arbitrary source mismatches.
    path=ROOT/'results/runtime_compatibility.json'
    if not path.exists():return False
    record=json.loads(path.read_text())
    evidence=ROOT.parent/record['evidence_path']
    return (old==record['old_sources'] and new==record['new_sources']
            and sha(evidence)==record['evidence_sha256']
            and json.loads(evidence.read_text()).get('state')=='passed')

def report(folder):
    rows=[]
    for p in (folder/'cases').glob('*.json'):rows.extend(json.loads(p.read_text())['rows'])
    if not rows:return
    d=pd.DataFrame(rows);d.to_csv(folder/'per_target.csv',index=False)
    keys=['dataset','method','explainer','selection']
    metrics=['cosine','binary_top25_cosine','jaccard','delta_label','delta_prob','clean_hard_plus','attacked_hard_plus','clean_hard_minus','attacked_hard_minus','clean_soft_plus','attacked_soft_plus','clean_soft_minus','attacked_soft_minus']
    trials=d.groupby(keys+['trial'])[metrics].mean().reset_index();trials.to_csv(folder/'trial_means.csv',index=False)
    trials.groupby(keys)[metrics].agg(['mean','std']).to_csv(folder/'summary.csv')
    lines=['# GNNExplainer-primary results','', 'GXAttack-objective adaptation with differentiation through GNNExplainer mask fitting. Direct targeting is distinct from the original paper\'s PGExplainer targeting. Native PyG explanations score every candidate and all reported outcomes.','', f'Current saved target-trial cases: {d[["dataset","target","trial"]].drop_duplicates().shape[0]}. Check status.json for completion. Pilot/smoke data are validation-only, not final test results.','', '| Dataset | Method | Explainer | Binary top25 similarity | Label change fraction | Clean soft+ | Attacked soft+ |','|---|---|---|---:|---:|---:|---:|']
    for (name,method,ex),g in trials[trials.selection.isin(['top10','native'])].groupby(['dataset','method','explainer']):
        vals=[f'{g[c].mean():.5f}' for c in ['binary_top25_cosine','delta_label','clean_soft_plus','attacked_soft_plus']]
        lines.append('| '+name+' | '+method+' | '+ex+' | '+' | '.join(vals)+' |')
    lines+=['','Soft values are signed probability differences, not percentage points. Clean repeat uses a different explanation seed; its fidelity fields are unavailable. Random search uses the same number of native candidate evaluations as the attack, but does not match gradient-computation effort. Features remain fixed.']
    (folder/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')

def run(args):
    folder=ROOT/'results'/args.phase;(folder/'cases').mkdir(parents=True,exist_ok=True)
    validation=json.loads((ROOT/'results/validation.json').read_text());assert validation['state']=='passed'
    params=dict(outer=args.outer,inner=100,draws=args.draws,budget=6,trials=args.trials,targets=args.targets)
    sources={str(p.relative_to(ROOT.parent)):sha(p) for p in list(ROOT.glob('*.py'))+[OLD/'attack_core.py',OLD/'prepare.py',OLD/'run_study.py',OLD/'subgraph_worker.py']}
    if args.phase=='full':
        status=json.loads((ROOT/'results/pilot/status.json').read_text())
        assert status['state']=='complete' and status['params']['outer']==args.outer and status['params']['draws']==args.draws
        assert status['params']['targets']==3 and status['params']['trials']==2
        assert compatible_sources(status['sources'],sources),'Pilot/full sources differ'
    save(folder/'manifest.json',dict(params=params,sources=sources,datasets=['amlsim','hi_small'],phase=args.phase))
    worker=Worker(folder)
    try:
        for name in ['amlsim','hi_small']:
            data,model,bundle=load(name);cache=CachedSAGE(data,model)
            source_phase='full' if args.phase=='full' else 'pilot'
            targets=json.loads((OLD/f'results/{source_phase}/{name}_targets.json').read_text())['selected']
            if args.phase!='full':targets=targets[:args.targets]
            trial_count=5 if args.phase=='full' else args.trials
            for trial in range(2026,2026+trial_count):
                pg=make_pg(model,name,trial)
                for target in targets:
                    dest=folder/'cases'/f'{name}_{target}_{trial}.json'
                    if dest.exists():
                        old=json.loads(dest.read_text());assert compatible_sources(old['sources'],sources) and old['params']==params
                        continue
                    save(folder/'status.json',dict(state='running',dataset=name,target=target,trial=trial,params=params))
                    started=time.time();ctx=Context(cache,target);frozen={k:v.clone() for k,v in model.state_dict().items()}
                    clean_edges,clean_ids=ctx.physical([])
                    clean_gnn=gnn_explain(ctx,clean_edges,clean_ids,trial)
                    _,clean_pg,_,_=ctx.native_pg([],pg)
                    clean_sub,_=worker.explain(ctx,clean_edges,clean_ids,trial,bundle['hidden'],cache.logits[target])
                    clean={'GNNExplainer':clean_gnn,'PGExplainer':clean_pg,'SubgraphX':clean_sub}
                    repeated={'GNNExplainer':gnn_explain(ctx,clean_edges,clean_ids,trial+10000)}
                    optimization_start=time.time()
                    candidates,trace,relaxed=optimize(ctx,trial*100000+target,args.outer,100,args.draws)
                    optimization_seconds=time.time()-optimization_start
                    print(name,target,'optimization seconds',round(optimization_seconds,1),flush=True)
                    # Check full predictor equivalence at clean and edited vertices.
                    for edits in [[],candidates[0]]:
                        p=torch.zeros_like(ctx.base);p[edits]=1
                        edges,ids=ctx.physical(edits)
                        with torch.no_grad():native=model(data.x,edges)[target];approx=relaxed.logits(p)
                        torch.testing.assert_close(native,approx,atol=3e-4,rtol=3e-4)
                    del relaxed
                    label=int(cache.logits[target].argmax());prob=float(cache.logits[target].softmax(-1)[label])
                    def evaluate(edits):
                        assert len(edits)==len(set(edits))==6
                        edges,ids=ctx.physical(edits)
                        scores=gnn_explain(ctx,edges,ids,trial)
                        with torch.no_grad():logit=ctx.forward(ctx.weights(edits))[target]
                        keep=int(logit.argmax())==label
                        return dict(edits=edits,scores=scores,preserved=keep,probability=float(logit.softmax(-1)[label]),distance=1-compare(clean_gnn,scores)['cosine'])
                    def best(draws):
                        values=[evaluate(x) for x in draws]
                        return max(values,key=lambda x:(x['preserved'],x['distance']))
                    rng=random.Random(trial*100000+target+51)
                    random_draws=[rng.sample(range(len(ctx.base)),6) for _ in range(args.draws)]
                    chosen={'GNN-targeted GX adaptation':best(candidates),'Random flipping':evaluate(random_draws[0]),'Random search':best(random_draws),'Random rewiring':evaluate(rng.sample(range(ctx.m),3)+rng.sample(range(ctx.m,len(ctx.base)),3))}
                    rows=[];evidence={}
                    for method,result in chosen.items():
                        edges,ids=ctx.physical(result['edits']);scores={'GNNExplainer':result['scores']}
                        if method=='GNN-targeted GX adaptation':
                            logits,rank,_,_=ctx.native_pg(result['edits'],pg);scores['PGExplainer']=rank
                            scores['SubgraphX'],_=worker.explain(ctx,edges,ids,trial,bundle['hidden'],logits[target])
                        evidence[method]=dict(**result,edge_ids=[ctx.ids[i] for i in result['edits']],all_scores=scores)
                        for ex,ranking in scores.items():
                            selections=[('native',len(ranking))] if ex=='SubgraphX' else [('top5',5),('top10',10),('top20',20),('top25pct',max(1,(len(ranking)+3)//4))]
                            for selection,k in selections:
                                ck=len(clean[ex]) if ex=='SubgraphX' else (max(1,(len(clean[ex])+3)//4) if selection=='top25pct' else k)
                                cf=fidelity(ctx,clean_edges,clean_ids,clean[ex],ck);af=fidelity(ctx,edges,ids,ranking,k)
                                row=dict(dataset=name,target=target,trial=trial,method=method,explainer=ex,selection=selection,delta_label=int(not result['preserved']),delta_prob=abs(prob-result['probability']),**compare(clean[ex],ranking,k),**binary_top25(clean[ex],ranking,ex=='SubgraphX'))
                                if selection in ['top25pct','native']:
                                    ca=set(sorted(clean[ex],key=lambda i:(-clean[ex][i],i))[:ck]);aa=set(sorted(ranking,key=lambda i:(-ranking[i],i))[:k])
                                    row.update(jaccard=len(ca&aa)/len(ca|aa) if ca|aa else 1.,clean_size=len(ca),attacked_size=len(aa),binary_cosine=len(ca&aa)/(len(ca)*len(aa))**.5 if ca and aa else (1. if not ca and not aa else 0.))
                                for prefix,v in [('clean',cf),('attacked',af)]:
                                    for new,old in [('hard_plus','necessity'),('hard_minus','sufficiency_failure'),('soft_plus','removed_probability_drop'),('soft_minus','kept_probability_gap')]:row[prefix+'_'+new]=v[old]
                                rows.append(row)
                    rows.append(dict(dataset=name,target=target,trial=trial,method='Clean repeat',explainer='GNNExplainer',selection='top10',delta_label=0,delta_prob=0,**compare(clean_gnn,repeated['GNNExplainer'],10),**binary_top25(clean_gnn,repeated['GNNExplainer'])))
                    for k,v in frozen.items():torch.testing.assert_close(v,model.state_dict()[k],atol=0,rtol=0)
                    save(dest,dict(dataset=name,target=target,trial=trial,params=params,sources=sources,seconds=time.time()-started,optimization_seconds=optimization_seconds,clean=clean,clean_repeat=repeated,attacks=evidence,trace=trace,rows=rows,checks=dict(full_predictor_equivalence=True,model_unchanged=True)))
                    report(folder)
                    print(name,target,trial,'seconds',round(time.time()-started,1),flush=True)
            del cache,data,model;torch.cuda.empty_cache()
        save(folder/'status.json',dict(state='complete',params=params,sources=sources))
    except Exception:
        import traceback
        save(folder/'status.json',dict(state='failed',params=params,traceback=traceback.format_exc()));raise
    finally:worker.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['smoke','pilot','full']);parser.add_argument('--outer',type=int,default=100);parser.add_argument('--draws',type=int,default=40);parser.add_argument('--targets',type=int,default=3);parser.add_argument('--trials',type=int,default=2)
    run(parser.parse_args())
