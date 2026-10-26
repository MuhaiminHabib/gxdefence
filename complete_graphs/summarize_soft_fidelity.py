"""Full eligible-cohort fidelity summary and all-edge-removal ablation."""
import json
import pandas as pd
import torch
from prepare import ROOT,load,save

OUT=ROOT/'results/soft_fidelity_full'
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(ROOT/'results/full/per_target_metrics.csv')
    d=d[d.dataset.isin(['amlsim','hi_small']) & (d.attack!='Clean repeat')].copy()
    rows=[];coverage=[];ablation=[]
    for name in ['amlsim','hi_small']:
        t=json.loads((ROOT/f'results/full/{name}_targets.json').read_text())['selected']
        g=d[(d.dataset==name)&(d.attack=='GXAttack')&(d.explainer=='PGExplainer')&(d.k==10)]
        expected={(x,s) for x in t for s in range(2026,2031)}
        assert set(zip(g.target,g.trial))==expected and len(g)==len(expected)
        coverage.append(dict(dataset=name,targets=len(t),trials=5,evaluations=len(g),label_changes=int(g.delta_label.sum())))
        data,model,b=load(name)
        with torch.no_grad():
            clean=model(data.x,data.edge_index)[t]
            noedge=model(data.x,data.edge_index[:,:0])[t]
            labels=clean.argmax(1);p=clean.softmax(-1).gather(1,labels[:,None]).flatten();q=noedge.softmax(-1).gather(1,labels[:,None]).flatten()
        for i,target in enumerate(t):
            ablation.append(dict(dataset=name,target=target,clean_probability=float(p[i]),noedge_probability=float(q[i]),probability_drop=float(p[i]-q[i]),label_preserved=int(labels[i]==noedge[i].argmax())))
        del data,model,b;torch.cuda.empty_cache()
        print(name,'coverage and all-edge ablation complete',flush=True)
    cols={'hard_plus':'necessity','hard_minus':'sufficiency_failure','soft_plus':'removed_probability_drop','soft_minus':'kept_probability_gap'}
    for (name,attack,ex,k),g in d.groupby(['dataset','attack','explainer','k']):
        for condition in ['clean','attacked']:
            for metric,suffix in cols.items():
                col=condition+'_'+suffix
                assert g[col].notna().all()
                v=g[col];means=g.groupby('trial')[col].mean()
                preserved=g[g.target_lp==1].groupby('trial')[col].mean()
                rows.append(dict(dataset=name,attack=attack,explainer=ex,k=int(k),condition=condition,metric=metric,mean=float(means.mean()),trial_sd=float(means.std()),n=len(v),unique_targets=g.target.nunique(),mean_absolute=float(v.abs().mean()),negative_fraction=float((v < -1e-6).mean()),positive_fraction=float((v > 1e-6).mean()),median=float(v.median()),q05=float(v.quantile(.05)),q95=float(v.quantile(.95)),preserved_only_mean=float(preserved.mean())))
    r=pd.DataFrame(rows);r.to_csv(OUT/'summary.csv',index=False)
    a=pd.DataFrame(ablation);a.to_csv(OUT/'no_edges_per_target.csv',index=False)
    save(OUT/'coverage.json',coverage)
    lines=['# Full-cohort hard and soft fidelity: AMLSim and HI-Small','', 'All existing eligible test targets, five saved trials. No attack rerun or model retraining. Full saved-metric aggregation; the earlier independent physical-edge audit remains a 20-target pilot. Every eligible target is included in the new all-edge-removal ablation.','', 'Soft+ is the signed baseline probability minus the probability after removing explanation edges. Soft- is the signed baseline probability minus the probability after retaining explanation edges. Each graph uses its own predicted class as reference. Negative values indicate increased probability, not an error. Mean absolute changes and signed distributions are saved to expose cancellation.','', '## Coverage','', '| Dataset | Targets | Trials | Evaluations | GXAttack label changes |','|---|---:|---:|---:|---:|']
    for c in coverage:lines.append(f'| {c["dataset"]} | {c["targets"]} | 5 | {c["evaluations"]} | {c["label_changes"]} |')
    lines+=['','## GXAttack: clean versus attacked','', 'Means +/- sample SD across the five trial means. PG/GNN use top-10 capped by available edges; SubgraphX uses its native set. Soft values below are percentage points. Hard values below are percentages of class changes.','', '| Dataset | Explainer | Metric | Clean | Attacked |','|---|---|---|---:|---:|']
    for name in ['amlsim','hi_small']:
        for ex in ['PGExplainer','GNNExplainer','SubgraphX']:
            for metric in cols:
                vals=[]
                for condition in ['clean','attacked']:
                    x=r[(r.dataset==name)&(r.attack=='GXAttack')&(r.explainer==ex)&(r.k==(0 if ex=='SubgraphX' else 10))&(r.condition==condition)&(r.metric==metric)].iloc[0]
                    vals.append(f'{100*x["mean"]:.4f} +/- {100*x.trial_sd:.4f}')
                lines.append('| '+name+' | '+ex+' | '+metric+' | '+' | '.join(vals)+' |')
    lines+=['','## All-edge-removal ablation','', 'One deterministic evaluation per unique target with the frozen model; node features are retained.','', '| Dataset | Labels preserved | Mean clean illicit probability | Mean no-edge illicit probability | Mean probability drop (pp) |','|---|---:|---:|---:|---:|']
    for name,g in a.groupby('dataset'):lines.append(f'| {name} | {g.label_preserved.sum()}/{len(g)} | {100*g.clean_probability.mean():.3f}% | {100*g.noedge_probability.mean():.3f}% | {100*g.probability_drop.mean():.3f} |')
    lines+=['','## Explanation-size sensitivity','', 'GXAttack/PGExplainer means; soft metrics in percentage points, hard necessity in percent.','', '| Dataset | k | Clean hard+ | Attacked hard+ | Clean soft+ | Attacked soft+ |','|---|---:|---:|---:|---:|']
    for name in ['amlsim','hi_small']:
        for k in [5,10,20]:
            vals=[]
            for metric in ['hard_plus','soft_plus']:
                for condition in ['clean','attacked']:
                    x=r[(r.dataset==name)&(r.attack=='GXAttack')&(r.explainer=='PGExplainer')&(r.k==k)&(r.condition==condition)&(r.metric==metric)].iloc[0]
                    vals.append(f'{100*x["mean"]:.4f}')
            lines.append(f'| {name} | {k} | '+' | '.join(vals)+' |')
    lines+=['','## Interpretation limits','', 'The saved full experiment contains fidelity for fixed k=5/10/20 and native SubgraphX sets. Top-25% fidelity remains pilot-only; binary top-25% similarity is a different metric. Summary CSV includes random baselines, signed distributions, mean absolute values and prediction-preserved-only results.','', 'No-edge ablation retains transaction-derived features (including HI-Small aggregate features) and learned root transformations. It is not a separately trained feature-only model and does not establish independence from transaction information. Low soft means can hide opposing effects; inspect distributions. The eligible cohort is not the whole test population. Neither fidelity nor similarity establishes human-investigator deception.']
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
    save(OUT/'status.json',dict(state='complete',coverage=coverage,full_edge_removal_audit=False,all_target_noedge_ablation=True))
if __name__=='__main__':run()
