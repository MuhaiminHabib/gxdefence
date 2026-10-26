"""Independent numerical checks for graph relaxation and metric conventions."""
import torch
from torch_geometric.data import Data
from prepare import DEVICE,seed,save,ROOT
from src.models.marasi_models import MarasiGraphSAGE
from attack_core import CachedSAGE,Context,project,compare,fidelity
seed(7)
e=torch.tensor([[0,0,1,2,3,4,4],[1,1,2,3,4,2,4]],device=DEVICE)
x=torch.randn(5,3,device=DEVICE);m=MarasiGraphSAGE(3,4).to(DEVICE).eval()
for p in m.parameters():p.requires_grad_(False)
c=CachedSAGE(Data(x=x,edge_index=e),m);ctx=Context(c,3)
# Compare against an independently evaluated weighted adjacency, including duplicates.
w=(ctx.base*.6+.2).requires_grad_();dense=x.new_zeros(5,5)
for a,b in e.T:dense[b,a]+=1
for i,(a,b) in enumerate(ctx.support.T):dense[b,a]=dense[b,a]+w[i]-ctx.base[i]
degree=dense.sum(1).clamp_min(1)[:,None]
h=torch.relu(m.conv1.lin_l((dense@x)/degree)+m.conv1.lin_r(x))
expected=m.conv2.lin_l((dense@h)/degree)+m.conv2.lin_r(h)
actual=ctx.forward(w);torch.testing.assert_close(actual,expected,atol=1e-5,rtol=1e-5)
ga=torch.autograd.grad(actual.sum(),w,retain_graph=True)[0];gb=torch.autograd.grad(expected.sum(),w)[0]
torch.testing.assert_close(ga,gb,atol=1e-5,rtol=1e-5)
for edits in [[],[0],[ctx.m],[0,ctx.m]]:
    edges,ids=ctx.physical(edits)
    torch.testing.assert_close(ctx.forward(ctx.weights(edits)),m(x,edges),atol=1e-5,rtol=1e-5)
    chosen={ids[0]:1.};f=fidelity(ctx,edges,ids,chosen,1)
    with torch.no_grad():
        base=m(x,edges)[3];label=int(base.argmax());select=torch.tensor([i in chosen for i in ids],device=DEVICE)
        removed=m(x,edges[:,~select])[3];kept=m(x,edges[:,select])[3]
    assert f['necessity']==int(removed.argmax()!=label)
    assert f['sufficiency_failure']==int(kept.argmax()!=label)
    assert abs(f['removed_probability_drop']-float(base.softmax(-1)[label]-removed.softmax(-1)[label]))<1e-6
assert compare({'E1':1.},{'E2':1.})['cosine']==0
assert compare({}, {})['cosine']==1
assert compare({}, {'E1':1.})['cosine']==0
assert float(project(torch.ones(100,device=DEVICE),6).sum())<=6.0001
save(ROOT/'results/core_validation.json',dict(state='passed',checks=['weighted dense adjacency equivalence','autograd equivalence','physical addition/deletion equivalence with parallel edges and self-loops','empty and disjoint mask metrics','projection budget']))
print('CORE VALIDATION PASSED')
