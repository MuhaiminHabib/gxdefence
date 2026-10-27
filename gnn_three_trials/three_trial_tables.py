"""Tables II-IV; aggregate within each trial before taking mean/sample SD."""
import json
from pathlib import Path
import pandas as pd

NAMES={'amlsim':'AMLSim','hi_small':'HI-Small'}
METHODS=['GNN-targeted GX adaptation','Random flipping','Random rewiring','Random search']
def build(folder):
    folder=Path(folder)
    d=pd.read_csv(folder/'per_target.csv')
    base=folder.parents[2]
    targets={n:set(json.loads((base/f'complete_graphs/results/full/{n}_targets.json').read_text())['selected']) for n in NAMES}
    unique=d[['dataset','target','trial']].drop_duplicates()
    assert not d.duplicated(['dataset','target','trial','method','explainer','selection']).any()
    completed=set()
    for name, ids in targets.items():
        for trial in [2026,2027,2028]:
            observed=set(unique[(unique.dataset==name)&(unique.trial==trial)].target)
            assert observed<=ids
            if observed==ids:completed.add((name,trial))
    complete=len(completed)==6
    lines=['# GNNExplainer-primary: three-trial report','',
           '**COMPLETE**' if complete else '**IN PROGRESS — final tables are withheld until all three trials finish for both datasets.**','',
           '| Dataset | Eligible illicit test targets | Planned trials | Saved evaluations | Expected evaluations |',
           '|---|---:|---:|---:|---:|']
    for name,ids in targets.items():
        lines.append(f'| {NAMES[name]} | {len(ids)} | 3 | {int((unique.dataset==name).sum())} | {len(ids)*3} |')
    lines+=['| Total | 961 | 3 | '+str(len(unique))+' | 2883 |','',
      'All previously eligible targets on the complete graphs; Elliptic excluded. Six directed edge edits, frozen features and classifiers. Trial seeds 2026, 2027 and 2028. This is a GNNExplainer-targeted GXAttack-objective adaptation, not an exact reproduction of the original PGExplainer attack.','',
      'Eligibility: correctly classified illicit test nodes, incoming two-hop neighbourhood of 4–100 nodes and 5–2000 edge rows, at least three removable non-self edges and three absent ordered pairs. These are our registered limits.','']
    if not complete:
        lines+=['Completed dataset-trials: '+(', '.join(f'{NAMES[n]} / {t}' for n,t in sorted(completed)) or 'none')+'.',
                'Saved per-target and trial-means CSVs are provisional and may contain incomplete trials. No partial average is presented as a final result.']
    else:
        t=d.groupby(['dataset','method','explainer','selection','trial']).mean(numeric_only=True).reset_index()
        def values(name,method,metric,ex='GNNExplainer',selection='top10'):
            g=t[(t.dataset==name)&(t.method==method)&(t.explainer==ex)&(t.selection==selection)]
            assert len(g)==3
            return g[metric]
        def fmt(v):return f'{v.mean():.4f} ± {v.std(ddof=1):.4f}'
        lines+=['## Table II — Attack results','',
                '| Method | Metric | AMLSim | HI-Small |','|---|---|---:|---:|']
        for method in METHODS:
            for metric,label in [('binary_top25_cosine','Cosine similarity ↓'),(None,'Edge edits'),('delta_label','ΔLabel ↓'),('delta_prob','ΔProb ↓')]:
                cells=['6' if metric is None else fmt(values(n,method,metric)) for n in NAMES]
                lines.append('| '+method+' | '+label+' | '+' | '.join(cells)+' |')
        lines+=['','Mean ± sample standard deviation across three trial means. Similarity uses binary top-25% edge selections; lower means more explanation change. ΔLabel is the fraction of changed predictions. ΔProb is the average absolute change in probability for the original class. Fractions and probability differences are not percentages.','',
                '## Table III — Explanation fidelity before → after GXAttack','',
                '| Explainer | AMLSim | HI-Small |','|---|---:|---:|']
        for ex in ['GNNExplainer','PGExplainer','SubgraphX']:
            cells=[]
            for n in NAMES:
                halves=[]
                for prefix in ['clean','attacked']:
                    a=values(n,METHODS[0],prefix+'_hard_plus',ex,'native' if ex=='SubgraphX' else 'top10')
                    b=1-values(n,METHODS[0],prefix+'_hard_minus',ex,'native' if ex=='SubgraphX' else 'top10')
                    h=(2*a*b/(a+b)).fillna(0)
                    halves.append(fmt(h))
                cells.append(' → '.join(halves))
            lines.append('| '+ex+' | '+' | '.join(cells)+' |')
        lines+=['','This is our harmonic summary of Fidelity+ and (1 − Fidelity−), computed within each trial before averaging. It is not ground-truth explanation accuracy (GEA), and is not a direct harmonic mean of Fidelity+ and Fidelity−. PG/GNN use top-10 edges; SubgraphX uses its native set.','',
                '## Table IV — Additional GNNExplainer results','',
                '| Dataset | Metric | Clean | GX adaptation | Random flipping | Random rewiring | Random search |',
                '|---|---|---:|---:|---:|---:|---:|']
        for n in NAMES:
            for key,label in [('jaccard','Jaccard@10 ↓'),('hard_plus','Fidelity+ ↑'),('hard_minus','Fidelity− ↓'),('soft_plus','Soft Fidelity+'),('soft_minus','Soft Fidelity−')]:
                clean='1.0000 (self-reference)' if key=='jaccard' else fmt(values(n,METHODS[0],'clean_'+key))
                cells=[fmt(values(n,m,key if key=='jaccard' else 'attacked_'+key)) for m in METHODS]
                lines.append('| '+NAMES[n]+' | '+label+' | '+clean+' | '+' | '.join(cells)+' |')
        lines+=['','Fidelity+: how often removing the selected edges changes the label. Fidelity−: how often keeping only those edges changes the label. Soft versions measure the signed drop in class probability under the same removal/retention tests. Negative means confidence increased. Lower overlap alone does not demonstrate poorer fidelity or investigator deception.','',
                '## Clean-repeat controls and prediction preservation','',
                '| Dataset | Repeat binary top25 similarity | Repeat Jaccard@10 | GX label changes / evaluations |',
                '|---|---:|---:|---:|']
        for n in NAMES:
            changed=d[(d.dataset==n)&(d.method==METHODS[0])&(d.explainer=='GNNExplainer')&(d.selection=='top10')].delta_label.sum()
            lines.append(f'| {NAMES[n]} | {fmt(values(n,"Clean repeat","binary_top25_cosine"))} | {fmt(values(n,"Clean repeat","jaccard"))} | {int(changed)} / {len(targets[n])*3} |')
        lines+=['','Clean repeat reruns the explainer with a different seed on the unchanged graph. Random search selects among 40 candidates, matching native candidate-evaluation count but not gradient computation. No defence evaluation is included.']
    dest=folder/'TABLES_PAPER_LAYOUT.md'
    temp=dest.with_suffix('.tmp');temp.write_text('\n'.join(lines)+'\n',encoding='utf8');temp.replace(dest)
    (folder/'coverage.json').write_text(json.dumps(dict(complete=complete,saved=len(unique),expected=2883,completed_dataset_trials=sorted(completed)),indent=2))

if __name__=='__main__':
    build(Path(__file__).resolve().parent/'results/full')
