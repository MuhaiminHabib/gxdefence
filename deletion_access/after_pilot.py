"""Launch only this experiment's full phase after its matching pilot passes."""
import ctypes,json,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'

def status(state,**extra):
    p=RESULTS/'queue_status.json';tmp=p.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(state=state,**extra),indent=2));tmp.replace(p)

def alive(pid):
    kernel=ctypes.windll.kernel32
    kernel.OpenProcess.argtypes=[ctypes.c_uint,ctypes.c_int,ctypes.c_uint]
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:return False
    code=ctypes.c_ulong()
    try:
        if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):raise RuntimeError('Cannot inspect pilot process')
        return code.value==259
    finally:kernel.CloseHandle(handle)

if __name__=='__main__':
    status('waiting_for_pilot')
    while True:
        p=RESULTS/'pilot/status.json'
        if not p.exists():raise RuntimeError('Start the validation pilot before this queue')
        current=json.loads(p.read_text())
        if current['state']=='complete' and not (RESULTS/'controller.lock').exists():break
        if current['state']=='failed':
            status('failed_pilot',reason='Full execution withheld; inspect pilot/status.json');sys.exit(1)
        if current['state']=='running' and not alive(current['pid']):
            status('pilot_process_exited',reason='Full execution withheld; pilot did not complete');sys.exit(1)
        time.sleep(15)
    status('running_full')
    with (RESULTS/'full_stdout.log').open('a',encoding='utf-8') as out,(RESULTS/'full_stderr.log').open('a',encoding='utf-8') as err:
        code=subprocess.call([sys.executable,'-u',str(ROOT/'run.py'),'full'],cwd=ROOT.parent,stdout=out,stderr=err)
    status('complete' if code==0 else 'failed_full',returncode=code)
