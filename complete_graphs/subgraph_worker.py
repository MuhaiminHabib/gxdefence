"""Persistent DGL worker: one JSON request/response per line."""
import sys,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'framework'))
import numpy as np
import torch,dgl
from dgl.nn.pytorch.explain import SubgraphX
from src.models.marasi_models import MarasiGraphSAGE
torch.set_num_threads(2)
for line in sys.stdin:
    try:
        request=json.loads(line);bundle=torch.load(request['path'],map_location='cpu',weights_only=False)
        s=request['seed'];random.seed(s);np.random.seed(s);torch.manual_seed(s)
        x,e=bundle['x'],bundle['edge'];model=MarasiGraphSAGE(x.shape[1],bundle['hidden'])
        model.load_state_dict(bundle['state']);model.eval()
        for p in model.parameters():p.requires_grad_(False)
        graph=dgl.graph((e[0],e[1]),num_nodes=len(x))
        class Adapter(torch.nn.Module):
            def forward(self,g,features):return model(features,e)[bundle['target']:bundle['target']+1]
        adapter=Adapter().eval()
        with torch.no_grad():torch.testing.assert_close(adapter(graph,x)[0],bundle['logits'],atol=3e-4,rtol=3e-4)
        alg=SubgraphX(adapter,num_hops=2,num_child=6,num_rollouts=5,node_min=3,shapley_steps=5,log=False)
        # A context at or below the stopping size is already a terminal coalition.
        nodes=list(range(len(x))) if len(x)<=3 else alg.explain_graph(graph,x,target_class=bundle['label']).tolist()
        selected=set(nodes)
        ids=[bundle['ids'][i] for i,(a,b) in enumerate(e.T.tolist()) if a in selected and b in selected]
        result=dict(ids=ids,nodes=[int(bundle['nodes'][i]) for i in nodes])
        print(json.dumps(result),flush=True)
    except Exception:
        import traceback
        print(json.dumps({'error':traceback.format_exc()}),flush=True)
