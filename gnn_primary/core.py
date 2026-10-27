"""Differentiable GNNExplainer fitting for a GXAttack-objective adaptation.

Graph presence controls mean aggregation degrees; explanation masks control
messages, as in PyG SAGEConv's explanation mode. No PG surrogate is used.
"""
import sys, math
from pathlib import Path
import torch
from torch.nn import functional as F
from torch_geometric.utils import k_hop_subgraph
from torch_geometric.explain import Explainer,GNNExplainer
from torch_geometric.explain.algorithm.utils import set_masks,clear_masks

OLD=Path(__file__).resolve().parents[1]/'complete_graphs'
sys.path.insert(0,str(OLD))
from attack_core import project

def forward(model,x,edge,presence,mask=None):
    src,dst=edge
    degree=x.new_zeros(len(x)).index_add(0,dst,presence).clamp_min(1)
    weight=presence if mask is None else presence*mask
    adjacency=None
    if len(x)<=1024:
        adjacency=x.new_zeros(len(x)*len(x)).index_add(0,dst*len(x)+src,weight).reshape(len(x),len(x))
    def layer(conv,h):
        sums=adjacency@h if adjacency is not None else h.new_zeros((len(h),h.shape[1])).index_add(0,dst,h[src]*weight[:,None])
        return conv.lin_l(sums/degree[:,None])+conv.lin_r(h)
    h=F.relu(layer(model.conv1,x))
    return layer(model.conv2,h)

def fit(model,x,edge,presence,target,label,initial,steps=100,unroll=False):
    z=initial.clone().requires_grad_(True)
    first=second=torch.zeros_like(z)
    hard=None
    for i in range(steps):
        out=forward(model,x,edge,presence,z.sigmoid())[target]
        loss=-out.log_softmax(-1)[label]
        if hard is not None:
            m=z.index_select(0,hard_idx).sigmoid();weights=presence.index_select(0,hard_idx)
            entropy=-m*torch.log(m+1e-15)-(1-m)*torch.log(1-m+1e-15)
            loss=loss+.005*(weights*m).sum()+(weights*entropy).sum()/weights.sum().clamp_min(1e-15)
        grad=torch.autograd.grad(loss,z,create_graph=unroll)[0]
        if hard is None:
            hard=grad.detach()!=0
            hard_idx=hard.nonzero().flatten()
        first=.9*first+.1*grad;second=.999*second+.001*grad.square()
        # Clamp only prevents undefined higher derivatives at zero Adam variance.
        z=z-.01*(first/(1-.9**(i+1)))/((second/(1-.999**(i+1))).clamp_min(1e-30).sqrt()+1e-8)
        if not unroll:z=z.detach().requires_grad_(True)
    return z.sigmoid()*hard.to(z.dtype)*presence

def native_fixed_init(model,x,edge,target,initial,steps=100):
    alg=GNNExplainer(epochs=steps)
    original=alg._initialize_masks
    def initialize(x,e):
        original(x,e)
        alg.edge_mask=torch.nn.Parameter(initial.clone())
    alg._initialize_masks=initialize
    ex=Explainer(model=model,algorithm=alg,explanation_type='model',edge_mask_type='object',model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
    return ex(x,edge,index=target).edge_mask.detach()

class RelaxedContext:
    def __init__(self,ctx,seed):
        self.ctx=ctx;self.model=ctx.c.model
        # The union graph's receptive field includes external boundary nodes that
        # can become relevant through new edges, avoiding a truncated predictor.
        added=ctx.support[:,ctx.m:]
        union=torch.cat([ctx.c.e,added],1)
        nodes,e,mapping,mask=k_hop_subgraph(ctx.target,2,union,relabel_nodes=True,num_nodes=ctx.c.n)
        global_ids=mask.nonzero().flatten()
        self.nodes=nodes;self.edge=e;self.x=ctx.c.x[nodes];self.target=int(mapping)
        self.base=(global_ids<ctx.c.e.shape[1]).to(self.x.dtype)
        lookup={int(v):i for i,v in enumerate(global_ids.cpu().tolist())}
        support_global=ctx.removable.cpu().tolist()+list(range(ctx.c.e.shape[1],union.shape[1]))
        self.positions=torch.tensor([lookup[i] for i in support_global],device=e.device)
        generator=torch.Generator(device=e.device).manual_seed(seed)
        self.initial=torch.randn(len(global_ids),generator=generator,device=e.device)*math.sqrt(2/len(nodes))
        self.label=int(ctx.c.logits[ctx.target].argmax())
    def presence(self,p):
        w=self.ctx.base+(1-2*self.ctx.base)*p
        return self.base.index_copy(0,self.positions,w)
    def explain(self,p,steps=100,unroll=True):
        w=self.presence(p)
        return fit(self.model,self.x,self.edge,w,self.target,self.label,self.initial,steps,unroll)
    def logits(self,p):
        return forward(self.model,self.x,self.edge,self.presence(p))[self.target]

def optimize(ctx,seed,outer=100,inner=100,draws=40):
    relaxed=RelaxedContext(ctx,seed)
    zero=torch.zeros_like(ctx.base)
    clean=relaxed.explain(zero,inner,False).detach()
    trace=[]
    # Interior start allows additions to participate in the fitted-mask response.
    generator=torch.Generator(device=zero.device).manual_seed(seed+1)
    p=project(torch.rand(len(zero),generator=generator,device=zero.device)*.01,6).requires_grad_()
    for step in range(outer):
        mask=relaxed.explain(p,inner,True)
        distance=1-F.cosine_similarity(clean[None],mask[None])[0]
        q=p*.99+.005;entropy=-(q*q.log()+(1-q)*(1-q).log()).mean()
        objective=relaxed.logits(p).log_softmax(-1)[relaxed.label]+.1*distance-.0005*entropy
        grad=torch.autograd.grad(objective,p)[0]
        if not torch.isfinite(grad).all():raise RuntimeError('Nonfinite unrolled gradient')
        trace.append(dict(step=step,objective=float(objective.detach()),distance=float(distance.detach()),gradient_max=float(grad.abs().max())))
        p=project(p.detach()+.01*grad.detach(),6).requires_grad_()
    weights=p.detach().clamp_min(1e-12)
    candidates=[torch.multinomial(weights,6,replacement=False,generator=generator).tolist() for _ in range(draws)]
    return candidates,trace,relaxed
