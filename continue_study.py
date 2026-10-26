"""Run all remaining pilot cases, then the full study only after pilot gates pass."""
import sys,subprocess,time,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def status(**kw):
    p=ROOT/'results/pipeline_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(kw,indent=2));tmp.replace(p)
try:
    for phase in ['pilot','full']:
        status(state='running',phase=phase,started=time.time())
        with (ROOT/f'results/{phase}_continued.log').open('a',encoding='utf8') as log:
            rc=subprocess.call([sys.executable,'-u',str(ROOT/'run_study.py'),phase],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
        subprocess.run([sys.executable,str(ROOT/'report.py')],check=True,cwd=ROOT)
        if rc:raise RuntimeError(f'{phase} failed; inspect results/{phase}_continued.log')
    status(state='complete',finished=time.time())
except Exception:
    status(state='failed',traceback=traceback.format_exc());raise
