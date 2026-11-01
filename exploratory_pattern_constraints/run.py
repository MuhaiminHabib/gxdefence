import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import argparse,copy,ctypes,hashlib,importlib.util,json,math,random,sys,time,traceback
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;STUDY=ROOT.parent;OUT=ROOT/'results'
spec=importlib.util.spec_from_file_location('pattern_helpers',STUDY/'followup_audit/run.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
from structure import Structure,self_test
np,pd,torch,save,sha=H.np,H.pd,H.torch,H.save,H.sha
CONDITIONS=['source_fixed','degree','degree_cycles'];SELECTORS=['Best of 40','First random candidate']
CONFIG=dict(datasets=['amlsim','hi_small'],screening_targets=10,expanded_targets=50,subset_seed=358113,
            max_proposals=40,max_structural_draws=20000,record_rewirings=3,edge_edits=6,probability_cap=.02,
            selection_seeds=[120001,120002,120003],fresh_seeds=[list(range(121001,121006)),list(range(123001,123006)),list(range(124001,124006))],
            repeat_seeds=[list(range(122001,122006)),list(range(125001,125006)),list(range(126001,126006))],
            bootstrap_draws=5000,bootstrap_seed=127001,gpu_fraction=.20,
            promotion_min_coverage=.8,promotion_min_excess=.10,promotion_min_joint_disruption=.30)
def identity(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def priority():
    if os.name=='nt':
        k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
        k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint];k.SetPriorityClass(k.GetCurrentProcess(),0x4000)
def freeze():
    files=[Path(__file__),ROOT/'README.md',ROOT/'structure.py',STUDY/'followup_audit/run.py',
           STUDY/'complete_graphs/prepare.py',STUDY/'complete_graphs/attack_core.py',STUDY/'framework/src/models/marasi_models.py']
    sources={str(p.relative_to(STUDY)):sha(p) for p in files};inputs={};screen={};expanded={};census={}
    rng=np.random.default_rng(CONFIG['subset_seed'])
    for name in CONFIG['datasets']:
        p=STUDY/f'complete_graphs/prepared/{name}.pt';inputs[str(p.relative_to(STUDY))]=sha(p)
        p=STUDY/f'complete_graphs/results/full/{name}_targets.json';inputs[str(p.relative_to(STUDY))]=sha(p)
        targets=sorted(json.loads(p.read_text())['selected']);eligible=[];excluded=[]
        for t in targets:
            p=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json';inputs[str(p.relative_to(STUDY))]=sha(p)
            old=json.loads(p.read_text());(eligible if len(old['clean']['GNNExplainer'])>=10 else excluded).append(t)
        chosen=[int(t) for t in rng.choice(eligible,60,replace=False)];screen[name]=sorted(chosen[:10]);expanded[name]=sorted(chosen[10:])
        census[name]=dict(eligible=len(eligible),excluded_small_clean_pools=excluded)
    d=dict(config=CONFIG,sources=sources,inputs=inputs,screening=screen,expanded=expanded,census=census,
           torch=torch.__version__,pyg=__import__('torch_geometric').__version__)
    p=OUT/'manifest.json'
    if p.exists():assert json.loads(p.read_text())==d,'Sources or configuration changed'
    else:save(p,d)
    return d
class RewiredIds:
    def __init__(self,edge,rewires):self.edge=edge;self.changed=dict(rewires)
    def __getitem__(self,i):
        return f'R{i}:{int(self.edge[0,i])}:{self.changed[i]}' if i in self.changed else f'E{i}'
def graph(data,target,rewires):
    e=data.edge_index.clone() if rewires else data.edge_index
    for row,v in rewires:e[1,row]=v
    ids=RewiredIds(data.edge_index,rewires)
    return H.local_graph(data,e,ids,target),e,ids
def endpoints(key,edge):
    if key.startswith('E'):return tuple(int(v) for v in edge[:,int(key[1:])])
    _,u,v=key.split(':');return int(u),int(v)
def overlap(a,b,edge):
    aa=set(sorted(a,key=lambda k:(-a[k],k))[:math.ceil(len(a)/4)])
    bb=set(sorted(b,key=lambda k:(-b[k],k))[:math.ceil(len(b)/4)])
    if not aa or not bb:return dict(row_overlap=float(not aa and not bb),pair_overlap=float(not aa and not bb))
    den=math.sqrt(len(aa)*len(bb));ca=Counter(endpoints(k,edge) for k in aa);cb=Counter(endpoints(k,edge) for k in bb)
    raw=len(aa&bb)/den;pair=sum(min(v,cb[k]) for k,v in ca.items())/den
    assert raw-1e-10<=pair<=1+1e-10
    return dict(row_overlap=raw,pair_overlap=pair)
def pool(condition,name,t,trial,clean,structure):
    domain=[int(k[1:]) for k in clean['ids'] if structure.edge[0,int(k[1:])]!=structure.edge[1,int(k[1:])]]
    nodes=clean['global_nodes'];seed_key=[name,t,trial,'unrestricted' if condition=='source_fixed' else 'degree']
    rng=random.Random(int(identity(seed_key)[:16],16));seen=set();candidates=[];rejects=Counter();draws=0
    if len(domain)<3:return [],dict(draws=0,accepted=0,rejections={'domain_too_small':1},budget_shortfall=40)
    for draws in range(1,CONFIG['max_structural_draws']+1):
        rows=rng.sample(domain,3);src=[int(structure.edge[0,r]) for r in rows];dst=[int(structure.edge[1,r]) for r in rows]
        if len(set(src))<3 or len(set(dst))<3:rejects['non_distinct_sources_or_receivers']+=1;continue
        if condition=='source_fixed':new=[rng.choice(nodes) for _ in rows]
        else:
            shift=rng.choice([1,2]);new=dst[shift:]+dst[:shift]
        if any(u==v for u,v in zip(src,new)):rejects['self_loop']+=1;continue
        if set(zip(src,dst))&set(zip(src,new)):rejects['unchanged_or_cancelled_pair']+=1;continue
        rewires=tuple(sorted(zip(rows,new)))
        if rewires in seen:rejects['duplicate']+=1;continue
        seen.add(rewires);delta=structure.delta(rewires)
        assert delta['outdegree_l1']==0
        if condition!='source_fixed':assert delta['indegree_l1']==0
        if condition=='degree_cycles' and (delta['cycles2_delta'] or delta['cycles3_delta']):rejects['changed_cycles']+=1;continue
        candidates.append(dict(rewires=[list(x) for x in rewires],structure=delta,structural_draw=draws))
        if len(candidates)==CONFIG['max_proposals']:break
    return candidates,dict(draws=draws,accepted=len(candidates),rejections=dict(rejects),budget_shortfall=40-len(candidates))
def native_check(model,data,t,g,e,ids):
    cpu=copy.deepcopy(model).cpu().eval()
    with torch.no_grad():ref=cpu(data.x,e)[t]
    torch.testing.assert_close(H.predict(model,g)[0].cpu(),ref,atol=3e-4,rtol=3e-4);del cpu
    scores=H.explain(model,g,2026)
    return dict(full_local_prediction=True,**H.validate_graph(model,data,e,ids,t,g,scores,scores))
def one(name,t,trial,phase,data,model,structure,mid,validate):
    start=time.time();frozen={k:v.clone() for k,v in model.state_dict().items()};clean,e,ids=graph(data,t,[])
    source=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json';old=json.loads(source.read_text())
    original=H.explain(model,clean,2026);checks=dict(source_mask_max_error=H.assert_scores(original,old['clean']['GNNExplainer']))
    if validate:checks['native_clean']=native_check(model,data,t,clean,e,ids)
    co,label=H.predict(model,clean);cp=float(co.softmax(-1)[label]);s=CONFIG['selection_seeds'][trial]
    clean_scores=H.explain(model,clean,s);candidate_sets={};generation={};selected={};memo={};explain_calls=0;prediction_calls=0
    for condition in CONDITIONS:
        candidates,generation[condition]=pool(condition,name,t,trial,clean,structure)
        for i,r in enumerate(candidates):
            key=tuple(map(tuple,r['rewires']))
            if key not in memo:
                g,edited,edgeids=graph(data,t,r['rewires']);lo,lab=H.predict(model,g);prediction_calls+=1
                prob=float(lo.softmax(-1)[label]);feasible=lab==label and abs(prob-cp)<=CONFIG['probability_cap'] and len(g['ids'])>=10
                result=dict(preserved=lab==label,probability=prob,probability_change=abs(prob-cp),feasible=feasible,edge_count=len(g['ids']))
                if validate and 'native_edited' not in checks:checks['native_edited']=native_check(model,data,t,g,edited,edgeids)
                if feasible:
                    scores=H.explain(model,g,s);explain_calls+=1;result.update(scores=scores,**overlap(clean_scores,scores,structure.edge))
                memo[key]=result
                del g,edited,edgeids
            r.update(memo[key]);r['proposal']=i+1
            if (i+1)%10==0:print(name,t,trial,condition,'candidate',i+1,flush=True)
        feasible=[r for r in candidates if r['feasible']]
        selected[condition+'|Best of 40']=min(feasible,key=lambda r:(r['pair_overlap'],r['proposal'])) if feasible else None
        selected[condition+'|First random candidate']=candidates[0] if candidates else None
        candidate_sets[condition]=candidates
    # Independent global affected-cycle enumeration for every distinct selected graph.
    graphs={};verified={}
    for method,r in selected.items():
        if r is None:continue
        key=tuple(map(tuple,r['rewires']))
        if key not in verified:
            independent=structure.independent_delta(r['rewires'])
            assert all(independent[k]==r['structure'][k] for k in independent)
            verified[key]=independent
        graphs[method]=graph(data,t,r['rewires'])[0]
    checks['selected_global_cycle_checks']=[dict(rewires=[list(x) for x in k],**v) for k,v in verified.items()]
    rows=[];masks={}
    for j,seed in enumerate(CONFIG['fresh_seeds'][trial]):
        cs=H.explain(model,clean,seed);repeat=H.explain(model,clean,CONFIG['repeat_seeds'][trial][j]);base=overlap(cs,repeat,structure.edge)
        cfid=H.fid_scores(model,clean,cs);fresh={};cache={}
        for method,r in selected.items():
            condition,selector=method.split('|');feasible=bool(r and r['feasible'])
            metric=dict(row_overlap=None,pair_overlap=None);fid={k:None for k in H.FID}
            if r is not None:
                key=tuple(map(tuple,r['rewires']))
                if key not in cache:
                    score=H.explain(model,graphs[method],seed);cache[key]=(score,H.fid_scores(model,graphs[method],score))
                score,fid=cache[key];fresh[method]=score;metric=overlap(cs,score,structure.edge)
            rows.append(dict(dataset=name,target=t,trial=trial,phase=phase,seed=seed,condition=condition,selector=selector,
                             selected=int(r is not None),feasible=int(feasible),preserved=int(bool(r and r['preserved'])),
                             probability_change=None if r is None else r['probability_change'],**metric,
                             clean_repeat_pair_overlap=base['pair_overlap'],clean_repeat_row_overlap=base['row_overlap'],
                             joint_disruption=(1-metric['pair_overlap']) if feasible else 0.,
                             excess_disruption=(base['pair_overlap']-metric['pair_overlap']) if feasible else 0.,
                             **{'clean_'+k:v for k,v in cfid.items()},**{'attacked_'+k:v for k,v in fid.items()}))
        masks[str(seed)]=dict(clean=cs,clean_repeat=repeat,repeat_seed=CONFIG['repeat_seeds'][trial][j],attacks=fresh)
        print(name,t,trial,'fresh seed',seed,flush=True)
    for k,v in frozen.items():torch.testing.assert_close(model.state_dict()[k],v,atol=0,rtol=0)
    torch.cuda.synchronize()
    return dict(dataset=name,target=t,trial=trial,phase=phase,manifest_id=mid,seconds=time.time()-start,source_sha256=sha(source),
                clean_label=label,clean_probability=cp,clean_selection_scores=clean_scores,selection_seed=s,candidates=candidate_sets,
                generation=generation,selected=selected,checks=checks,rows=rows,explanations=masks,
                unique_prediction_calls=prediction_calls,unique_candidate_explainer_calls=explain_calls,
                graph_details={'Clean':dict(ids=clean['ids'],global_nodes=clean['global_nodes']),
                               **{m:dict(ids=g['ids'],global_nodes=g['global_nodes']) for m,g in graphs.items()}})
def report(phase,d,names):
    folder=OUT/phase;cases=[json.loads(p.read_text()) for p in (folder/'cases').glob('*.json')];mid=identity(d)
    assert all(c['manifest_id']==mid for c in cases)
    ids=d[phase];trials=[0] if phase=='screening' else [1,2];expected={(n,t,s) for n in names for t in ids[n] for s in trials}
    done={(c['dataset'],c['target'],c['trial']) for c in cases};assert len(done)==len(cases) and done<=expected
    cov=dict(saved=len(done),expected=len(expected),complete=done==expected);save(folder/'coverage.json',cov)
    rows=[r for c in cases for r in c['rows']]
    if not rows:return cov,[],cases
    df=pd.DataFrame(rows);df.to_csv(folder/'per_seed.csv',index=False)
    metrics=['selected','feasible','preserved','probability_change','row_overlap','pair_overlap','clean_repeat_pair_overlap',
             'clean_repeat_row_overlap','joint_disruption','excess_disruption']+['clean_'+k for k in H.FID]+['attacked_'+k for k in H.FID]
    trials_df=df.groupby(['dataset','target','trial','condition','selector'])[metrics].mean().reset_index()
    target=trials_df.groupby(['dataset','target','condition','selector'])[metrics].mean().reset_index();target.to_csv(folder/'per_target.csv',index=False)
    summary=[];rng=np.random.default_rng(CONFIG['bootstrap_seed'])
    for (name,condition,selector),g in target.groupby(['dataset','condition','selector']):
        a=g.excess_disruption.to_numpy();boot=a[rng.integers(0,len(a),(5000,len(a)))].mean(1)
        summary.append(dict(dataset=name,condition=condition,selector=selector,targets=len(g),feasible_coverage=float(g.feasible.mean()),
                            joint_disruption=float(g.joint_disruption.mean()),excess_disruption=float(a.mean()),
                            excess_lo=float(np.quantile(boot,.025)),excess_hi=float(np.quantile(boot,.975))))
    pd.DataFrame(summary).to_csv(folder/'summary.csv',index=False)
    comparisons=[]
    for name,g in target.groupby('dataset'):
        comparisons_spec=[(c,'Best of 40',c,'First random candidate') for c in CONDITIONS]+[('degree_cycles','Best of 40','source_fixed','Best of 40'),('degree_cycles','Best of 40','degree','Best of 40')]
        for ac,ass,bc,bss in comparisons_spec:
            a=g[(g.condition==ac)&(g.selector==ass)].set_index('target').sort_index();b=g[(g.condition==bc)&(g.selector==bss)].set_index('target').sort_index()
            assert a.index.equals(b.index);delta=(a.excess_disruption-b.excess_disruption).to_numpy()
            boot=delta[rng.integers(0,len(delta),(5000,len(delta)))].mean(1)
            comparisons.append(dict(dataset=name,a=ac+'|'+ass,b=bc+'|'+bss,mean=float(delta.mean()),lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975))))
    pd.DataFrame(comparisons).to_csv(folder/'paired_effects.csv',index=False)
    costs=[dict(dataset=c['dataset'],target=c['target'],trial=c['trial'],condition=k,**v,
                feasible_candidates=sum(r['feasible'] for r in c['candidates'][k])) for c in cases for k,v in c['generation'].items()]
    pd.DataFrame(costs).to_csv(folder/'search_coverage.csv',index=False)
    lines=['# Exploratory graph-pattern constraints', '',f'**{phase.upper()} {"COMPLETE" if cov["complete"] else "PROVISIONAL"}: {len(done)}/{len(expected)} target-search cases.**','',
           'Three record rewirings = six removed/inserted edge connections; best-of-40 random search versus the first '
           'structurally valid random candidate. Frozen features and model. Degree+cycle constraints preserve global '
           'multiplicity-weighted two/three-cycle totals, not every individual motif. Failure cases remain in joint denominators. '
           'Candidate-generation shortfalls and actual calls are recorded. Five fresh seeds are averaged within targets; '
           'expanded trials are also averaged within targets. Clean repeats are a variability reference, not a matched null.', '',
           '| Dataset | Constraint | Selector | Targets | Feasible coverage | Joint disruption | Excess over clean repeat, 95% interval |',
           '|---|---|---|---:|---:|---:|---|']
    for r in summary:lines.append(f'| {r["dataset"]} | {r["condition"]} | {r["selector"]} | {r["targets"]} | {r["feasible_coverage"]:.2%} | {r["joint_disruption"]:.4f} | {r["excess_disruption"]:.4f} ({r["excess_lo"]:.4f}, {r["excess_hi"]:.4f}) |')
    lines+=['','The prespecified primary endpoint is degree_cycles / Best of 40 excess disruption. '
            'Intervals omit graph-node dependence and model-training variation. Endpoint overlap is not explanation quality. '
            'No economic feasibility or feature consistency is claimed. Partial summaries are provisional; the gate is applied only after all screening targets.']
    (folder/'REPORT.md').write_text('\n'.join(lines),encoding='utf8');return cov,summary,cases
def phase_run(phase,d,names,pilot=False):
    folder=OUT/phase;(folder/'cases').mkdir(parents=True,exist_ok=True);mid=identity(d)
    for name in names:
        b=torch.load(STUDY/f'complete_graphs/prepared/{name}.pt',map_location='cpu',weights_only=False);data=b['data']
        model=H.MarasiGraphSAGE(data.num_features,b['hidden']).to('cuda');model.load_state_dict(b['state']);model.eval()
        for p in model.parameters():p.requires_grad_(False)
        structure=Structure(data.edge_index.numpy(),data.num_nodes)
        for trial in ([0] if phase=='screening' else [1,2]):
            targets=d[phase][name][:1] if pilot else d[phase][name]
            for i,t in enumerate(targets):
                path=folder/f'cases/{name}_{t}_{trial}.json'
                if path.exists():assert json.loads(path.read_text())['manifest_id']==mid;continue
                save(OUT/'status.json',dict(state='running',phase=phase,pid=os.getpid(),dataset=name,target=t,trial=trial,manifest_id=mid))
                print('START',phase,name,t,trial,flush=True)
                c=one(name,t,trial,phase,data,model,structure,mid,validate=i==0);save(path,c);report(phase,d,names)
                print('SAVED',phase,name,t,trial,'seconds',round(c['seconds'],1),flush=True);torch.cuda.empty_cache()
        del structure,model,data,b;torch.cuda.empty_cache()
    return report(phase,d,names)
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['pilot','pipeline']);a=p.parse_args()
    priority();assert torch.cuda.is_available();torch.cuda.set_per_process_memory_fraction(CONFIG['gpu_fraction'])
    OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'controller.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        d=freeze();mid=identity(d)
        if a.mode=='pilot':
            validation=self_test();cov,summary,cases=phase_run('screening',d,CONFIG['datasets'],pilot=True)
            assert len(cases)==2 and all('native_edited' in c['checks'] for c in cases),'Need a valid edited-graph technical check on both datasets'
            save(OUT/'validation.json',dict(**validation,manifest_id=mid,real_graph_checks=2));save(OUT/'status.json',dict(state='pilot_complete',manifest_id=mid,**cov));return
        v=json.loads((OUT/'validation.json').read_text());assert v['passed'] and v['manifest_id']==mid
        cov,summary,cases=phase_run('screening',d,CONFIG['datasets']);assert cov['complete']
        decisions=[];names=[]
        for name in CONFIG['datasets']:
            r=next(r for r in summary if r['dataset']==name and r['condition']=='degree_cycles' and r['selector']=='Best of 40')
            qualifies=(r['targets']==10 and r['feasible_coverage']>=.8 and r['excess_disruption']>=.10 and r['excess_lo']>0 and r['joint_disruption']>=.30)
            decisions.append(dict(**r,qualifies=qualifies))
            if qualifies:names.append(name)
        save(OUT/'promotion_decision.json',dict(manifest_id=mid,qualified_datasets=names,decisions=decisions))
        if names:phase_run('expanded',d,names)
        save(OUT/'status.json',dict(state='complete',manifest_id=mid,expanded_datasets=names))
    except Exception:save(OUT/'status.json',dict(state='failed',traceback=traceback.format_exc()));raise
    finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
