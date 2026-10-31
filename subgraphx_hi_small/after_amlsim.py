"""Sequential experiment controller: wait for AMLSim, then run HI-Small."""
import json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'
RESULTS.mkdir(exist_ok=True)

def status(state,**extra):
    p=RESULTS/'queue_status.json';tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(state=state,**extra),indent=2),encoding='utf8');tmp.replace(p)

if __name__=='__main__':
    prior=ROOT.parent/'subgraphx_primary/results/full'
    status('waiting_for_amlsim',dataset='hi_small',targets=795,trials=1,pilot_evaluations=3)
    while True:
        current=json.loads((prior/'status.json').read_text())
        if current['state']=='complete':
            coverage=json.loads((prior/'coverage.json').read_text())
            assert coverage['complete'] and coverage['saved']==coverage['expected']==498
            break
        if current['state'] in ['failed','stopped_by_user']:
            status('blocked_by_amlsim',upstream_state=current['state']);sys.exit(1)
        time.sleep(30)
    status('running_hi_small',targets=795,trials=1)
    with (RESULTS/'pipeline_stdout.log').open('a',encoding='utf8') as out, (RESULTS/'pipeline_stderr.log').open('a',encoding='utf8') as err:
        result=subprocess.run([sys.executable,'-u','-X','utf8',str(ROOT/'run.py'),'pipeline'],cwd=ROOT,stdout=out,stderr=err)
    status('complete' if result.returncode==0 else 'failed',returncode=result.returncode)
