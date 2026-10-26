import csv
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'outputs' / ('baseline_check_' + dt.datetime.now().strftime('%Y%m%d_%H%M%S'))
REFERENCE = {
    ('Elliptic', 'gcn'): (30266, 6985, 9313, .6080, .0119),
    ('Elliptic', 'gat'): (30266, 6985, 9313, .7690, .0115),
    ('Elliptic', 'graphsage'): (30266, 6985, 9313, .8762, .0075),
    ('Elliptic', 'chebnet'): (30266, 6985, 9313, .8974, .0053),
    ('Elliptic', 'gatv2'): (30266, 6985, 9313, .8688, .0048),
    ('IBM AMLSim', 'gcn'): (6500, 1500, 2000, .3688, .0201),
    ('IBM AMLSim', 'graphsage'): (6500, 1500, 2000, .9051, .0139),
    ('IBM AMLSim', 'gatv2'): (6500, 1500, 2000, .7545, .0647),
}

def status(state, **extra):
    record = dict(state=state, updated=dt.datetime.now().isoformat(), run_dir=str(RUN), **extra)
    temporary = RUN / 'status.tmp'
    temporary.write_text(json.dumps(record, indent=2), encoding='utf-8')
    temporary.replace(RUN / 'status.json')
    print(json.dumps(record), flush=True)

def main():
    RUN.mkdir(parents=True, exist_ok=False)
    # Keep the copied training source unchanged; set only the destination for this run.
    ibm_dir = RUN / 'ibm_amlsim'
    ibm_dir.mkdir()
    prefix = RUN.name
    jobs = [
        ('IBM AMLSim', [sys.executable, '-u', '-B', '-c',
          "import runpy,pathlib; p=pathlib.Path(" + repr(str(ROOT / 'scripts' / 'run_ibm_amlsim_prev_reproduction.py')) +
          "); ns=runpy.run_path(str(p),run_name='baseline_import'); ns['main'].__globals__['OUTPUT_DIR']=pathlib.Path(" + repr(str(ibm_dir)) + "); ns['main']()"]),
        ('Elliptic', [sys.executable, '-u', '-B', str(ROOT / 'scripts' / 'run_marasi_5seed.py'), '--device', 'cuda', '--output-prefix', prefix]),
    ]
    failures = []
    for dataset, command in jobs:
        log = RUN / (dataset.replace(' ', '_').lower() + '.log')
        status('running', dataset=dataset, log=str(log))
        with log.open('w', encoding='utf-8') as output:
            result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            failures.append(dict(dataset=dataset, exit_code=result.returncode, log=str(log)))
    rows = []
    sources = [
        ('IBM AMLSim', ibm_dir / 'ibm_amlsim_prev_reproduction_summary.csv', 'test_fraud_f1_mean', 'test_fraud_f1_std'),
        ('Elliptic', ROOT / 'outputs' / 'results' / (prefix + '_summary.csv'), 'f1_mean', 'f1_std'),
    ]
    for dataset, source, mean_key, std_key in sources:
        if not source.exists():
            continue
        with source.open(newline='', encoding='utf-8') as f:
            for actual in csv.DictReader(f):
                model = actual['model'].lower()
                train, val, test, mean, std = REFERENCE[(dataset, model)]
                got_mean, got_std = float(actual[mean_key]), float(actual[std_key])
                counts = tuple(int(actual[k]) for k in ('train_samples', 'val_samples', 'test_samples'))
                rows.append(dict(dataset=dataset, model=actual['model'], runs=int(actual['runs']),
                    train_samples=counts[0], validation_samples=counts[1], test_samples=counts[2],
                    split_matches=counts == (train, val, test), reference_f1_mean=mean,
                    reference_f1_std=std, actual_f1_mean=got_mean, actual_f1_std=got_std,
                    mean_difference=got_mean-mean,
                    matches_at_four_decimals=(f'{got_mean:.4f}' == f'{mean:.4f}' and f'{got_std:.4f}' == f'{std:.4f}')))
    if rows:
        with (RUN / 'comparison.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        lines = ['# Baseline comparison', '', 'Reference values are historical five-seed illicit/fraud-class F1 scores. Exact match means both mean and sample standard deviation agree at four decimal places; this is not a statistical equivalence test.', '',
                 '| Dataset | Model | Runs | Split matches | Reference F1 | New F1 | Mean difference | Exact match |',
                 '| --- | --- | ---: | --- | --- | --- | ---: | --- |']
        for r in rows:
            lines.append(f"| {r['dataset']} | {r['model']} | {r['runs']} | {r['split_matches']} | {r['reference_f1_mean']:.4f} ± {r['reference_f1_std']:.4f} | {r['actual_f1_mean']:.4f} ± {r['actual_f1_std']:.4f} | {r['mean_difference']:+.4f} | {r['matches_at_four_decimals']} |")
        (RUN / 'COMPARISON.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    status('failed' if failures or len(rows) != 8 else 'complete', failures=failures, compared_models=len(rows), report=str(RUN / 'COMPARISON.md'))

if __name__ == '__main__':
    try:
        main()
    except Exception:
        if RUN.exists():
            status('failed', error=traceback.format_exc())
        raise
