"""Create an isolated three-trial continuation, preserving original case evidence."""
from pathlib import Path
import ast, hashlib, json, shutil

BASE = Path(__file__).resolve().parent
DEST = BASE / 'gnn_three_trials'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf8'))
def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2), encoding='utf8')

def setup():
    assert not (DEST/'results/full/manifest.json').exists(), 'Already launched; do not recreate sources'
    DEST.mkdir(exist_ok=True)
    source = BASE/'gnn_primary'
    for name in ['core.py', 'validate.py']:
        shutil.copy2(source/name, DEST/name)
    original = (source/'run.py').read_text(encoding='utf8')
    # Copy the proven per-target evaluation unchanged; only orchestration changes.
    code = original.replace("trial_count=5 if args.phase=='full' else args.trials", "trial_count=args.trials")
    code = code.replace("folder=ROOT/'results'/args.phase;", "assert args.phase=='full' and args.trials==3 and args.targets==0\n    folder=ROOT/'results'/args.phase;")
    code = code.replace("ROOT/'results/pilot/status.json'", "ROOT.parent/'gnn_primary/results/pilot/status.json'")
    code = code.replace("old=json.loads(dest.read_text());assert compatible_sources(old['sources'],sources) and old['params']==params", "old=json.loads(dest.read_text());assert valid_saved_case(dest,old,sources,params)")
    start, end = code.index('def compatible_sources('), code.index('\ndef report(')
    code = code[:start] + '''def reuse_record():
    record=json.loads((ROOT/'results/reuse_registry.json').read_text())
    for relative,digest in record['evidence'].items():
        assert sha(ROOT.parent/relative)==digest, 'Reuse evidence changed'
    return record

def compatible_sources(old,new):
    if old==new:return True
    record=reuse_record()
    return new==record['new_sources'] and old in record['accepted_sources']

def valid_saved_case(path,case,sources,params):
    if case['sources']==sources and case['params']==params:return True
    record=reuse_record()
    entry=record['cases'].get(path.name)
    return (entry is not None and sha(path)==entry['sha256']
            and compatible_sources(case['sources'],sources)
            and all(case['params'][k]==params[k] for k in ['outer','inner','draws','budget']))
''' + code[end:]
    # Preserve original aggregation and add the requested paper-layout report.
    code = code.replace("def run(args):", "from three_trial_tables import build as paper_report\nbase_report=report\ndef report(folder):\n    base_report(folder)\n    paper_report(folder)\n\ndef run(args):")
    code = code.replace("default=2)", "default=3)").replace("default=3);parser.add_argument('--trials'", "default=0);parser.add_argument('--trials'")
    (DEST/'run.py').write_text(code, encoding='utf8')
    # The expensive evaluation body must be literally identical to the validated runner.
    body_start="started=time.time();ctx=Context(cache,target)"
    body_end="                    report(folder)"
    assert original[original.index(body_start):original.index(body_end)] == code[code.index(body_start):code.index(body_end)]
    for p in DEST.glob('*.py'): ast.parse(p.read_text(encoding='utf8'))
    migration=read(source/'results/runtime_compatibility.json')
    evidence_path=BASE/migration['evidence_path']
    assert sha(evidence_path)==migration['evidence_sha256'] and read(evidence_path)['state']=='passed'
    def sources(root):
        return {str(p.relative_to(BASE)):sha(p) for p in list(root.glob('*.py'))+[BASE/'complete_graphs'/n for n in ['attack_core.py','prepare.py','run_study.py','subgraph_worker.py']]}
    current=sources(source)
    assert current==migration['new_sources']
    preview=BASE/'hi_small_preview'
    ps=read(preview/'results/preview/manifest.json')['sources']
    assert ps==sources(preview)
    assert sha(preview/'core.py')==sha(source/'core.py')
    preview_code=(preview/'run.py').read_text(encoding='utf8')
    assert original[original.index(body_start):original.index(body_end)]==preview_code[preview_code.index(body_start):preview_code.index(body_end)]
    accepted=[current,migration['old_sources'],ps]
    eligible={n:set(read(BASE/f'complete_graphs/results/full/{n}_targets.json')['selected']) for n in ['amlsim','hi_small']}
    assert {n:len(v) for n,v in eligible.items()}=={'amlsim':166,'hi_small':795}
    registry={}
    out=DEST/'results/full/cases';out.mkdir(parents=True,exist_ok=True)
    for folder in [source/'results/full/cases', preview/'results/preview/cases']:
        for p in sorted(folder.glob('*.json')):
            c=read(p)
            assert c['sources'] in accepted
            assert c['target'] in eligible[c['dataset']] and c['trial'] in [2026,2027,2028]
            assert all(c['params'][k]==v for k,v in dict(outer=100,inner=100,draws=40,budget=6).items())
            assert all(c['checks'].values())
            assert p.name not in registry
            shutil.copy2(p,out/p.name)
            registry[p.name]={'source':str(p.relative_to(BASE)), 'sha256':sha(p)}
    assert len(registry)==307
    write(DEST/'results/reuse_registry.json',dict(new_sources=sources(DEST),accepted_sources=accepted,cases=registry,
        evidence={str(evidence_path.relative_to(BASE)):sha(evidence_path)},
        explanation='Only cohort size/trial count and reporting changed; per-case computation is unchanged. Original case files retain original metadata. Earlier index caching is covered by the recorded equivalence benchmark.'))
    write(DEST/'results/setup_audit.json',dict(state='passed',reused=len(registry),expected=2883,remaining=2576,
        datasets={n:len(v) for n,v in eligible.items()},trials=[2026,2027,2028],per_case_body_identical=True))
    print('Verified and copied 307 cases; 2576 remain. Original results preserved.')

if __name__=='__main__': setup()
