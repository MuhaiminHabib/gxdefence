"""Independent full-graph CPU prediction checks on the two technical-pilot cases."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;STUDY=ROOT.parent;OUT=ROOT/'results'
spec=importlib.util.spec_from_file_location('full_prediction_helpers',STUDY/'followup_audit/run.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def main():
    d=json.loads((OUT/'manifest.json').read_text());checks=[]
    inputs={str(Path(__file__).relative_to(STUDY)):H.sha(Path(__file__)),
            str((OUT/'manifest.json').relative_to(STUDY)):H.sha(OUT/'manifest.json')}
    for name in ['amlsim','hi_small']:
        t=d['targets'][name][0];p=OUT/f'cases/{name}_{t}.json';case=json.loads(p.read_text());inputs[str(p.relative_to(STUDY))]=H.sha(p)
        p=STUDY/f'complete_graphs/prepared/{name}.pt';assert H.sha(p)==d['inputs'][str(p.relative_to(STUDY))]
        b=H.torch.load(p,map_location='cpu',weights_only=False);data=b['data']
        model=H.MarasiGraphSAGE(data.num_features,b['hidden']);model.load_state_dict(b['state']);model.eval()
        source=STUDY/f'gnn_three_trials/results/full/cases/{name}_{t}_2026.json'
        assert H.sha(source)==d['inputs'][str(source.relative_to(STUDY))];old=json.loads(source.read_text())
        for method in ['Clean','GNN-targeted GX adaptation']:
            edit=[] if method=='Clean' else old['attacks'][method]['edge_ids'];e,_=H.physical(data,edit)
            with H.torch.no_grad():full=model(data.x,e)[t]
            local=H.torch.tensor(case['predictions'][method]['logits'])
            H.torch.testing.assert_close(full,local,atol=3e-4,rtol=3e-4)
            checks.append(dict(dataset=name,target=t,method=method,max_logit_error=float((full-local).abs().max())))
        del data,b,model
    H.save(OUT/'full_prediction_validation.json',dict(passed=True,inputs=inputs,checks=checks))
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
