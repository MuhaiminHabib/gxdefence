"""Benchmark a synchronization-only optimization without changing live code."""
import sys,inspect,json,time,statistics,importlib.util
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'gnn_primary'))
import core
from prepare import load
from attack_core import CachedSAGE,Context

spec=importlib.util.spec_from_file_location('reference_core',ROOT/'performance/before_core.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
source=inspect.getsource(reference.fit)
source=source.replace('m=z[hard].sigmoid();weights=presence[hard]','m=z.index_select(0,hard_idx).sigmoid();weights=presence.index_select(0,hard_idx)')
source=source.replace('if hard is None:hard=grad.detach()!=0','if hard is None:\n            hard=grad.detach()!=0\n            hard_idx=hard.nonzero().flatten()')
namespace=dict(core.__dict__);exec(compile(source,'cached-index-fit','exec'),namespace)
fast=namespace['fit'];original=reference.fit
results=[]
for name,target in [('amlsim',7598),('hi_small',277872)]:
    data,model,b=load(name);ctx=Context(CachedSAGE(data,model),target)
    rc=core.RelaxedContext(ctx,2026*100000+target)
    outputs=[];times=[]
    for implementation in [original,fast,original,fast]:
        p=torch.full_like(ctx.base,.0001,requires_grad=True)
        w=rc.presence(p)
        torch.cuda.synchronize();start=time.perf_counter()
        score=implementation(model,rc.x,rc.edge,w,rc.target,rc.label,rc.initial,100,True)
        g=torch.autograd.grad(score.sum(),p)[0];torch.cuda.synchronize()
        times.append(time.perf_counter()-start);outputs.append((score.detach(),g.detach()))
    mask_error=float((outputs[0][0]-outputs[1][0]).abs().max())
    grad_error=float((outputs[0][1]-outputs[1][1]).abs().max())
    repeat_grad_error=float((outputs[0][1]-outputs[2][1]).abs().max())
    print(json.dumps(dict(dataset=name,mask_error=mask_error,gradient_error=grad_error,original_repeat_mask_error=float((outputs[0][0]-outputs[2][0]).abs().max()),original_repeat_gradient_error=repeat_grad_error)),flush=True)
    torch.testing.assert_close(outputs[0][0],outputs[1][0],atol=1e-7,rtol=1e-6)
    torch.testing.assert_close(outputs[0][1],outputs[1][1],atol=1e-7,rtol=1e-6)
    # End-to-end optimizer: identical random state, all 100 outer steps and 40 draws.
    optimize=[];opt_times=[]
    for implementation in [original,fast]:
        core.fit=implementation;torch.cuda.synchronize();start=time.perf_counter()
        candidates,trace,_=core.optimize(ctx,2026*100000+target,100,100,40)
        torch.cuda.synchronize();opt_times.append(time.perf_counter()-start)
        optimize.append((candidates,trace))
    assert optimize[0][0]==optimize[1][0],'Discrete candidates differ'
    trace_error=max(abs(a[k]-b[k]) for a,b in zip(optimize[0][1],optimize[1][1]) for k in ['objective','distance','gradient_max'])
    assert trace_error<1e-6,'Optimizer trace differs beyond tolerance'
    results.append(dict(dataset=name,target=target,mask_error=mask_error,gradient_error=grad_error,trace_error=trace_error,all_40_candidates_identical=True,original_fit_seconds=statistics.mean(times[::2]),fast_fit_seconds=statistics.mean(times[1::2]),original_optimize_seconds=opt_times[0],fast_optimize_seconds=opt_times[1],speedup=opt_times[0]/opt_times[1]))
    print(json.dumps(results[-1]),flush=True)
    core.fit=original
    del data,model,b,ctx,rc,outputs;torch.cuda.empty_cache()
(ROOT/'performance/benchmark_indices.json').write_text(json.dumps(dict(state='passed',results=results),indent=2))
