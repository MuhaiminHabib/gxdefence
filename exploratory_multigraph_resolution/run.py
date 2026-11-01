"""Read saved masks and verify conditional parallel-row equivalence on CPU."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import sys, json, math, random, hashlib, time
from pathlib import Path
from collections import Counter, defaultdict
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import torch
ROOT = Path(__file__).resolve().parent; STUDY = ROOT.parent; OUT = ROOT/'results'
sys.path.insert(0,str(STUDY/'framework'))
from src.models.marasi_models import MarasiGraphSAGE
torch.set_num_threads(1)
CONFIG = dict(bootstrap_draws=5000, bootstrap_seed=58231, null_seed=27183,
              selections=['top25','top10'], validation_atol=3e-5, validation_rtol=3e-5)
inputs = {}; rows = []; checks = []

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for part in iter(lambda:f.read(1024**2),b''):h.update(part)
    return h.hexdigest()

def read(path):
    raw=path.read_bytes(); inputs[str(path.relative_to(STUDY))]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)

def select(scores, selection):
    k=len(scores) if selection=='native' else (math.ceil(len(scores)/4) if selection=='top25' else 10)
    return set(sorted(scores,key=lambda v:(-scores[v],v))[:k])

def measure(a,b,selection,endpoint,shared_only=True):
    aa,bb=select(a,selection),select(b,selection); den=math.sqrt(len(aa)*len(bb))
    if not den:
        base=float(not aa and not bb)
        return dict(row_similarity=base,matched_similarity=base,gap=0.,clean_size=len(aa),attacked_size=len(bb))
    common={v for v in set(a)&set(b) if v.startswith('E')} if shared_only else set(a)|set(b)
    ca,cb=Counter(endpoint(v) for v in aa&common),Counter(endpoint(v) for v in bb&common)
    # Shared added IDs are absent from clean graphs; original exact intersections
    # are included even for hypothetical non-original same-ID comparisons.
    unmatched_exact=len((aa&bb)-common)
    actual=len(aa&bb)/den
    matched=(sum(min(v,cb[k]) for k,v in ca.items())+unmatched_exact)/den
    assert actual-1e-10<=matched<=1+1e-10
    return dict(row_similarity=actual,matched_similarity=matched,gap=matched-actual,
                clean_size=len(aa),attacked_size=len(bb))

def append(scope,name,target,trial,method,a,b,endpoint,native=False):
    for selection in (['native'] if native else CONFIG['selections']):
        rows.append(dict(scope=scope,dataset=name,target=target,trial=trial,method=method,selection=selection,
                         **measure(a,b,selection,endpoint,shared_only=not native)))

@torch.no_grad()
def verify(d,model,data,endpoint):
    g=d['graph_details']['Clean']; nodes=g['global_nodes']; ids=g['ids']
    ix=torch.tensor([int(v[1:]) for v in ids]); global_edges=data.edge_index[:,ix]
    lookup={v:i for i,v in enumerate(nodes)}
    edge=torch.tensor([[lookup[int(v)] for v in side] for side in global_edges],dtype=torch.long)
    x=data.x[nodes]; target=lookup[d['target']]
    groups=defaultdict(list)
    for key in ids:groups[endpoint(key)].append(key)
    rng=random.Random(CONFIG['null_seed']+d['target'])
    for seed,ev in d['explanations'].items():
        if seed=='2026':continue
        chosen=select(ev['scores']['Clean'],'top25'); alternative=set()
        for pair, members in groups.items():
            count=len(chosen&set(members))
            ordered=sorted(set(members)-chosen)+sorted(set(members)&chosen)
            alternative.update(ordered[:count])
        assert len(chosen)==len(alternative)
        assert Counter(endpoint(v) for v in chosen)==Counter(endpoint(v) for v in alternative)
        arbitrary=set(rng.sample(ids,len(chosen)))
        outputs={}; max_error=0.; random_error=0.
        for mode in ('remove','retain'):
            for label,selected in [('original',chosen),('equivalent',alternative),('random',arbitrary)]:
                keep=torch.tensor([(v in selected)==(mode=='retain') for v in ids])
                outputs[mode+'_'+label]=model(x,edge[:,keep])[target]
            original=outputs[mode+'_original']; changed=outputs[mode+'_equivalent']
            torch.testing.assert_close(original,changed,atol=CONFIG['validation_atol'],rtol=CONFIG['validation_rtol'])
            max_error=max(max_error,float((original-changed).abs().max()))
            random_error=max(random_error,float((original-outputs[mode+'_random']).abs().max()))
        checks.append(dict(dataset=d['dataset'],target=d['target'],seed=int(seed),selected_size=len(chosen),
                           row_similarity=len(chosen&alternative)/len(chosen) if chosen else 1.,
                           changed=int(chosen!=alternative),max_logit_error=max_error,
                           random_max_logit_error=random_error,original_ids=sorted(chosen),
                           equivalent_ids=sorted(alternative),random_ids=sorted(arbitrary),
                           logits={k:v.tolist() for k,v in outputs.items()}))

def main():
    OUT.mkdir(parents=True,exist_ok=True); start=time.time()
    source_hashes={str(p.relative_to(STUDY)):sha(p) for p in [Path(__file__),ROOT/'README.md',STUDY/'framework/src/models/marasi_models.py']}
    for name in ['amlsim','hi_small']:
        cp=STUDY/f'complete_graphs/prepared/{name}.pt'; inputs[str(cp.relative_to(STUDY))]=sha(cp)
        bundle=torch.load(cp,map_location='cpu',weights_only=False); data=bundle['data']; edges=data.edge_index.numpy()
        model=MarasiGraphSAGE(data.num_features,bundle['hidden']); model.load_state_dict(bundle['state']); model.eval()
        for p in model.parameters():p.requires_grad_(False)
        cache={}
        def endpoint(key):
            if key not in cache:
                cache[key]=tuple(int(v) for v in edges[:,int(key[1:])]) if key[0]=='E' else tuple(map(int,key[1:].split(':')))
            return cache[key]
        for p in sorted((STUDY/'followup_audit/results/gnn_audit/cases').glob(name+'_*.json')):
            d=read(p)
            for seed,ev in d['explanations'].items():
                if seed=='2026':continue
                clean=ev['scores']['Clean']
                for method,scores in ev['scores'].items():
                    if method!='Clean':append('Fresh seed audit',name,d['target'],int(seed),method,clean,scores,endpoint)
                append('Fresh seed audit',name,d['target'],int(seed),'Clean repeat',clean,ev['clean_repeat_scores'],endpoint)
            verify(d,model,data,endpoint)
        print('VERIFIED',name,'fresh audit',flush=True)
        for p in sorted((STUDY/'gnn_three_trials/results/full/cases').glob(name+'_*.json')):
            d=read(p); clean=d['clean']['GNNExplainer']
            for method,attack in d['attacks'].items():
                append('Full three-trial GNN',name,d['target'],d['trial'],method,clean,attack['scores'],endpoint)
            append('Full three-trial GNN',name,d['target'],d['trial'],'Clean repeat',clean,d['clean_repeat']['GNNExplainer'],endpoint)
        if name=='amlsim':
            for p in sorted((STUDY/'subgraphx_primary/results/full/cases').glob(name+'_*.json')):
                d=read(p); clean=d['clean']['SubgraphX']
                for method,attack in d['attacks'].items():
                    append('Native SubgraphX control',name,d['target'],d['trial'],method,clean,attack['scores'],endpoint,native=True)
        for k,v in bundle['state'].items():torch.testing.assert_close(model.state_dict()[k],v,atol=0,rtol=0)
        del model,data,bundle; print('ANALYZED',name,flush=True)
    df=pd.DataFrame(rows); df.to_csv(OUT/'per_case.csv',index=False)
    keys=['scope','dataset','target','method','selection']
    target=df.groupby(keys)[['row_similarity','matched_similarity','gap']].mean().reset_index()
    target.to_csv(OUT/'per_target.csv',index=False)
    rng=np.random.default_rng(CONFIG['bootstrap_seed']); summary=[]
    for key,g in target.groupby(['scope','dataset','method','selection']):
        a=g.gap.to_numpy(); boot=a[rng.integers(0,len(a),(CONFIG['bootstrap_draws'],len(a)))].mean(1)
        summary.append(dict(zip(['scope','dataset','method','selection'],key),targets=len(a),
                            row_similarity=float(g.row_similarity.mean()),matched_similarity=float(g.matched_similarity.mean()),
                            gap=float(a.mean()),gap_lo=float(np.quantile(boot,.025)),gap_hi=float(np.quantile(boot,.975))))
    pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
    (OUT/'equivalence_checks.json').write_text(json.dumps(checks,indent=2,allow_nan=False),encoding='utf8')
    check_summary=[]
    for name in ['amlsim','hi_small']:
        vals=[c for c in checks if c['dataset']==name]
        check_summary.append(dict(dataset=name,comparisons=len(vals),changed_sets=sum(c['changed'] for c in vals),
                                  mean_row_similarity=float(np.mean([c['row_similarity'] for c in vals])),
                                  max_logit_error=max(c['max_logit_error'] for c in vals),
                                  random_median_logit_error=float(np.median([c['random_max_logit_error'] for c in vals]))))
    provenance=dict(config=CONFIG,sources=source_hashes,inputs=inputs,torch=torch.__version__,seconds=time.time()-start,
                    analysis='Exploratory retrospective extension; initial 100-target results were inspected before script creation',
                    cases=len(df),equivalence_summary=check_summary)
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
    lines=['# Multigraph explanation-resolution audit','', '**COMPLETE. Separate exploratory retrospective analysis.**','',
           'This is a representation-equivalence diagnostic, not a new attack or a corrected success rate. '
           'Matching can only increase overlap by construction. For GNN masks it uses original rows available in both '
           'input pools and retains the original selected-cardinality denominator. Features remain frozen.', '',
           '| Scope | Dataset | Method | Selection | Targets | Row overlap | Matched overlap | Gap, 95% target interval |',
           '|---|---|---|---|---:|---:|---:|---|']
    for r in summary:
        lines.append(f'| {r["scope"]} | {r["dataset"]} | {r["method"]} | {r["selection"]} | {r["targets"]} | '
                     f'{r["row_similarity"]:.4f} | {r["matched_similarity"]:.4f} | {r["gap"]:.4f} '
                     f'({r["gap_lo"]:.4f}, {r["gap_hi"]:.4f}) |')
    lines+=['','## Mechanical zero-transaction-edit controls','',
            '| Dataset | Compared sets | Sets with changed row IDs | Mean row overlap | Maximum logit difference |',
            '|---|---:|---:|---:|---:|']
    for r in check_summary:
        lines.append(f'| {r["dataset"]} | {r["comparisons"]} | {r["changed_sets"]} | {r["mean_row_similarity"]:.4f} | {r["max_logit_error"]:.3g} |')
    lines+=['','Equivalent sets are constructed alternatives to saved clean top-25% explanations, not independent '
            'outputs from an explainer. They preserve the number of selected rows at each ordered endpoint pair; '
            'removal and retention logits both pass numerical parity. Node features stay fixed. Actual transaction '
            'amounts/times need not be equivalent; re-extracting their account aggregates can break the property.', '',
            'Native SubgraphX retains whole induced edge groups. Its permissive pair-count bound is a negative control. '
            'The full three-trial cohort overlaps the preliminary fresh-seed cohort, so it is not independent confirmation. '
            'Intervals average seeds/trials within targets and omit graph-node dependence and model-training variation.', '',
            'Symmetry-aware explanation reporting is prior work: Crabbé and van der Schaar (NeurIPS 2023), '
            'https://arxiv.org/abs/2304.06715; Xu et al. (2026 preprint), https://arxiv.org/abs/2607.26344. '
            'The candidate contribution is its measured relevance to financial multigraph attack evaluation.']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps(dict(seconds=provenance['seconds'],checks=check_summary),indent=2),flush=True)

if __name__=='__main__':main()
