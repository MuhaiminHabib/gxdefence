"""Wait for active preparation, validate, then run pilot and complete evaluation."""
from pathlib import Path
import subprocess,sys,time,json,traceback
ROOT=Path(__file__).resolve().parent
def status(value):
    p=ROOT/'results/launcher_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2));tmp.replace(p)
try:
    status(dict(state='waiting_for_preparation',started=time.time()))
    deadline=time.monotonic()+6*3600
    while True:
        p=ROOT/'results/preparation_status.json'
        state=json.loads(p.read_text()) if p.exists() else {}
        if state.get('state')=='complete':break
        log=(ROOT/'results/prepare.log').read_text(encoding='utf8',errors='replace')
        if 'Traceback (most recent call last)' in log:raise RuntimeError('Preparation failed; inspect prepare.log')
        if time.monotonic()>deadline:raise TimeoutError('Preparation did not complete within six hours')
        time.sleep(5)
    for dataset in ['elliptic','amlsim','hi_small']:
        for s in range(2026,2031):
            if not (ROOT/f'prepared/{dataset}_pg_{s}.pt').exists():raise RuntimeError('Missing PG fit')
    status(dict(state='validating',time=time.time()))
    subprocess.run([sys.executable,str(ROOT/'validate_core.py')],check=True,cwd=ROOT)
    status(dict(state='running_pilot_then_all_targets',time=time.time()))
    subprocess.run([sys.executable,'-u',str(ROOT/'continue_study.py')],check=True,cwd=ROOT)
    status(dict(state='complete',finished=time.time()))
except Exception:
    status(dict(state='failed',traceback=traceback.format_exc()));raise
