"""Exploratory paired clean-repeat contrast; consumes the completed resolution audit."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
DRAWS = 5000
SEED = 89637


def main():
    source = OUT / 'per_case.csv'
    df = pd.read_csv(source)
    join = ['scope', 'dataset', 'target', 'trial', 'selection']
    baseline = df[df.method.eq('Clean repeat')][join + ['row_similarity', 'matched_similarity']]
    assert not baseline.duplicated(join).any()
    attack = df[(~df.method.eq('Clean repeat')) & df.scope.ne('Native SubgraphX control')]
    paired = attack.merge(baseline, on=join, suffixes=('', '_repeat'), validate='many_to_one')
    assert len(paired) == len(attack)
    paired['row_excess_disruption'] = paired.row_similarity_repeat - paired.row_similarity
    paired['matched_excess_disruption'] = paired.matched_similarity_repeat - paired.matched_similarity
    paired['contrast_change'] = paired.matched_excess_disruption - paired.row_excess_disruption
    metrics = ['row_excess_disruption', 'matched_excess_disruption', 'contrast_change']
    keys = ['scope', 'dataset', 'method', 'selection']
    target = paired.groupby(keys + ['target'])[metrics].mean().reset_index()
    target.to_csv(OUT / 'paired_baseline_per_target.csv', index=False)
    rng = np.random.default_rng(SEED)
    results = []
    for key, group in target.groupby(keys):
        values = group[metrics].to_numpy()
        boot = values[rng.integers(0, len(group), (DRAWS, len(group)))].mean(axis=1)
        record = dict(zip(keys, key), targets=len(group))
        for i, metric in enumerate(metrics):
            record.update({metric: float(values[:, i].mean()),
                           metric + '_lo': float(np.quantile(boot[:, i], .025)),
                           metric + '_hi': float(np.quantile(boot[:, i], .975))})
        results.append(record)
    summary = pd.DataFrame(results)
    summary.to_csv(OUT / 'paired_baseline_summary.csv', index=False)
    lines = ['# Paired attack contrast against clean reruns', '',
             'Exploratory follow-up after observing the resolution audit. Each comparison shares the same clean '
             'explanation; the baseline uses an independent clean rerun. For each similarity measure, excess '
             'disruption = clean-to-clean similarity minus clean-to-attacked similarity. Positive values mean '
             'the attack departs further from the clean explanation than an ordinary rerun does on average.', '',
             'Seeds/trials are averaged within targets before 5,000 paired target bootstrap draws. These intervals '
             'omit graph-node dependence and training variation. Matched overlap is the original audit diagnostic, '
             'not semantic accuracy. The larger cohort overlaps the fresh-seed cohort and is not an independent '
             'replication. Fresh seeds were not used for attack selection; the full cohort uses selection seeds.', '',
             '| Scope | Dataset | Method | Selection | Targets | Row excess, 95% interval | Matched excess, 95% interval | Change in contrast, 95% interval |',
             '|---|---|---|---|---:|---|---|---|']
    for r in results:
        cells = [r['scope'], r['dataset'], r['method'], r['selection'], str(r['targets'])]
        cells += [f'{r[m]:.4f} ({r[m + "_lo"]:.4f}, {r[m + "_hi"]:.4f})' for m in metrics]
        lines.append('| ' + ' | '.join(cells) + ' |')
    (OUT / 'PAIRED_BASELINE.md').write_text('\n'.join(lines), encoding='utf8')
    provenance = dict(bootstrap_draws=DRAWS, bootstrap_seed=SEED,
                      input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      paired_rows=len(paired), design='Exploratory after inspecting audit results')
    (OUT / 'paired_baseline_provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf8')
    selected = summary[summary.scope.eq('Fresh seed audit') & summary.selection.eq('top25')]
    print(selected.to_string(index=False))


if __name__ == '__main__':
    main()
