"""Exact changes in distinct-vertex directed multigraph 2/3-cycle counts."""
from collections import Counter
import numpy as np
from scipy.sparse import coo_matrix

class Structure:
    def __init__(self, edge, n):
        self.edge=np.asarray(edge);self.n=n
        keep=self.edge[0]!=self.edge[1]
        self.csr=coo_matrix((np.ones(int(keep.sum()),dtype=np.int64),self.edge[:,keep]),shape=(n,n)).tocsr()
        self.csc=self.csr.tocsc();self.outcache={};self.incache={}
    def outgoing(self,u):
        if u not in self.outcache:
            a,b=self.csr.indptr[u:u+2];self.outcache[u]=dict(zip(self.csr.indices[a:b].tolist(),self.csr.data[a:b].tolist()))
        return self.outcache[u]
    def incoming(self,u):
        if u not in self.incache:
            a,b=self.csc.indptr[u:u+2];self.incache[u]=dict(zip(self.csc.indices[a:b].tolist(),self.csc.data[a:b].tolist()))
        return self.incache[u]
    def edits(self,rewires):
        old=[(int(self.edge[0,r]),int(self.edge[1,r]),-1) for r,v in rewires]
        new=[(int(self.edge[0,r]),int(v),1) for r,v in rewires]
        return old+new
    def delta(self,rewires):
        outs={};ins={};d2=d3=0;indegree=Counter();outdegree=Counter()
        def out(u):return outs[u] if u in outs else self.outgoing(u)
        def inc(u):return ins[u] if u in ins else self.incoming(u)
        for u,v,change in self.edits(rewires):
            assert u!=v
            d2+=change*out(v).get(u,0)
            a,b=out(v),inc(u)
            if len(a)>len(b):a,b=b,a
            d3+=change*sum(count*b.get(w,0) for w,count in a.items() if w not in (u,v))
            if u not in outs:outs[u]=dict(self.outgoing(u))
            if v not in ins:ins[v]=dict(self.incoming(v))
            value=outs[u].get(v,0)+change;assert value>=0
            if value:outs[u][v]=value;ins[v][u]=value
            else:outs[u].pop(v,None);ins[v].pop(u,None)
            outdegree[u]+=change;indegree[v]+=change
        return dict(cycles2_delta=int(d2),cycles3_delta=int(d3),
                    indegree_l1=int(sum(abs(v) for v in indegree.values())),
                    outdegree_l1=int(sum(abs(v) for v in outdegree.values())))
    def independent_delta(self,rewires):
        """Enumerate cycles touching any edited endpoint, avoiding whole-graph powers."""
        touched={u for u,v,d in self.edits(rewires)}|{v for u,v,d in self.edits(rewires)}
        changed={u:dict(self.outgoing(u)) for u in touched}
        for u,v,d in self.edits(rewires):
            changed[u][v]=changed[u].get(v,0)+d
            if not changed[u][v]:del changed[u][v]
        def counts(edited):
            def out(u):return changed[u] if edited and u in changed else self.outgoing(u)
            two={};three={}
            for u in touched:
                for v,a in out(u).items():
                    if u==v:continue
                    reverse=out(v).get(u,0)
                    if reverse:two[tuple(sorted((u,v)))]=a*reverse
                    for w,b in out(v).items():
                        if w in (u,v):continue
                        c=out(w).get(u,0)
                        if c:
                            key=min((u,v,w),(v,w,u),(w,u,v));three[key]=a*b*c
            return sum(two.values()),sum(three.values())
        before=counts(False);after=counts(True)
        return dict(cycles2_delta=after[0]-before[0],cycles3_delta=after[1]-before[1])

def self_test():
    rng=np.random.default_rng(179611);comparisons=0
    for _ in range(100):
        n=8;edge=rng.integers(0,n,(2,60));s=Structure(edge,n)
        eligible=np.flatnonzero(edge[0]!=edge[1])
        for j in range(5):
            ids=rng.choice(eligible,3,replace=False)
            rw=[(int(r),int(rng.choice([v for v in range(n) if v!=edge[0,r]]))) for r in ids]
            result=s.delta(rw);independent=s.independent_delta(rw)
            modified=edge.copy()
            for r,v in rw:modified[1,r]=v
            def brute(e):
                a=np.zeros((n,n),dtype=np.int64)
                for u,v in e.T:
                    if u!=v:a[u,v]+=1
                return int(np.trace(a@a)//2),int(np.trace(a@a@a)//3)
            before,after=brute(edge),brute(modified)
            assert result['cycles2_delta']==independent['cycles2_delta']==after[0]-before[0]
            assert result['cycles3_delta']==independent['cycles3_delta']==after[1]-before[1]
            assert result['indegree_l1']==int(np.abs(np.bincount(edge[1],minlength=n)-np.bincount(modified[1],minlength=n)).sum())
            comparisons+=1
    return dict(passed=True,random_multigraph_checks=comparisons,includes_parallel_edges_and_self_loops=True)
