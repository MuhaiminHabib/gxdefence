"""Read-only capture of live outputs into a new, dated publication directory."""
import argparse,csv,hashlib,io,json,time
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(b):return hashlib.sha256(b).hexdigest()
def stable(paths):
    for _ in range(10):
        first={str(p):p.read_bytes() for p in paths}
        if any(not b or b'\0' in b for b in first.values()):time.sleep(.2);continue
        if all(p.read_bytes()==first[str(p)] for p in paths):return first
        time.sleep(.2)
    raise RuntimeError('Could not read a stable nonempty snapshot')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('date');a=parser.parse_args()
    assert len(a.date)==10 and datetime.strptime(a.date,'%Y-%m-%d')
    out=ROOT/'publication_snapshots'/a.date
    if out.exists():raise RuntimeError('Snapshot already exists; preserve it and choose a separate snapshot directory')
    src=ROOT/'subgraphx_hi_small/results/full';names=['REPORT.md','coverage.json','summary.csv','trial_means.csv']
    blocks=stable([src/n for n in names]);cov=json.loads(blocks[str(src/'coverage.json')])
    assert f'{cov["saved"]} / {cov["expected"]}' in blocks[str(src/'REPORT.md')].decode()
    for n in ['summary.csv','trial_means.csv']:
        lines=list(csv.reader(io.StringIO(blocks[str(src/n)].decode('utf8'))));assert len(lines)>3 and len(set(map(len,lines)))==1
    statuses=[];hashes={}
    for folder,subdir,expected in [('exploratory_transaction_consistency','pilot/cases',40),
                                   ('exploratory_resolution_validation','cases',100),
                                   ('exploratory_pattern_constraints','screening/cases',20)]:
        base=ROOT/folder/'results';mbytes=(base/'manifest.json').read_bytes();m=json.loads(mbytes)
        mid=hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest();counts=Counter();case_hashes={}
        # Completed case files are written before being counted. Incomplete writes fail this capture.
        for p in sorted((base/subdir).glob('*.json')):
            raw=p.read_bytes();case=json.loads(raw);assert case['manifest_id']==mid
            counts[case['dataset']]+=1;case_hashes[p.name]=digest(raw)
        raw=stable([base/'status.json'])[str(base/'status.json')];status=json.loads(raw)
        statuses.append(dict(experiment=folder,scope=subdir,saved=sum(counts.values()),expected=expected,
                             by_dataset=dict(counts),controller_state=status['state'],manifest_id=mid,
                             scientific_status='Incomplete; no completed-cohort claim',case_sha256=case_hashes))
        hashes[str((base/'manifest.json').relative_to(ROOT))]=digest(mbytes)
    (out/'subgraphx_hi_small').mkdir(parents=True)
    for n in names:
        data=blocks[str(src/n)];(out/'subgraphx_hi_small'/n).write_bytes(data)
        hashes[str((src/n).relative_to(ROOT))]=digest(data)
    stamp=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    record=dict(captured_at_perth=stamp,subgraphx_hi_small=cov,followups=statuses,source_sha256=hashes,
                capture_script_sha256=digest(Path(__file__).read_bytes()),
                note='Immutable upload snapshot. Per-case content, models and raw data remain local. Live controller_state is informational, not a scientific result.')
    (out/'snapshot.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    lines=['# Publication snapshot: '+a.date,'',f'Captured **{stamp}** (Australia/Perth).', '',
           'This folder is a fixed publication snapshot, not a live monitor. The completed contribution evidence is indexed in '
           '[RESEARCH_CONTRIBUTIONS.md](../../RESEARCH_CONTRIBUTIONS.md). Raw datasets, checkpoints and per-target record contents are excluded. '
           'The manifest stores hashes of the local case records used to count coverage.', '',
           '| Experiment | Saved / planned | State at capture |', '|---|---:|---|',
           f'| HI-Small SubgraphX | {cov["saved"]} / {cov["expected"]} | Incomplete; final cohort tables withheld |']
    for s in statuses:lines.append(f'| {s["experiment"]} | {s["saved"]} / {s["expected"]} | {s["controller_state"]}; conclusions pending |')
    lines+=['', 'The three follow-up controllers were found stopped during upload preparation. Their saved cases and immutable '
            'source/input hashes were checked before resuming. Invalid live metadata was preserved locally for diagnosis and '
            'is excluded from this upload. The live HI-Small SubgraphX controller was left running.', '',
            'Only source/protocols are published for the three unfinished follow-ups. Their partially accumulated effect estimates '
            'are not used to promote claims. Completed fresh-seed, deletion-access, search-budget, multigraph-resolution and '
            'negative fidelity-selector summaries are included in their respective experiment folders.', '',
            '[HI-Small SubgraphX report](subgraphx_hi_small/REPORT.md) | [coverage](subgraphx_hi_small/coverage.json) | '
            '[snapshot manifest](snapshot.json)', '',
            'The original tracked subgraphx_hi_small/results/full files are older publication artifacts; use this dated copy '
            'for the coverage uploaded with this snapshot. Later local progress requires a new deliberate upload.']
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps(dict(snapshot=str(out),captured_at=stamp,subgraphx=cov,followups=[{k:v for k,v in s.items() if k!='case_sha256'} for s in statuses]),indent=2))
if __name__=='__main__':main()
