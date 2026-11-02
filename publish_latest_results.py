"""Rebuild a publication snapshot from verified immutable cases, without editing live runs."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def identity(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
def worker(kind,work):
    folders=dict(resolution='exploratory_resolution_validation',pattern='exploratory_pattern_constraints',
                 transaction='exploratory_transaction_consistency',subgraphx='subgraphx_hi_small',
                 subgraphx_fresh='exploratory_subgraphx_fresh_seed')
    folder=folders[kind];sys.path.insert(0,str(ROOT/folder))
    spec=importlib.util.spec_from_file_location('publication_report_module',ROOT/folder/'run.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    m=json.loads((work/'manifest.json').read_text());mod.OUT=work
    if kind in ['resolution','subgraphx_fresh']:mod.report(m)
    elif kind=='pattern':
        mod.report('screening',m,m['config']['datasets'])
        decision=json.loads((work/'promotion_decision.json').read_text())
        if (work/'expanded/cases').exists():mod.report('expanded',m,decision['qualified_datasets'])
    elif kind=='transaction':
        mod.report(m,identity(m),phase='pilot')
    else:mod.report(work,{(t,s) for t in m['targets'] for s in m['trials']})
def validate_sources(m):
    checked=0
    for field in ['sources','inputs','input_hashes','checkpoints','original_sources']:
        for rel,expected in m.get(field,{}).items():
            if isinstance(expected,str) and len(expected)==64:
                assert sha(ROOT/rel)==expected,('changed source/input',rel);checked+=1
    return checked
def stage_cases(source,target,m,kind,phase):
    target.mkdir(parents=True,exist_ok=True);counts=Counter();hashes={};identities=set();permutation=Counter();maxerr={};pattern_stats=defaultdict(Counter)
    if kind=='subgraphx':expected={(int(t),int(s)) for t in m['targets'] for s in m['trials']}
    elif kind=='subgraphx_fresh':expected={(m['config']['dataset'],int(t),0) for t in m['targets']}
    else:
        key='targets' if kind in ['resolution','transaction'] else phase
        trials=[1,2] if phase=='expanded' else [0]
        expected={(n,int(t),s) for n,ts in m[key].items() for t in ts for s in trials}
    for p in sorted(source.glob('*.json')):
        raw=p.read_bytes();c=json.loads(raw);ident=(int(c['target']),int(c['trial'])) if kind=='subgraphx' else (c['dataset'],int(c['target']),int(c.get('trial',0)))
        assert ident in expected and ident not in identities;identities.add(ident)
        if kind=='subgraphx':
            assert c['params']==m['params'] and c['sources']==m['sources'] and all(c['checks'].values())
        else:assert c['manifest_id']==identity(m)
        if kind=='subgraphx_fresh':
            cfg=m['config'];seeds={cfg['source_trial'],*cfg['fresh_seeds']}
            assert set(map(int,c['explanations']))==seeds and len(c['rows'])==2*len(seeds)
            assert {(r['method'],r['seed']) for r in c['rows']}=={(method,seed) for method in cfg['methods'] for seed in seeds}
            source_key=f'subgraphx_hi_small/results/full/cases/hi_small_{c["target"]}_2026.json'
            assert c['source_sha256']==m['inputs'][source_key]
            original=json.loads((ROOT/source_key).read_text())
            assert c['checks']['model_unchanged']
            for method in ['Clean']+cfg['methods']:
                assert c['checks'][method]['source_seed_native_set_parity']
                saved=original['clean']['SubgraphX'] if method=='Clean' else original['attacks'][method]['scores']
                assert c['explanations']['2026']['graphs'][method]['scores']==saved
            if c['target'] in m['targets'][:cfg['technical_targets']]:
                assert c['technical'] and c['checks']['same_seed_repeat']
                assert all(c['checks'][method]['full_local_physical_fidelity_parity'] for method in ['Clean']+cfg['methods'])
            for row in c['rows']:
                seed=row['seed'];ev=c['explanations'][str(seed)]
                assert row['stage']==('selection_seed' if seed==cfg['source_trial'] else 'fresh')
                if seed!=cfg['source_trial']:assert ev['repeat_seed']==cfg['repeat_seeds'][cfg['fresh_seeds'].index(seed)]
                a=set(ev['graphs']['Clean']['scores']);b=set(ev['graphs'][row['method']]['scores']);rep=set(ev['clean_repeat']['scores'])
                def overlap(x,y):
                    return (len(x&y)/(len(x)*len(y))**.5 if x and y else float(not (x|y)),len(x&y)/len(x|y) if x|y else 1.)
                similarity,jaccard=overlap(a,b);repeat_similarity,repeat_jaccard=overlap(a,rep)
                for key,value in dict(similarity=similarity,jaccard=jaccard,clean_repeat_similarity=repeat_similarity,
                                      clean_repeat_jaccard=repeat_jaccard,excess_disruption=repeat_similarity-similarity).items():
                    assert abs(row[key]-value)<1e-12,(p,key)
                assert row['preserved']==int(original['attacks'][row['method']]['preserved'])
                for metric in ['hard_plus','hard_minus','soft_plus','soft_minus']:
                    clean=ev['fidelity']['Clean'][metric];attacked=ev['fidelity'][row['method']][metric]
                    assert row['clean_'+metric]==clean and row['attacked_'+metric]==attacked
                    assert abs(row['delta_'+metric]-(attacked-clean))<1e-12
        if kind=='resolution':
            assert set(map(int,c['explanations']))==set(m['config']['seeds'])
            assert len(c['rows'])==50
            for ev in c['explanations'].values():
                n=c['dataset'];permutation[n]+=1;err=ev['permutation_logit_max_error'];assert err<=3e-5
                maxerr[n]=max(maxerr.get(n,0),err)
                assert sorted(ev['permutation'])==list(range(len(c['graph_details']['Clean']['ids'])))
        if kind=='pattern':
            assert len(c['rows'])==30
            seeds=m['config']['fresh_seeds'][c['trial']]
            assert set(map(int,c['explanations']))==set(seeds)
            assert {(r['condition'],r['selector'],r['seed']) for r in c['rows']}=={(condition,selector,seed) for condition in ['source_fixed','degree','degree_cycles'] for selector in ['Best of 40','First random candidate'] for seed in seeds}
            assert not set(m['screening'][c['dataset']])&set(m['expanded'][c['dataset']])
            checked={tuple(map(tuple,v['rewires'])):v for v in c['checks']['selected_global_cycle_checks']}
            for method,r in c['selected'].items():
                if method.startswith('degree_cycles|') and r:
                    assert all(r['structure'][k]==0 for k in ['cycles2_delta','cycles3_delta','indegree_l1','outdegree_l1'])
                    independent=checked[tuple(map(tuple,r['rewires']))]
                    assert independent['cycles2_delta']==independent['cycles3_delta']==0
            stats=pattern_stats[c['dataset']];stats['search_cases']+=1
            chosen=c['selected']['degree_cycles|Best of 40'];count=c['generation']['degree_cycles']['accepted']
            stats['feasible_degree_cycle_cases']+=int(bool(chosen and chosen['feasible']))
            stats['zero_structural_pool_cases']+=int(count==0)
            stats['nonempty_pool_without_feasible_attack']+=int(count>0 and chosen is None)
            stats['fewer_than_40_structural_candidates']+=int(count<40)
            stats['total_structural_candidates']+=count
        (target/p.name).write_bytes(raw);counts[c['dataset']]+=1;hashes[p.name]=hashlib.sha256(raw).hexdigest()
    return dict(saved=len(identities),expected=len(expected),complete=identities==expected,by_dataset=dict(counts),
                case_sha256=hashes,permutation_comparisons=dict(permutation),maximum_permutation_logit_error=maxerr,
                pattern_search_validation={k:dict(v) for k,v in pattern_stats.items()})
def capture():
    stamp=datetime.now(timezone(timedelta(hours=8)));name=stamp.strftime('%Y-%m-%d-%H%M%S')
    out=ROOT/'publication_snapshots'/name;assert not out.exists();out.mkdir(parents=True)
    temp=Path(tempfile.mkdtemp(prefix='_publication_work_',dir=ROOT)).resolve()
    assert temp.is_relative_to(ROOT.resolve()) and temp.name.startswith('_publication_work_')
    specs=[('resolution','exploratory_resolution_validation',[('', 'cases')]),
           ('pattern','exploratory_pattern_constraints',[('screening','screening/cases'),('expanded','expanded/cases')]),
           ('transaction','exploratory_transaction_consistency',[('pilot','pilot/cases')]),
           ('subgraphx','subgraphx_hi_small',[('','cases')]),
           ('subgraphx_fresh','exploratory_subgraphx_fresh_seed',[('','cases')])]
    records={};config_hashes={};allowed=['REPORT.md','coverage.json','summary.csv','paired_effects.csv','trial_means.csv','fidelity_paired_effects.csv','search_coverage.csv']
    try:
        for kind,folder,phases in specs:
            src=ROOT/folder/'results';src=src/'full' if kind=='subgraphx' else src
            mpath=src/'manifest.json';m=json.loads(mpath.read_text());checked=validate_sources(m)
            work=temp/folder;work.mkdir();write(work/'manifest.json',m);config_hashes[folder]=sha(mpath)
            if kind=='pattern':
                decision=json.loads((src/'promotion_decision.json').read_text());assert decision['manifest_id']==identity(m)
                write(work/'promotion_decision.json',decision)
            for phase,rel in phases:
                if not (src/rel).exists():continue
                r=stage_cases(src/rel,work/rel,m,kind,phase);r['source_hashes_verified']=checked
                records[folder+('/'+phase if phase else '')]=r
            completed=subprocess.run([sys.executable,str(Path(__file__)),'--worker',kind,'--work',str(work)],cwd=ROOT,capture_output=True,text=True)
            if completed.returncode:raise RuntimeError(completed.stdout+completed.stderr)
            for phase,rel in phases:
                source_folder=work/phase;dest=out/folder/phase
                if not (work/rel).exists():continue
                dest.mkdir(parents=True,exist_ok=True)
                for filename in allowed:
                    p=source_folder/filename
                    if p.exists():
                        raw=p.read_bytes();assert raw and b'\0' not in raw,(p,'invalid report');(dest/filename).write_bytes(raw)
            if kind=='pattern':
                # Verify that the published promotion decision agrees with the rebuilt screening summary.
                import pandas as pd
                summary=pd.read_csv(work/'screening/summary.csv');qualified=[]
                for d in decision['decisions']:
                    r=summary[(summary.dataset==d['dataset'])&(summary.condition=='degree_cycles')&(summary.selector=='Best of 40')].iloc[0]
                    for metric in ['feasible_coverage','joint_disruption','excess_disruption','excess_lo','excess_hi']:
                        assert abs(float(r[metric])-d[metric])<1e-10
                    ok=r.targets==10 and r.feasible_coverage>=.8 and r.excess_disruption>=.10 and r.excess_lo>0 and r.joint_disruption>=.30
                    assert bool(ok)==d['qualifies']
                    if ok:qualified.append(d['dataset'])
                assert qualified==decision['qualified_datasets'];write(out/folder/'promotion_decision.json',decision)
                if folder+'/expanded' in records:
                    expanded=records[folder+'/expanded']
                    write(out/folder/'expanded/validation_summary.json',dict(complete=expanded['complete'],saved=expanded['saved'],expected=expanded['expected'],
                          seeds_and_trial_membership_verified=True,screening_and_expansion_targets_disjoint=True,
                          selected_cycles_checked_independently=True,by_dataset=expanded['pattern_search_validation']))
            if kind=='transaction' and (src/'promotion_decision.json').exists():
                import pandas as pd
                decision=json.loads((src/'promotion_decision.json').read_text());assert decision['manifest_id']==identity(m)
                paired=pd.read_csv(work/'pilot/paired_effects.csv');qualified=[]
                for d in decision['details']:
                    r=paired[(paired.dataset==d['dataset'])&(paired.comparison=='Matched search / own scenario')&(paired.metric=='joint_disruption')].iloc[0]
                    for metric in ['mean','lo','hi']:assert abs(float(r[metric])-d[metric])<1e-10
                    ok=abs(r['mean'])>=.10 and (r.lo>0 or r.hi<0);assert bool(ok)==d['promising']
                    if ok:qualified.append(d['dataset'])
                assert qualified==decision['qualified_datasets'];write(out/folder/'promotion_decision.json',decision)
            if kind=='subgraphx_fresh':
                validation=json.loads((src/'validation.json').read_text())
                assert validation==dict(passed=True,manifest_id=identity(m),targets=m['targets'][:m['config']['technical_targets']])
                recoveries=[]
                for p in sorted((src/'recoveries').glob('*.json')):
                    recovery=json.loads(p.read_text())
                    assert recovery['frozen_manifest_sha256']==sha(mpath)
                    assert recovery['recovery_wrapper_sha256']==sha(ROOT/folder/'resume_resilient.py')
                    assert recovery['recovery_document_sha256']==sha(ROOT/folder/'RECOVERY.md')
                    assert all(sha(src/'cases'/name)==expected for name,expected in recovery['completed_case_sha256'].items())
                    recoveries.append(dict(recorded_at_perth=recovery['recorded_at_perth'],record_sha256=sha(p),
                                           frozen_manifest_sha256=recovery['frozen_manifest_sha256'],
                                           recovery_wrapper_sha256=recovery['recovery_wrapper_sha256'],
                                           recovery_document_sha256=recovery['recovery_document_sha256'],
                                           preserved_completed_cases=len(recovery['completed_case_sha256']),
                                           retry_policy=recovery['retry_policy']))
                r=records[folder]
                write(out/folder/'validation_summary.json',dict(complete=r['complete'],targets=r['saved'],expected=r['expected'],
                      fresh_seeds_per_target=len(m['config']['fresh_seeds']),source_hashes_verified=checked,
                      technical_targets_checked=len(validation['targets']),native_overlap_rows_recomputed=True,
                      source_explanations_and_fidelity_rows_verified=True,recoveries=recoveries))
            print('CAPTURED',folder,flush=True)
        resolution=records['exploratory_resolution_validation'];assert resolution['complete']
        write(out/'exploratory_resolution_validation/validation_summary.json',dict(complete=True,targets=resolution['saved'],
              source_hashes_verified=resolution['source_hashes_verified'],permutation_comparisons=resolution['permutation_comparisons'],
              maximum_permutation_logit_error=resolution['maximum_permutation_logit_error']))
        record=dict(captured_at_perth=stamp.isoformat(timespec='seconds'),experiments=records,manifest_sha256=config_hashes,
                    report_source='Reports rebuilt from frozen copies of verified case records by the original report functions.',
                    exporter_sha256=sha(Path(__file__)),note='Incomplete cohorts are provisional. Model/data and per-case contents are excluded.')
        write(out/'snapshot.json',record)
        lines=['# Latest results snapshot: '+name,'',f'Capture began **{record["captured_at_perth"]}** (Australia/Perth).','',
               'Reports were rebuilt in an isolated temporary directory from verified copies of saved cases. '
               'Live study outputs were not edited. Source/input hashes, target membership and case identities were checked. '
               'The resolution audit includes all five fresh seeds per target; the selected degree/cycle attacks have independent cycle-check records. '
               'Completed screening promotion decisions agree with recomputed summaries.', '',
               '| Experiment / phase | Saved / planned | Interpretation | Report |','|---|---:|---|---|']
        for key,r in records.items():
            label='Complete' if r['complete'] else 'Provisional; incomplete cohort'
            lines.append(f'| {key} | {r["saved"]}/{r["expected"]} | {label} | [Report]({key}/REPORT.md) |')
        expanded=records.get('exploratory_pattern_constraints/expanded',{})
        pattern_note=('The pattern expansion is complete: 50 separate targets per dataset, two search trials per target and five fresh explainer seeds per trial. '
                      'Seeds and trials are averaged within targets for uncertainty estimates; screening and expansion remain separate.'
                      if expanded.get('complete') else
                      'The pattern expansion remains incomplete. Partial expansion means may average different numbers of completed trials per target and are not confirmatory.')
        hi=records.get('subgraphx_hi_small',{})
        hi_note=(f'HI-Small SubgraphX is complete: {hi["saved"]}/{hi["expected"]} targets in one trial. '
                 'The final report includes native-set overlap and fidelity; between-trial uncertainty is unavailable.'
                 if hi.get('complete') else
                 'HI-Small SubgraphX results remain provisional until the planned cohort finishes.')
        lines+=['',pattern_note+' '
                'Transaction-consistency pilot completeness is determined by its coverage row; its verified promotion decision is published separately. '
                +hi_note, '',
                'The additional resolution cohort excludes the original fresh-seed cohort but was included in the earlier retrospective aggregates. '
                'It supplies new explainer draws and native permutation controls, not an independent dataset or trained-model replication.', '',
                '[Updated contribution register](../../RESEARCH_CONTRIBUTIONS.md) | [Case/input hash manifest](snapshot.json)', '',
                'Raw datasets, checkpoints, per-target records and machine logs remain local. Case hashes identify the exact saved inputs. '
                'Previous publication snapshots are preserved in sibling directories. Later live progress requires another upload.']
        if 'exploratory_subgraphx_fresh_seed' in records:
            lines+=['','The separate HI-Small SubgraphX fresh-seed audit evaluates fixed saved attacks on 100 sampled targets '
                    'with five unseen paired seeds. It measures seed attenuation and residual overlap disruption, '
                    'not a new attack-search trial or an independent trained-model replication. '
                    'Its validation summary verifies the file-lock recovery and unchanged completed cases.']
        (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
        print(json.dumps(dict(snapshot=str(out.relative_to(ROOT)),coverage={k:{a:b for a,b in r.items() if a not in ['case_sha256']} for k,r in records.items()}),indent=2))
    finally:
        resolved=temp.resolve();assert resolved.is_relative_to(ROOT.resolve()) and resolved.name.startswith('_publication_work_')
        shutil.rmtree(resolved)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',choices=['resolution','pattern','transaction','subgraphx','subgraphx_fresh']);p.add_argument('--work',type=Path);a=p.parse_args()
    worker(a.worker,a.work) if a.worker else capture()
