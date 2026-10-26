"""Directed multigraph adaptation of the GXAttack projected-ascent objective."""
import random
import numpy as np
import torch
from torch.nn import functional as F
from torch_geometric.utils import k_hop_subgraph, get_embeddings
from torch_geometric.explain import Explainer, PGExplainer, GNNExplainer
from prepare import DEVICE, PREP, seed

def cosine(a,b):
    if not torch.any(a) and not torch.any(b):return 1.
    return float(F.cosine_similarity(a.reshape(1,-1),b.reshape(1,-1)))
def project(p,budget):
    p=p.clamp(0,1)
    if p.sum()<=budget:return p
    lo=0.;hi=float(p.max())
    for _ in range(35):
        mid=(lo+hi)/2
        if (p-mid).clamp(0,1).sum()>budget:lo=mid
        else:hi=mid
    return (p-hi).clamp(0,1)
def make_pg(model,name,s):
    alg=PGExplainer(epochs=20,lr=1e-6).to(DEVICE)
    ex=Explainer(model=model,algorithm=alg,explanation_type='phenomenon',edge_mask_type='object',model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
    alg.load_state_dict(torch.load(PREP/f'{name}_pg_{s}.pt',map_location=DEVICE,weights_only=False))
    alg._curr_epoch=19;alg.mlp.eval()
    for p in alg.parameters():p.requires_grad_(False)
    return ex

class CachedSAGE:
    """Exact full-graph weighted mean GraphSAGE using sparse delta updates.

    Keeps external boundary messages. At binary weights it equals physical edits,
    including changed degree normalization and changes reaching outside the ego graph.
    """
    def __init__(self,data,model):
        self.data=data;self.model=model;self.x=data.x;self.e=data.edge_index
        self.n=data.num_nodes;src,dst=self.e
        with torch.no_grad():
            self.degree=torch.bincount(dst,minlength=self.n).to(self.x.dtype)
            self.sum1=torch.zeros_like(self.x).index_add_(0,dst,self.x[src])
            self.h1=F.relu(model.conv1.lin_l(self.sum1/self.degree.clamp_min(1)[:,None])+model.conv1.lin_r(self.x))
            self.sum2=self.x.new_zeros((self.n,self.h1.shape[1])).index_add_(0,dst,self.h1[src])
            self.logits=model.conv2.lin_l(self.sum2/self.degree.clamp_min(1)[:,None])+model.conv2.lin_r(self.h1)
            torch.testing.assert_close(self.logits,model(self.x,self.e),atol=2e-4,rtol=2e-4)

class Context:
    def __init__(self,cache,target):
        self.c=cache;self.target=int(target)
        nodes,e,m,mask=k_hop_subgraph(target,2,cache.e,num_nodes=cache.n)
        self.nodes=nodes;self.clean_ids=mask.nonzero().flatten()
        self.clean_edges=cache.e[:,self.clean_ids]
        pairs=set(map(tuple,self.clean_edges.T.cpu().tolist()))
        nonedges=[(a,b) for a in nodes.tolist() for b in nodes.tolist() if a!=b and (a,b) not in pairs]
        removable=self.clean_ids[self.clean_edges[0]!=self.clean_edges[1]]
        self.removable=removable
        self.m=len(removable)
        additions=torch.tensor(nonedges,device=DEVICE,dtype=torch.long).reshape(-1,2).T
        self.support=torch.cat([cache.e[:,removable],additions],1)
        self.base=torch.cat([torch.ones(self.m,device=DEVICE),torch.zeros(len(nonedges),device=DEVICE)])
        self.change_nodes=torch.unique(self.support[1])
        # Only first-layer destination states can change. Their outgoing messages
        # propagate changes to second-layer sums, including nodes outside the context.
        source_mask=torch.zeros(cache.n,dtype=torch.bool,device=DEVICE);source_mask[self.change_nodes]=True
        self.outgoing=cache.e[:,source_mask[cache.e[0]]]
        self.affected=torch.unique(torch.cat([self.outgoing[1],self.change_nodes]))
        # Sorted-index maps avoid allocating full hidden-state matrices per step.
        self.dst1=torch.searchsorted(self.change_nodes,self.support[1])
        self.os1=torch.searchsorted(self.change_nodes,self.outgoing[0])
        self.od2=torch.searchsorted(self.affected,self.outgoing[1])
        self.dst2=torch.searchsorted(self.affected,self.support[1])
        self.changed2=torch.searchsorted(self.affected,self.change_nodes)
        self.src_changed=source_mask[self.support[0]]
        self.src1=torch.searchsorted(self.change_nodes,self.support[0][self.src_changed])
        self.ids=[f'E{int(i)}' for i in removable]+[f'A{a}:{b}' for a,b in nonedges]
        self.fixed_ids=self.clean_ids[~torch.isin(self.clean_ids,removable)]
        self.score_edges=torch.cat([self.support,cache.e[:,self.fixed_ids]],1)
        self.score_ids=self.ids+[f'E{int(i)}' for i in self.fixed_ids]
    def forward(self,w):
        c=self.c;src,dst=self.support;delta=w-self.base
        degree1=c.degree[self.change_nodes].index_add(0,self.dst1,delta).clamp_min(1)
        sum1=c.sum1[self.change_nodes].index_add(0,self.dst1,c.x[src]*delta[:,None])
        h1=F.relu(c.model.conv1.lin_l(sum1/degree1[:,None])+c.model.conv1.lin_r(c.x[self.change_nodes]))
        os,od=self.outgoing
        sum2=c.sum2[self.affected].index_add(0,self.od2,h1[self.os1]-c.h1[os])
        source_h=c.h1[src].clone();source_h[self.src_changed]=h1[self.src1]
        sum2=sum2.index_add(0,self.dst2,source_h*delta[:,None])
        degree2=c.degree[self.affected].index_add(0,self.dst2,delta).clamp_min(1)
        root_h=c.h1[self.affected].index_copy(0,self.changed2,h1)
        out=c.model.conv2.lin_l(sum2/degree2[:,None])+c.model.conv2.lin_r(root_h)
        return c.logits.index_copy(0,self.affected,out)
    def scores(self,w,pg):
        logits=self.forward(w)
        inputs=pg.algorithm._get_inputs(logits,self.score_edges,self.target)
        scores=pg.algorithm.mlp(inputs).reshape(-1).sigmoid()
        presence=torch.cat([w,torch.ones(len(self.fixed_ids),device=DEVICE)])
        return logits,scores*presence
    def physical(self,edits):
        c=self.c;removed=self.removable[[i for i in edits if i<self.m]]
        keep=torch.ones(c.e.shape[1],dtype=torch.bool,device=DEVICE);keep[removed]=False
        add=[i for i in edits if i>=self.m]
        edges=torch.cat([c.e[:,keep],self.support[:,add]],1)
        ids=[f'E{i}' for i in keep.nonzero().flatten().tolist()]+[self.ids[i] for i in add]
        return edges,ids
    def weights(self,edits):
        w=self.base.clone();w[edits]=1-w[edits];return w
    def native_pg(self,edits,pg):
        edges,ids=self.physical(edits)
        with torch.no_grad():
            emb=get_embeddings(self.c.model,self.c.x,edges)[-1]
            logits=emb  # These frozen two-layer classifiers return conv2 directly.
            _,_,_,mask=k_hop_subgraph(self.target,2,edges,num_nodes=self.c.n)
            idx=mask.nonzero().flatten()
            scores=pg.algorithm.mlp(pg.algorithm._get_inputs(emb,edges[:,idx],self.target)).reshape(-1).sigmoid()
        return logits,{ids[i]:v for i,v in zip(idx.cpu().tolist(),scores.cpu().tolist())},edges,ids
    def validate(self,pg):
        for edits in [[],list(range(min(2,self.m)))+[self.m]]:
            w=self.weights(edits)
            logits,rank,edges,ids=self.native_pg(edits,pg)
            with torch.no_grad():out,z=self.scores(w,pg)
            torch.testing.assert_close(out,logits,atol=3e-4,rtol=3e-4)
            lookup={k:float(v) for k,v in zip(self.score_ids,z)}
            for k,v in rank.items():
                if k in lookup and abs(v-lookup[k])>3e-4:raise AssertionError('PG weighted/native mismatch')
        p=torch.zeros_like(self.base,requires_grad=True)
        out,z=self.scores(self.base+(1-2*self.base)*p,pg)
        grad=torch.autograd.grad(out[self.target].sum()+z.sum(),p)[0]
        if not torch.isfinite(grad).all():raise AssertionError('Nonfinite edge gradients')
        return dict(binary_equivalence=True,pg_native_equivalence=True,finite_gradients=True,max_gradient=float(grad.abs().max()))

def attack(ctx,pg,s,budget=6,epochs=100):
    seed(s)
    with torch.no_grad():
        clean_out,clean=ctx.scores(ctx.base,pg);label=int(clean_out[ctx.target].argmax())
    candidates=[];traces=[]
    for restart in range(2):
        p=(torch.zeros_like(ctx.base) if restart==0 else project(torch.rand_like(ctx.base)*.01,budget)).requires_grad_()
        trace=[]
        for epoch in range(epochs):
            out,z=ctx.scores(ctx.base+(1-2*ctx.base)*p,pg)
            q=p*.99+.005;entropy=-(q*q.log()+(1-q)*(1-q).log()).mean()
            objective=out[ctx.target].log_softmax(-1)[label]-.0005*entropy+.1*(1-F.cosine_similarity(clean[None],z[None])[0])
            grad=torch.autograd.grad(objective,p)[0]
            if not torch.isfinite(grad).all():raise ValueError('nonfinite attack gradient')
            with torch.no_grad():p.copy_(project(p+.01*grad,budget))
            if epoch in (0,epochs-1):trace.append(dict(epoch=epoch,objective=float(objective),gradient_max=float(grad.abs().max()),relaxed_budget=float(p.sum())))
        traces.append(trace)
        with torch.no_grad():
            weights=p.clamp_min(1e-12)
            for _ in range(20):
                edits=torch.multinomial(weights,budget,replacement=False).tolist()
                out,z=ctx.scores(ctx.weights(edits),pg)
                keep=int(out[ctx.target].argmax())==label
                distance=1-cosine(clean,z)
                candidates.append((keep,distance,edits))
    best=max(candidates,key=lambda v:(v[0],v[1]))
    rng=random.Random(s+51)
    flipping=rng.sample(range(len(ctx.base)),budget)
    rewiring=rng.sample(range(ctx.m),budget//2)+rng.sample(range(ctx.m,len(ctx.base)),budget//2)
    return {'GXAttack':best[2],'Random flipping':flipping,'Random rewiring':rewiring},dict(traces=traces,discretizations=len(candidates),preserved_draws=sum(int(x[0]) for x in candidates))

def gnn_explain(ctx,edges,ids,s):
    seed(s)
    nodes,local,mapping,mask=k_hop_subgraph(ctx.target,2,edges,relabel_nodes=True,num_nodes=ctx.c.n)
    target=int(mapping);x=ctx.c.x[nodes]
    if local.shape[1]==0:return {}
    ex=Explainer(model=ctx.c.model,algorithm=GNNExplainer(epochs=100),explanation_type='model',edge_mask_type='object',model_config=dict(mode='multiclass_classification',task_level='node',return_type='raw'))
    explanation=ex(x,local,index=target)
    return {ids[int(i)]:float(v) for i,v in zip(mask.nonzero().flatten(),explanation.edge_mask.detach())}

def compare(a,b,k=10):
    keys=sorted(set(a)|set(b));x=torch.tensor([a.get(i,0.) for i in keys]);y=torch.tensor([b.get(i,0.) for i in keys])
    top=lambda d:sorted(d,key=lambda i:(-d[i],i))[:k]
    aa=set(top(a));bb=set(top(b));union=aa|bb
    binary=0. if not aa or not bb else len(aa&bb)/(len(aa)*len(bb))**.5
    if not union:binary=1.
    return dict(cosine=cosine(x,y),jaccard=len(aa&bb)/len(union) if union else 1.,binary_cosine=binary,clean_size=len(aa),attacked_size=len(bb),clean_empty=not bool(a),attacked_empty=not bool(b))

def fidelity(ctx,edges,ids,scores,k):
    chosen=set(sorted(scores,key=lambda i:(-scores[i],i))[:k])
    # Deletions cannot expand a two-layer incoming receptive field. This exact
    # computation saves full-graph forwards for each explanation budget.
    nodes,local,mapping,mask=k_hop_subgraph(ctx.target,2,edges,relabel_nodes=True,num_nodes=ctx.c.n)
    x=ctx.c.x[nodes];target=int(mapping)
    select=torch.tensor([ids[i] in chosen for i in mask.nonzero().flatten().cpu().tolist()],device=DEVICE,dtype=torch.bool)
    with torch.no_grad():
        baseline=ctx.c.model(x,local)[target];label=int(baseline.argmax());p=float(baseline.softmax(-1)[label])
        removed=ctx.c.model(x,local[:,~select])[target]
        kept=ctx.c.model(x,local[:,select])[target]
    return dict(necessity=int(removed.argmax()!=label),sufficiency_failure=int(kept.argmax()!=label),removed_probability_drop=p-float(removed.softmax(-1)[label]),kept_probability_gap=p-float(kept.softmax(-1)[label]),size=len(chosen))
