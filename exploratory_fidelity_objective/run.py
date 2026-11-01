"""Experimental fixed-pool objective comparison and conditional larger pilot."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import argparse,copy,ctypes,hashlib,importlib.util,json,random,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;STUDY=ROOT.parent;OUT=ROOT/'results'
spec=importlib.util.spec_from_file_location('validated_audit',STUDY/'followup_audit/run.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
np=H.np;pd=H.pd;torch=H.torch;save=H.save;sha=H.sha
if os.name=='nt':
    ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
    ctypes.windll.kernel32.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint]
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)

METHODS=['Cosine selector','Necessity selector','First feasible candidate']
CONFIG=dict(datasets=['amlsim','hi_small'],screening_targets=20,expanded_targets=50,subset_seed=1618033,
            proposals=40,budget=6,probability_cap=.02,k=10,screening_trials=[0],expanded_trials=[1,2],
            selection_seeds=[61001,61002,61003],screening_seeds=list(range(71001,71006)),expanded_seeds=list(range(81001,81006)),
            minimum_coverage=.8,minimum_mean_advantage=.005,bootstrap_draws=5000)

def identity(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()

def freeze():
    sources={str(p.relative_to(STUDY)):sha(p) for p in [Path(__file__),ROOT/'README.md',STUDY/'followup_audit/run.py',
             STUDY/'complete_graphs/prepare.py',STUDY/'complete_graphs/attack_core.py',STUDY/'framework/src/models/marasi_models.py']}
    checkpoints={str((STUDY/f'complete_graphs/prepared/{n}.pt').relative_to(STUDY)):sha(STUDY/f'complete_graphs/prepared/{n}.pt') for n in CONFIG['datasets']}
    path=OUT/'manifest.json'
    if path.exists():
        d=json.loads(path.read_text());assert d['config']==CONFIG and d['sources']==sources and d['checkpoints']==checkpoints
        assert d['torch']==torch.__version__ and d['pyg']==__import__('torch_geometric').__version__
        return d
    rng=np.random.default_rng(CONFIG['subset_seed']);screen={};expanded={};census={};inputs={}
    for name in CONFIG['datasets']:
        p=STUDY/f'complete_graphs/results/full/{name}_targets.json';ids=json.loads(p.read_text())['selected'];inputs[str(p.relative_to(STUDY))]=sha(p)
        qualified=[];excluded=[]
        for t in ids:
            p=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json';raw=p.read_bytes();old=json.loads(raw)
            inputs[str(p.relative_to(STUDY))]=hashlib.sha256(raw).hexdigest()
            (qualified if len(old['clean']['GNNExplainer'])>=10 else excluded).append(t)
        chosen=[int(x) for x in rng.choice(sorted(qualified),70,replace=False)]
        screen[name]=sorted(chosen[:20]);expanded[name]=sorted(chosen[20:]);assert not set(screen[name])&set(expanded[name])
        census[name]=dict(original=len(ids),qualified=len(qualified),excluded=excluded)
    d=dict(config=CONFIG,sources=sources,checkpoints=checkpoints,input_hashes=inputs,screening=screen,expanded=expanded,census=census,
           torch=torch.__version__,pyg=__import__('torch_geometric').__version__)
    save(path,d);return d

def domain(data,target):
    nodes,e,m,mask=H.k_hop_subgraph(target,2,data.edge_index,num_nodes=data.num_nodes)
    edge_ids=mask.nonzero().flatten();pairs=set(map(tuple,e.T.tolist()))
    deleted=[f'E{int(i)}' for i in edge_ids if int(data.edge_index[0,i])!=int(data.edge_index[1,i])]
    added=[f'A{a}:{b}' for a in nodes.tolist() for b in nodes.tolist() if a!=b and (a,b) not in pairs]
    return deleted+added

def graph(data,target,ids):
    e,edge_ids=H.physical(data,ids);g=H.local_graph(data,e,edge_ids,target)
    return g,e,edge_ids

def validate_candidate(data,model,target,g,e,ids):
    # Independent full physical prediction, plus original native-mask/fidelity path.
    cpu=copy.deepcopy(model).cpu().eval()
    with torch.no_grad():ref=cpu(data.x,e)[target]
    torch.testing.assert_close(H.predict(model,g)[0].cpu(),ref,atol=3e-4,rtol=3e-4)
    scores=H.explain(model,g,2026)
    checks=H.validate_graph(model,data,e,ids,target,g,scores,scores)
    del cpu
    return dict(independent_full_prediction=True,**checks)

def one_case(name,target,trial,phase,data,model,mid,validate):
    start=time.time();frozen={k:v.clone() for k,v in model.state_dict().items()}
    source=STUDY/f'gnn_three_trials/results/full/cases/{name}_{target}_2026.json'
    source_case=json.loads(source.read_text());clean,e,ids=graph(data,target,[])
    original=H.explain(model,clean,2026);H.assert_scores(original,source_case['clean']['GNNExplainer'])
    assert len(clean['ids'])>=10
    checks=dict(saved_clean_mask=True,permissions=True,frozen_model=True,finite=True)
    if validate:checks['clean_native_parity']=H.validate_graph(model,data,e,ids,target,clean,original,source_case['clean']['GNNExplainer'])
    clean_out,label=H.predict(model,clean);clean_prob=float(clean_out.softmax(-1)[label])
    selection_seed=CONFIG['selection_seeds'][trial]
    clean_scores=H.explain(model,clean,selection_seed);allowed=domain(data,target)
    rng=random.Random(918273+target*37+trial*1000003+(0 if name=='amlsim' else 170000003))
    candidates=[];memo={};native_evaluations=0
    for i in range(40):
        edits=sorted(rng.sample(allowed,6));key=tuple(edits)
        assert len(set(edits))==6
        if key in memo:
            result=dict(memo[key],proposal=i+1,duplicate=True);candidates.append(result);continue
        g,edges,edge_ids=graph(data,target,edits);out,pred=H.predict(model,g);prob=float(out.softmax(-1)[label]);gap=abs(prob-clean_prob)
        feasible=pred==label and gap<=CONFIG['probability_cap'] and len(g['ids'])>=10
        result=dict(proposal=i+1,duplicate=False,edit_ids=edits,preserved=pred==label,probability=prob,probability_change=gap,
                    edge_count=len(g['ids']),feasible=feasible)
        if validate and i==0:checks['edited_native_parity']=validate_candidate(data,model,target,g,edges,edge_ids)
        if feasible:
            scores=H.explain(model,g,selection_seed);native_evaluations+=1
            fid=H.fid_scores(model,g,scores)
            result.update(scores=scores,fidelity=fid,**H.compare(clean_scores,scores,10),**H.binary_top25(clean_scores,scores))
        memo[key]=result;candidates.append(result)
        if (i+1)%10==0:print(name,target,trial,'candidate',i+1,flush=True)
    feasible=[r for r in candidates if r['feasible']]
    base=dict(dataset=name,target=target,trial=trial,phase=phase,manifest_id=mid,source_sha256=sha(source),
              feasible_count=len(feasible),unique_candidates=len(memo),native_candidate_evaluations=native_evaluations,
              clean_probability=clean_prob,clean_label=label,candidates=candidates,selection_seed=selection_seed,checks=checks)
    if not feasible:
        for k,v in frozen.items():torch.testing.assert_close(v,model.state_dict()[k],atol=0,rtol=0)
        return dict(**base,seconds=time.time()-start,rows=[],selected={},failure='No feasible candidate; target retained in coverage')
    selected={'Cosine selector':min(feasible,key=lambda r:(r['cosine'],r['proposal'])),
              'Necessity selector':min(feasible,key=lambda r:(r['fidelity']['soft_plus'],r['proposal'])),
              'First feasible candidate':feasible[0]}
    assert selected['Necessity selector']['fidelity']['soft_plus']<=selected['Cosine selector']['fidelity']['soft_plus']+1e-12
    graphs={'Clean':clean}
    for m,r in selected.items():graphs[m]=graph(data,target,r['edit_ids'])[0]
    # Use the same Monte Carlo control when two selectors choose the same graph.
    control_cache={};controls={}
    for m,g in graphs.items():
        key=() if m=='Clean' else tuple(selected[m]['edit_ids'])
        control_seed=int(hashlib.sha256(json.dumps([name,target,trial,key]).encode()).hexdigest()[:8],16)
        if key not in control_cache:control_cache[key]=H.random_control(model,g,control_seed)
        controls[m]=control_cache[key]
    fresh=CONFIG['screening_seeds'] if phase=='screening' else CONFIG['expanded_seeds']
    rows=[];masks={}
    for s in [selection_seed]+fresh:
        # Identical selected graphs share the same-seed explanation by construction.
        score_cache={};scores={}
        for m,g in graphs.items():
            key=() if m=='Clean' else tuple(selected[m]['edit_ids'])
            if key not in score_cache:score_cache[key]=H.explain(model,g,s)
            scores[m]=score_cache[key]
        fids={m:H.fid_scores(model,g,scores[m]) for m,g in graphs.items()};masks[str(s)]=scores
        for m in METHODS:
            r=dict(dataset=name,target=target,trial=trial,method=m,stage='selection_seed' if s==selection_seed else 'fresh',seed=s,
                   probability_change=selected[m]['probability_change'],preserved=int(selected[m]['preserved']),
                   **H.compare(scores['Clean'],scores[m],10),**H.binary_top25(scores['Clean'],scores[m]))
            for metric in H.FID:
                cf=fids['Clean'][metric];af=fids[m][metric];cr=controls['Clean']['mean'][metric];ar=controls[m]['mean'][metric]
                r.update({f'clean_{metric}':cf,f'attacked_{metric}':af,f'reduction_{metric}':cf-af,
                          f'clean_random_{metric}':cr,f'attacked_random_{metric}':ar,f'excess_reduction_{metric}':(cf-cr)-(af-ar)})
            assert all(np.isfinite(v) for v in r.values() if isinstance(v,(int,float)))
            rows.append(r)
    for k,v in frozen.items():torch.testing.assert_close(v,model.state_dict()[k],atol=0,rtol=0)
    torch.cuda.synchronize()
    return dict(**base,seconds=time.time()-start,selected=selected,rows=rows,random_controls=controls,explanations=masks)

def report(phase,d,expected):
    folder=OUT/phase;cases=[json.loads(p.read_text()) for p in (folder/'cases').glob('*.json')]
    mid=identity(d);assert all(c['manifest_id']==mid for c in cases)
    done={(c['dataset'],c['target'],c['trial']) for c in cases};assert len(done)==len(cases) and done<=expected
    coverage=dict(saved=len(done),expected=len(expected),complete=done==expected,feasible=sum(c['feasible_count']>0 for c in cases))
    save(folder/'coverage.json',coverage)
    rows=[r for c in cases for r in c['rows']];pd.DataFrame(rows).to_csv(folder/'per_seed.csv',index=False)
    lines=['# EXPLORATORY: candidate-selection objective comparison','',f'**{phase.upper()} - {"COMPLETE" if coverage["complete"] else "PROVISIONAL"}: {len(done)}/{len(expected)} target-search cases; {coverage["feasible"]} with a feasible candidate.**', '',
           'Separate from the main study. Common 40-candidate pools, six edits, unchanged class, probability gap <= 0.02 and exactly ten selected explanation edges. No-feasible-candidate cases remain in coverage. Selection-seed objective improvement is expected by construction and is not evidence for promotion. All comparisons below use fresh explanation seeds.', '',
           '| Dataset | Comparator | Paired extra necessity reduction (pp) | 95% interval (pp) | Random-adjusted advantage (pp) |', '|---|---|---:|---:|---:|']
    paired=[];target_rows=None
    if rows:
        frame=pd.DataFrame(rows);fresh=frame[frame.stage=='fresh']
        numeric=['reduction_soft_plus','excess_reduction_soft_plus','reduction_soft_minus','reduction_hard_plus','reduction_hard_minus','cosine','binary_top25_cosine','jaccard','probability_change']
        # Average seeds within trial, then average search trials within target.
        trials=fresh.groupby(['dataset','target','trial','method'])[numeric].mean().reset_index()
        target_rows=trials.groupby(['dataset','target','method'])[numeric].mean().reset_index();target_rows.to_csv(folder/'per_target.csv',index=False)
        target_rows.groupby(['dataset','method'])[numeric].agg(['mean','std']).to_csv(folder/'summary.csv')
        rng=np.random.default_rng(471)
        for name,g in target_rows.groupby('dataset'):
            for comparator in ['Cosine selector','First feasible candidate']:
                a=g[g.method=='Necessity selector'].set_index('target').sort_index();b=g[g.method==comparator].set_index('target').sort_index();assert a.index.equals(b.index)
                vals=(a.reduction_soft_plus-b.reduction_soft_plus).to_numpy();adjusted=(a.excess_reduction_soft_plus-b.excess_reduction_soft_plus).to_numpy()
                boot=vals[rng.integers(0,len(vals),(5000,len(vals)))].mean(axis=1)
                r=dict(dataset=name,comparator=comparator,targets=len(vals),mean=float(vals.mean()),lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975)),random_adjusted_mean=float(adjusted.mean()))
                paired.append(r);lines.append(f"| {name} | {comparator} | {100*r['mean']:.4f} | ({100*r['lo']:.4f}, {100*r['hi']:.4f}) | {100*r['random_adjusted_mean']:.4f} |")
    pd.DataFrame(paired).to_csv(folder/'paired_effects.csv',index=False)
    lines+=['','Positive values indicate larger soft-necessity reduction for the necessity selector. These are conditional descriptive intervals from target resampling; they omit graph-node dependence and classifier-training variation. Random-adjusted values subtract size-matched random-mask necessity within each graph. Soft necessity is one metric, not explanation accuracy or a universal quality measure. Sufficiency, hard fidelity and overlap are secondary outcomes and must be inspected for tradeoffs.', '',
            'The larger pilot, if triggered, uses disjoint preselected targets and additional search seeds. Screening and expansion must be reported separately. No results are automatically incorporated into the main study.']
    if cases:lines.append(f'\nMean saved case runtime: {np.mean([c["seconds"] for c in cases]):.1f} seconds.')
    (folder/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    return coverage,paired,cases

def run_phase(phase,d,names,limit=0):
    folder=OUT/phase;(folder/'cases').mkdir(parents=True,exist_ok=True)
    ids=d['screening'] if phase=='screening' else d['expanded'];trials=[0] if phase=='screening' else [1,2]
    expected={(n,t,s) for n in names for t in ids[n] for s in trials};mid=identity(d)
    try:
        for name in names:
            bundle=torch.load(STUDY/f'complete_graphs/prepared/{name}.pt',map_location='cpu',weights_only=False);data=bundle['data']
            model=H.MarasiGraphSAGE(data.num_features,bundle['hidden']).to('cuda');model.load_state_dict(bundle['state']);model.eval()
            for p in model.parameters():p.requires_grad_(False)
            selected=ids[name][:limit] if limit else ids[name]
            for trial in trials:
                for i,t in enumerate(selected):
                    source=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json'
                    assert sha(source)==d['input_hashes'][str(source.relative_to(STUDY))],'Saved input changed'
                    path=folder/f'cases/{name}_{t}_{trial}.json'
                    if path.exists():assert json.loads(path.read_text())['manifest_id']==mid;continue
                    save(folder/'status.json',dict(state='running',pid=os.getpid(),dataset=name,target=t,trial=trial,manifest_id=mid))
                    print('START',phase,name,t,trial,flush=True)
                    result=one_case(name,t,trial,phase,data,model,mid,validate=i==0);save(path,result)
                    print('SAVED',phase,name,t,trial,'seconds',round(result['seconds'],1),'feasible',result['feasible_count'],flush=True)
                    if len(list((folder/'cases').glob('*.json')))%5==0:report(phase,d,expected)
                    torch.cuda.empty_cache()
            del model,data,bundle;torch.cuda.empty_cache()
        cov,paired,cases=report(phase,d,expected)
        save(folder/'status.json',dict(state='complete' if cov['complete'] else 'pilot_complete',manifest_id=mid,**cov))
        return cov,paired,cases
    except Exception:
        save(folder/'status.json',dict(state='failed',traceback=traceback.format_exc()));raise

def gate(d,paired,cases):
    qualified=[];details={}
    for name in CONFIG['datasets']:
        cs=[c for c in cases if c['dataset']==name];ps=[r for r in paired if r['dataset']==name]
        coverage=sum(c['feasible_count']>0 for c in cs)/20
        enough=len(cs)==20 and coverage>=.8
        promising=enough and len(ps)==2 and all(r['mean']>=.005 and r['lo']>0 and r['random_adjusted_mean']>0 for r in ps)
        details[name]=dict(attempted=len(cs),feasible_coverage=coverage,promising=promising,comparisons=ps)
        if promising:qualified.append(name)
    save(OUT/'promotion_decision.json',dict(qualified_datasets=qualified,criteria=CONFIG,details=details,manifest_id=identity(d)))
    return qualified

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['pilot','pipeline']);args=p.parse_args()
    assert torch.cuda.is_available();torch.cuda.set_per_process_memory_fraction(.25)
    OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'controller.lock';fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        d=freeze()
        if args.mode=='pilot':
            cov,_,cases=run_phase('screening',d,CONFIG['datasets'],limit=1)
            assert len(cases)==2 and all(c['checks'].get('edited_native_parity') for c in cases)
            save(OUT/'technical_pilot.json',dict(passed=True,manifest_id=identity(d),cases=2));return
        pilot=json.loads((OUT/'technical_pilot.json').read_text());assert pilot['passed'] and pilot['manifest_id']==identity(d)
        cov,paired,cases=run_phase('screening',d,CONFIG['datasets']);assert cov['complete']
        names=gate(d,paired,cases)
        if names:run_phase('expanded',d,names)
        save(OUT/'status.json',dict(state='complete',exploratory=True,expanded_datasets=names,manifest_id=identity(d)))
    except Exception:
        save(OUT/'status.json',dict(state='failed',traceback=traceback.format_exc()));raise
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
