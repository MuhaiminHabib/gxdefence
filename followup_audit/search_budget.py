"""Read-only retrospective analysis of completed AMLSim adaptive traces."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'subgraphx_primary/results/full'
OUT = ROOT / 'results/search_budget'
QS = [1, 5, 10, 20, 40]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    coverage = json.loads((SOURCE / 'coverage.json').read_text())
    assert coverage['complete'] and coverage['saved'] == 498
    rows, first, hashes = [], [], {}
    for p in sorted((SOURCE / 'cases').glob('*.json')):
        raw = p.read_bytes(); d = json.loads(raw)
        hashes[p.name] = hashlib.sha256(raw).hexdigest()
        trace = d['trace']; assert len(trace) == 40
        successes = [i + 1 for i, v in enumerate(trace) if v['preserved'] and v['distance'] >= 1 - 1e-12]
        first.append(dict(target=d['target'], trial=d['trial'], first_success=successes[0] if successes else None, censored=not bool(successes)))
        for q in QS:
            best = max(trace[:q], key=lambda v: (v['preserved'], v['distance']))
            rows.append(dict(target=d['target'], trial=d['trial'], proposals=q,
                             unique_proposals=len({tuple(sorted(v['edits'])) for v in trace[:q]}),
                             similarity=1-best['distance'], label_preserved=int(best['preserved']),
                             zero_similarity_success=int(best['preserved'] and best['distance'] >= 1-1e-12)))
        final = d['attacks']['SubgraphX-targeted search']
        assert abs((1-final['distance'])-rows[-1]['similarity']) < 1e-12
    frame = pd.DataFrame(rows)
    assert len(first) == 498 and frame.target.nunique() == 166
    frame.to_csv(OUT/'per_case.csv', index=False)
    pd.DataFrame(first).to_csv(OUT/'first_success.csv', index=False)
    rng = np.random.default_rng(731); summaries=[]
    for q, g in frame.groupby('proposals'):
        per_target = g.groupby('target')[['similarity','label_preserved','zero_similarity_success','unique_proposals']].mean()
        a=per_target.to_numpy(); draws=rng.integers(0,len(a),(10000,len(a))); boot=a[draws].mean(axis=1)
        r=dict(proposals=q,targets=len(a),source_trials=3)
        for i, name in enumerate(per_target.columns):
            r[name]=float(a[:,i].mean());r[name+'_lo']=float(np.quantile(boot[:,i],.025));r[name+'_hi']=float(np.quantile(boot[:,i],.975))
        summaries.append(r)
    summary=pd.DataFrame(summaries);summary.to_csv(OUT/'summary.csv',index=False)
    histogram=pd.DataFrame(first).assign(first_success=lambda f:f.first_success.fillna(41)).groupby('first_success').size().reset_index(name='case_count')
    histogram.to_csv(OUT/'first_success_distribution.csv',index=False)
    (OUT/'provenance.json').write_text(json.dumps(dict(source_hashes=hashes,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bootstrap_seed=731,bootstrap_draws=10000,interval='Percentile target-cluster resampling, conditional on graphs/models; graph-node dependence not modeled'),indent=2))
    plt.style.use('seaborn-v0_8-whitegrid')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,metric,label in [(axes[0],'similarity','Native-set cosine similarity'),(axes[1],'zero_similarity_success','Label-preserved zero-similarity fraction')]:
        ax.plot(summary.proposals,summary[metric],marker='o',color='#2463a6')
        ax.fill_between(summary.proposals,summary[metric+'_lo'],summary[metric+'_hi'],alpha=.2,color='#2463a6')
        ax.set(xlabel='Adaptive proposals available',ylabel=label,xticks=QS,ylim=(0,1))
    fig.suptitle('AMLSim SubgraphX: retrospective search-budget analysis')
    fig.tight_layout();fig.savefig(OUT/'search_budget.png',dpi=180);plt.close(fig)
    lines=['# AMLSim SubgraphX search-budget analysis','', '**COMPLETE: 166 targets, three source trials, 498 saved attack trajectories.**', '',
           'Retrospective prefixes of the same adaptive searches; the final result matches saved selected attacks. Intervals resample targets with their three trials together. These are conditional descriptive intervals; graph dependence and classifier-training uncertainty are not modeled.', '',
           '| Proposals | Similarity (95% interval) | Label-preserved zero similarity (95% interval) | Mean unique proposals |',
           '|---:|---:|---:|---:|']
    for r in summaries:
        lines.append(f"| {r['proposals']} | {r['similarity']:.4f} ({r['similarity_lo']:.4f}, {r['similarity_hi']:.4f}) | {100*r['zero_similarity_success']:.2f}% ({100*r['zero_similarity_success_lo']:.2f}, {100*r['zero_similarity_success_hi']:.2f}) | {r['unique_proposals']:.2f} |")
    lines += ['', 'All selected prefix candidates preserve labels in these cases. First-success data retain failures as censored, not as success at proposal 40. Unique proposal counts cover the adaptive trace only, excluding clean explanations and other methods. A zero set cosine can include an empty explanation and does not establish incorrectness. Random-search prefix scores were not saved; this curve cannot show adaptive superiority. The ongoing HI-Small experiment is excluded.', '', '![Search budget](search_budget.png)']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(summary[['proposals','similarity','zero_similarity_success']].to_string(index=False),flush=True)

if __name__=='__main__':main()
