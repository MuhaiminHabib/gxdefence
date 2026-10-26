"""Read-only model audit; separate pilot outputs, no attack reruns or tuning."""
import json, math, random, time
from pathlib import Path
import torch
import pandas as pd
from torch_geometric.utils import k_hop_subgraph
from prepare import ROOT, load, save, sha

OUT=ROOT/'results/fidelity_diagnostic'

@torch.no_grad()
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    plan={}
    for name in ['amlsim','hi_small']:
        census=json.loads((ROOT/f'results/full/{name}_targets.json').read_text())
        plan[name]=sorted(random.Random(42).sample(census['selected'],10))
    save(OUT/'protocol.json',dict(targets=plan,seed=42,trial=2026,explainers=['PGExplainer','GNNExplainer'],sizes=['top5','top10','top20','top25pct'],scope='Diagnostic sample from existing eligible test cohort; not an independent validation set. No model or attack tuning.',soft_metrics='Signed original-class probability drop: baseline minus removed/kept. Negative values retained.',audit='Independent full-graph physical edge removal and retention compared with local two-hop forwards for every selected set.',source_sha256=sha(__file__)))
    rows=[];empty_rows=[];max_error=0.;start=time.time()
    for name,targets in plan.items():
        data,model,b=load(name)
        weights={k:v.clone() for k,v in model.state_dict().items()}
        empty=data.edge_index[:,:0]
        empty_logits=model(data.x,empty)
        clean_logits=model(data.x,data.edge_index)
        for target in targets:
            case=json.loads((ROOT/f'results/full/cases/{name}_{target}_2026.json').read_text())
            label=int(clean_logits[target].argmax())
            p=float(clean_logits[target].softmax(-1)[label])
            assert abs(p-case['clean_probability'])<3e-4
            empty_rows.append(dict(dataset=name,target=target,clean_probability=p,no_edges_probability=float(empty_logits[target].softmax(-1)[label]),label_preserved=int(empty_logits[target].argmax()==label)))
            for condition in ['clean','GXAttack']:
                # Reconstruct physical graph directly from durable edge-edit records.
                active=torch.ones(data.edge_index.shape[1],dtype=torch.bool,device=data.x.device)
                adds=[];add_ids=[]
                if condition!='clean':
                    for edit in case['attacks']['GXAttack']['edits']:
                        if edit['operation']=='delete':active[int(edit['id'][1:])]=False
                        else:adds.append([edit['source'],edit['destination']]);add_ids.append(edit['id'])
                original=active.nonzero().flatten()
                edges=data.edge_index[:,active]
                if adds:edges=torch.cat([edges,torch.tensor(adds,device=edges.device).T],dim=1)
                baseline=model(data.x,edges)[target]
                graph_label=int(baseline.argmax());base_p=float(baseline.softmax(-1)[graph_label])
                nodes,local,mapping,mask=k_hop_subgraph(target,2,edges,relabel_nodes=True,num_nodes=data.num_nodes)
                local_ids=mask.nonzero().flatten()
                local_baseline=model(data.x[nodes],local)[int(mapping)]
                torch.testing.assert_close(local_baseline,baseline,atol=3e-4,rtol=3e-4)
                max_error=max(max_error,float((local_baseline-baseline).abs().max()))
                original_positions=torch.full((data.edge_index.shape[1],),-1,device=edges.device,dtype=torch.long)
                original_positions[original]=torch.arange(len(original),device=edges.device)
                scores_by_ex=case['clean_scores'] if condition=='clean' else case['attacks']['GXAttack']['scores']
                for ex in ['PGExplainer','GNNExplainer']:
                    scores=scores_by_ex[ex];rank=sorted(scores,key=lambda i:(-scores[i],i))
                    for size in ['top5','top10','top20','top25pct']:
                        k=math.ceil(.25*len(rank)) if size=='top25pct' else int(size[3:])
                        chosen=rank[:k]
                        positions=[]
                        for edge_id in chosen:
                            pos=int(original_positions[int(edge_id[1:])]) if edge_id.startswith('E') else len(original)+add_ids.index(edge_id)
                            assert pos>=0
                            positions.append(pos)
                        selected=torch.zeros(edges.shape[1],dtype=torch.bool,device=edges.device)
                        selected[positions]=True
                        assert int(selected.sum())==len(chosen)
                        removed_edges=edges[:,~selected];kept_edges=edges[:,selected]
                        assert removed_edges.shape[1]+kept_edges.shape[1]==edges.shape[1]
                        removed=model(data.x,removed_edges)[target];kept=model(data.x,kept_edges)[target]
                        local_select=selected[local_ids]
                        for full,part in [(removed,local[:,~local_select]),(kept,local[:,local_select])]:
                            result=model(data.x[nodes],part)[int(mapping)]
                            torch.testing.assert_close(result,full,atol=3e-4,rtol=3e-4)
                            max_error=max(max_error,float((result-full).abs().max()))
                        row=dict(dataset=name,target=target,condition=condition,explainer=ex,size=size,available=len(rank),selected=len(chosen),selection_fraction=len(chosen)/max(1,len(rank)),baseline_probability=base_p,fidelity_plus=int(removed.argmax()!=graph_label),fidelity_minus=int(kept.argmax()!=graph_label),soft_plus=base_p-float(removed.softmax(-1)[graph_label]),soft_minus=base_p-float(kept.softmax(-1)[graph_label]))
                        if size=='top10':
                            saved=next(r for r in case['rows'] if r['attack']=='GXAttack' and r['explainer']==ex and r['k']==10)
                            prefix='clean_' if condition=='clean' else 'attacked_'
                            for new,old in [('fidelity_plus','necessity'),('fidelity_minus','sufficiency_failure'),('soft_plus','removed_probability_drop'),('soft_minus','kept_probability_gap')]:
                                assert abs(row[new]-saved[prefix+old])<3e-4,(name,target,ex,new)
                        rows.append(row)
            save(OUT/f'{name}_{target}.json',dict(rows=[r for r in rows if r['dataset']==name and r['target']==target]))
            print(name,target,'checked',len(rows),'rows',flush=True)
        for k,v in weights.items():torch.testing.assert_close(v,model.state_dict()[k],atol=0,rtol=0)
        del data,model,b,weights,empty_logits,clean_logits
        torch.cuda.empty_cache()
    df=pd.DataFrame(rows);df.to_csv(OUT/'per_target.csv',index=False)
    summary=df.groupby(['dataset','explainer','condition','size'])[['selected','selection_fraction','fidelity_plus','fidelity_minus','soft_plus','soft_minus']].mean().reset_index()
    summary.to_csv(OUT/'summary.csv',index=False)
    er=pd.DataFrame(empty_rows);er.to_csv(OUT/'no_edges.csv',index=False)
    save(OUT/'status.json',dict(state='complete',targets=20,rows=len(rows),checks_passed=True,max_local_full_logit_error=max_error,seconds=time.time()-start))
    lines=['# Fidelity diagnostic pilot','', 'Ten reproducibly sampled eligible targets per dataset; saved trial 2026. PGExplainer and GNNExplainer, clean and GXAttack graphs. No retraining, new attacks or protocol tuning. These descriptive pilot means are not full-cohort estimates.','', '## Independent verification','',f'Physical full-graph removal/retention matched local two-hop evaluation for every selected set. Maximum absolute logit difference: {max_error:.8g}. Saved top-10 hard and soft metrics reproduced within 0.0003; model weights unchanged.','', 'Soft+ = probability before minus probability after removing explanation edges. Soft- = probability before minus probability after keeping only explanation edges. Both are signed and reference each graph\'s original predicted class; negative values mean probability increased. Hard metrics count class changes.','', '## Results','', '| Dataset | Explainer | Graph | Selection | Mean edges | Hard+ | Hard- | Soft+ | Soft- |','|---|---|---|---|---:|---:|---:|---:|---:|']
    for _,r in summary.iterrows():lines.append(f'| {r.dataset} | {r.explainer} | {r.condition} | {r["size"]} | {r.selected:.2f} | {r.fidelity_plus:.4f} | {r.fidelity_minus:.4f} | {r.soft_plus:.5f} | {r.soft_minus:.5f} |')
    lines+=['','## Removing every graph edge','', '| Dataset | Targets retaining label | Mean clean probability | Mean no-edge probability |','|---|---:|---:|---:|']
    for name,g in er.groupby('dataset'):lines.append(f'| {name} | {int(g.label_preserved.sum())}/{len(g)} | {g.clean_probability.mean():.5f} | {g.no_edges_probability.mean():.5f} |')
    lines+=['','Removing every edge leaves node features and the trained GraphSAGE root transformations intact. This is an inference-time ablation, not a separately trained feature-only baseline. HI-Small features themselves aggregate transaction activity, so it does not demonstrate independence from transaction information. Larger explanation sets are exploratory sensitivity checks, not a selected new evaluation protocol.']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')

if __name__=='__main__':run()
