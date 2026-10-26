"""Additional measured metrics, with unavailable metrics explicitly marked."""
from pathlib import Path
import pandas as pd

def table_lines(d, hi_label='HI-Small 50%'):
    lines = ['## Table IV — Additional explanation metrics', '',
        'PGExplainer; mean ± sample SD across available trial means. Completed initial study uses five trials. Fidelity uses top-10 edges, capped by available edges. Clean overlap with itself is 1 by definition; independent clean-repeat controls appear below.', '']
    def fmt(g, col):
        v = g[col].dropna()
        if v.empty: return '—'
        return f'{v.mean():.4f} ± {v.std():.4f}' if len(v)>1 else f'{v.mean():.4f} (one trial)'
    for name, label in [('elliptic','Elliptic'),('amlsim','AMLSim'),('hi_small',hi_label)]:
        p = d[(d.dataset==name)&(d.explainer=='PGExplainer')]
        if p.empty: continue
        lines += [f'### {label}', '', '| Metric | Clean | GXAttack | Random flipping | Random rewiring |', '|---|---:|---:|---:|---:|']
        for k in [5,10,20]:
            vals=[fmt(p[(p.attack==a)&(p.k==k)],'jaccard') for a in ['GXAttack','Random flipping','Random rewiring']]
            lines.append(f'| Top-{k} Jaccard ↓ | 1.0000 (reference) | '+' | '.join(vals)+' |')
        for label, clean, attacked in [
            ('Fidelity+ / necessity ↑','clean_necessity','attacked_necessity'),
            ('Fidelity− / sufficiency failure ↓','clean_sufficiency_failure','attacked_sufficiency_failure'),
            ('Harmonic fidelity summary ↑','clean_harmonic_fidelity','attacked_harmonic_fidelity')]:
            vals=[fmt(p[(p.attack=='GXAttack')&(p.k==10)],clean)]
            vals += [fmt(p[(p.attack==a)&(p.k==10)],attacked) for a in ['GXAttack','Random flipping','Random rewiring']]
            lines.append('| '+label+' | '+' | '.join(vals)+' |')
        for metric in ['RBO (not computed)','Recall / NDCG (no independent relevance labels)']:
            lines.append('| '+metric+' | — | — | — | — |')
        repeat=p[(p.attack=='Clean repeat')&(p.k==10)]
        lines += ['', 'Independent clean-repeat Jaccard@10: **'+fmt(repeat,'jaccard')+'**.', '']
    lines += ['Fidelity+ is the fraction of targets whose predicted class changes when selected edges are removed. Fidelity− is the fraction whose class changes when only selected edges are retained. The harmonic summary is 2 × Fidelity+ × (1 − Fidelity−) / (Fidelity+ + 1 − Fidelity−), computed within each trial before averaging; it is an adapted characterization summary, not ground-truth explanation accuracy.', '',
        'Arrows indicate metric direction: lower Jaccard means greater explanation disruption; higher necessity and lower sufficiency failure indicate stronger explanatory fidelity. Compare attack overlap with clean-repeat overlap before attributing changes to the attack. Missing metrics are not zero.', '']
    return lines

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    d=pd.read_csv(root/'results/full/trial_means.csv')
    intro=['# Supplementary results — completed initial study', '', 'Known-label Elliptic graph; full AMLSim; random 50% of HI-Small transaction rows. These are the completed initial results, not the ongoing complete-graph expansion.', '']
    (root/'SUPPLEMENTARY_TABLE.md').write_text('\n'.join(intro+table_lines(d)),encoding='utf8')
