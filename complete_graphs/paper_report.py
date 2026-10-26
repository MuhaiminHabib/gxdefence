"""Paper-layout tables with explicit adapted metric labels."""
from pathlib import Path
import json
import pandas as pd
from supplementary_table import table_lines
ROOT=Path(__file__).resolve().parent
NAMES=['elliptic','amlsim','hi_small']
def build():
    lines=['# Complete-graph GXAttack study','','All supplied raw graph records; all eligible illicit test targets, five trials. Pilot uses separate validation targets. Layout follows Tables II and III of the supplied v2 paper.','']
    for phase in ['pilot','full']:
        folder=ROOT/'results'/phase
        if not (folder/'trial_means.csv').exists():continue
        status=json.loads((folder/'status.json').read_text());d=pd.read_csv(folder/'trial_means.csv')
        lines += [f'## {phase.title()} — {status["state"]}','','| Dataset | Correctly detected illicit candidates | Eligible | Selected | Trials |','|---|---:|---:|---:|---:|']
        for n in NAMES:
            path=folder/f'{n}_targets.json'
            if path.exists():
                t=json.loads(path.read_text());lines.append(f'| {n} | {t["correct_illicit"]} | {t["eligible"]} | {len(t["selected"])} | {2 if phase=="pilot" else 5} |')
        lines += ['', '### Table II — adapted attack results','','GEA requires independent ground-truth explanations and is unavailable. Sim_cos uses binary top25% edge-row masks (ceil rounding); directed multigraph conventions remain an adaptation. Values are mean ± sample SD across trial means. DeltaLabel and DeltaProb are fractions.','','| Method | Metric | Elliptic | AMLSim | HI-Small 100% |','|---|---|---:|---:|---:|','| Clean | O. GEA | — | — | — |']
        def group(n,attack,ex='PGExplainer'):
            return d[(d.dataset==n)&(d.attack==attack)&(d.explainer==ex)&(d.k==(0 if ex=='SubgraphX' else 10))]
        def value(g,col):
            if g.empty or col is None:return '—'
            v=g[col].dropna()
            if v.empty:return '—'
            return f'{v.mean():.4f} ± {v.std():.4f}' if len(v)>1 else f'{v.mean():.4f} (one trial so far)'
        for attack in ['GXAttack','Random flipping','Random rewiring']:
            for metric,col in [('P. GEA ↓',None),('Delta GEA ↑',None),('Sim_cos binary25% ↓','binary_top25_cosine'),('#Pert. ↓','perturbations'),('DeltaLabel ↓','delta_label'),('DeltaProb ↓','delta_prob')]:
                lines.append('| '+attack+' | '+metric+' | '+' | '.join(value(group(n,attack),col) for n in NAMES)+' |')
        lines += ['', '### Table III — adapted clean → attacked fidelity summary','','Explainer rows and dataset columns follow the paper. Entries are equal-weight harmonic fidelity summaries, NOT GEA; five-trial averages rather than typical-run GEA. PG/GNN use top10 capped by available edges; SubgraphX uses its whole native induced set.','','| Explainer | Elliptic | AMLSim | HI-Small 100% |','|---|---:|---:|---:|']
        for ex in ['PGExplainer','GNNExplainer','SubgraphX']:
            vals=[]
            for n in NAMES:
                g=group(n,'GXAttack',ex)
                vals.append('—' if g.empty else f'{g.clean_harmonic_fidelity.mean():.4f} → {g.attacked_harmonic_fidelity.mean():.4f}')
            lines.append('| '+ex+' | '+' | '.join(vals)+' |')
        lines += ['', '### Supplement: transferred similarity and clean-repeat controls','','Continuous cosine for PG/GNN and native binary cosine for SubgraphX. Within-explainer comparisons only.','','| Explainer | Comparison | Elliptic | AMLSim | HI-Small 100% |','|---|---|---:|---:|---:|']
        for ex in ['PGExplainer','GNNExplainer','SubgraphX']:
            for attack in ['Clean repeat','GXAttack']:
                lines.append('| '+ex+' | '+attack+' | '+' | '.join(value(group(n,attack,ex),'cosine') for n in NAMES)+' |')
        lines += ['', 'Additional metrics below reflect only the cases currently saved for this phase; treat them as provisional until phase completion.', '']
        lines += table_lines(d, hi_label='HI-Small 100%')
        lines += ['',f'All metrics: results/{phase}/per_target_metrics.csv. Mean/SD: results/{phase}/summary.csv. Case evidence: results/{phase}/cases/.','']
    lines += ['## Model performance and interpretation','','| Dataset | Test F1 | Test average precision |','|---|---:|---:|']
    for n in ['elliptic','hi_small']:
        p=ROOT/f'prepared/{n}_model_metrics.json'
        if p.exists():
            m=json.loads(p.read_text());lines.append(f'| {n} | {m["test_f1"]:.4f} | {m["test_ap"]:.4f} |')
    lines += ['', 'AMLSim retains its existing complete-graph checkpoint. HI-Small uses an incident-laundering account-label proxy and eight aggregate features; weak detector performance, if present, limits conclusions.', '',
        'Eligibility excludes unknown labels, incorrect predictions and contexts outside registered bounds. Graph data are complete, but this is not an attack on every node. Features stay fixed; additions are graph-store edits, not validated financial transactions.', '',
        'GXAttack selects among40 discretizations; random controls use one draw. Edit budgets match, search effort does not. Six edits need not be small relative to a tiny context. Similarity changes do not prove explanation incorrectness or human deception. No defence experiment or literature review is included.']
    (ROOT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
if __name__=='__main__':build()
