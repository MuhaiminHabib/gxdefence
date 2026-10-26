"""Build a concise report solely from persisted measured results."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
def build():
    lines=['# GXAttack financial study results','',
        'Adapted directed-multigraph GXAttack on frozen GraphSAGE models. See PROTOCOL.md for assumptions and deviations from the reference implementation. No literature review or defence experiment.','']
    for phase in ['pilot','full']:
        folder=ROOT/'results'/phase
        if not (folder/'per_target_metrics.csv').exists():continue
        status=json.loads((folder/'status.json').read_text())
        lines += [f'## {phase.title()}', '',f"Execution status: **{status['state']}**.",'',
            '| Dataset | Method | Completed targets | Trials | PG cosine mean ± trial SD | Target label preserved | Absolute probability change |',
            '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
        all_df=pd.read_csv(folder/'per_target_metrics.csv');df=all_df[(all_df.explainer=='PGExplainer')&(all_df.k==10)]
        for (dataset,method),g in df.groupby(['dataset','attack']):
            t=g.groupby('trial')[['cosine','target_lp','delta_prob']].mean()
            sd=t.cosine.std();sdtext=f'{sd:.4f}' if len(t)>1 else 'not estimable'
            lines.append(f'| {dataset} | {method} | {g.target.nunique()} | {len(t)} | {t.cosine.mean():.4f} ± {sdtext} | {t.target_lp.mean():.1%} | {t.delta_prob.mean():.4f} |')
        lines+=['',f'Per-target evidence: results/{phase}/cases/. All explainer and fidelity metrics: results/{phase}/per_target_metrics.csv; trial means and sample SD: results/{phase}/summary.csv.','']
        lines += ['### Transfer on the same GXAttack graph','',
            '| Dataset | Explainer | Cosine mean ± trial SD | Selected-set Jaccard | Clean necessity → attacked | Clean sufficiency-failure → attacked |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
        transfer=all_df[(all_df.attack=='GXAttack')&(((all_df.explainer!='SubgraphX')&(all_df.k==10))|((all_df.explainer=='SubgraphX')&(all_df.k==0)))]
        cols=['cosine','jaccard','clean_necessity','attacked_necessity','clean_sufficiency_failure','attacked_sufficiency_failure']
        for (dataset,explainer),g in transfer.groupby(['dataset','explainer']):
            t=g.groupby('trial')[cols].mean();a=t.mean();sd=t.cosine.std();sdtext=f'{sd:.4f}' if len(t)>1 else 'not estimable'
            lines.append(f'| {dataset} | {explainer} | {a.cosine:.4f} ± {sdtext} | {a.jaccard:.4f} | {a.clean_necessity:.3f} → {a.attacked_necessity:.3f} | {a.clean_sufficiency_failure:.3f} → {a.attacked_sufficiency_failure:.3f} |')
        lines += ['', 'PG/GNN selected sets use k=10, capped by available edges; SubgraphX uses its full variable-size induced edge set. Cosine is within each explainer, not a calibration comparison across explainers. Fidelity entries here include all attempts; the CSV additionally provides prediction-preserved trial means.','']
    lines+=['## Interpretation limits','',
        '- Pilot targets are validation cases and are excluded from the test study. A pilot is a technical feasibility check.',
        '- Test results are conditional on one classifier checkpoint, correctly detected illicit nodes, and bounded contexts. Eligibility counts are saved in each dataset target file.',
        '- Features are frozen. Synthetic additions are graph-store edits, not validated financial transactions.',
        '- HI-Small account labels are derived from incident laundering transactions. Its new eight-feature classifier is a limited baseline; consult prepared/hi_small_training.csv and the checkpoint metadata.',
        '- SubgraphX has variable-size node coalitions; its induced edge sets are not top-k rankings.',
        '- Lower cosine or overlap demonstrates changed explanations, not human deception or ground-truth explanation error.',
        '- PG clean-repeat controls use another independently fitted network; GNNExplainer and SubgraphX controls rerun the same algorithm with a different seed.',
        '- The repository random-flipping implementation deletes existing edges. This study uses explicit uniform addition/deletion flips and separately matched deletion/addition rewiring; these are adapted controls.',
        '- Early pilot failure logs are retained for provenance; the current status.json determines whether repaired runs passed.', '']
    metrics=ROOT/'prepared/hi_small_model_metrics.json'
    if metrics.exists():
        m=json.loads(metrics.read_text());lines+= [f"HI-Small classifier test F1: {m['test_f1']:.4f}; test average precision: {m['test_ap']:.4f}. These are weak detector results and limit the scope of conclusions.",'']
    (ROOT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
if __name__=='__main__':build()
