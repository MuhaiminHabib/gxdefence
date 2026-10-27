"""Must pass before a real-data attack pilot is accepted."""
import json
from pathlib import Path
import torch
from core import forward,fit,native_fixed_init
from prepare import seed
from src.models.marasi_models import MarasiGraphSAGE

def run():
    seed(44)
    model=MarasiGraphSAGE(3,5).double().eval()
    for p in model.parameters():p.requires_grad_(False)
    x=torch.randn(5,3,dtype=torch.double)
    edge=torch.tensor([[0,0,1,2,3,4,4],[1,1,2,3,4,2,4]])
    w=torch.ones(edge.shape[1],dtype=torch.double)
    torch.testing.assert_close(forward(model,x,edge,w),model(x,edge),atol=1e-10,rtol=1e-10)
    target=3;label=int(model(x,edge)[target].argmax());initial=torch.randn(len(w),dtype=torch.double)*.2
    actual=fit(model,x,edge,w,target,label,initial,100,False)
    expected=native_fixed_init(model,x,edge,target,initial,100)
    torch.testing.assert_close(actual,expected,atol=1e-6,rtol=1e-6)
    # Independent central differences verify derivatives through Adam fitting.
    w=torch.full_like(w,.8).requires_grad_()
    weights=torch.linspace(.2,1,len(w),dtype=w.dtype)
    value=(fit(model,x,edge,w,target,label,initial,12,True)*weights).sum()
    grad=torch.autograd.grad(value,w)[0]
    numerical=[]
    for i in range(len(w)):
        delta=torch.zeros_like(w);delta[i]=1e-5
        a=(fit(model,x,edge,w.detach()+delta,target,label,initial,12,False)*weights).sum()
        b=(fit(model,x,edge,w.detach()-delta,target,label,initial,12,False)*weights).sum()
        numerical.append(float((a-b)/(2e-5)))
    numerical=torch.tensor(numerical,dtype=w.dtype)
    torch.testing.assert_close(grad,numerical,atol=2e-5,rtol=2e-4)
    assert grad.abs().max()>0 and torch.isfinite(grad).all()
    result=dict(state='passed',native_mask_max_error=float((actual-expected).abs().max()),hypergradient_max_error=float((grad-numerical).abs().max()),checks=['native PyG mask parity at identical initialization, 100 Adam steps','parallel edges and self loop predictor equivalence','unrolled Adam gradient versus independent finite differences'])
    out=Path(__file__).parent/'results';out.mkdir(exist_ok=True)
    (out/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
if __name__=='__main__':run()
