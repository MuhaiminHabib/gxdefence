"""Two GraphSAGE case reports with fixed classifier weights and five explainer seeds."""
import argparse
import contextlib
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
SEEDS = [2026, 2027, 2028, 2029, 2030]

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

def seed_all(seed):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def subgraphx_worker(folder):
    import numpy as np
    import torch
    import dgl
    from dgl.nn.pytorch.explain import SubgraphX
    from src.models.marasi_models import MarasiGraphSAGE
    torch.set_num_threads(2)
    bundle = torch.load(folder / 'context.pt', map_location='cpu', weights_only=False)
    model = MarasiGraphSAGE(bundle['x'].shape[1], bundle['hidden'])
    model.load_state_dict(bundle['state_dict'], strict=True)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    x, edge = bundle['x'], bundle['edge_index']
    graph = dgl.graph((edge[0], edge[1]), num_nodes=len(x))
    class Adapter(torch.nn.Module):
        def forward(self, graph, features):
            return model(features, edge)[bundle['target']:bundle['target']+1]
    adapter = Adapter().eval()
    with torch.no_grad():
        logits = adapter(graph, x)[0]
    torch.testing.assert_close(logits, bundle['baseline_logits'], atol=1e-4, rtol=1e-4)
    result = []
    for seed in SEEDS:
        seed_all(seed)
        algorithm = SubgraphX(adapter, num_hops=2, num_child=6,
            num_rollouts=5, node_min=3, shapley_steps=5, log=False)
        chosen = algorithm.explain_graph(graph, x, target_class=bundle['illicit'])
        nodes = sorted(int(n) for n in chosen.tolist())
        chosen_set = set(nodes)
        selected = [int(bundle['edge_ids'][i]) for i, (a,b) in enumerate(edge.t().tolist())
                    if a in chosen_set and b in chosen_set]
        result.append(dict(seed=seed, selection=selected,
            selected_nodes=[int(bundle['node_ids'][n]) for n in nodes]))
        print('SubgraphX seed', seed, 'selected', len(nodes), 'nodes,', len(selected), 'edges', flush=True)
    write_json(folder / 'subgraphx.json', result)

def load_dataset(name, folder, device):
    import torch
    if name == 'amlsim':
        from src.data.ibm_amlsim_prev_reproduction import build_ibm_amlsim_graph
        from scripts.run_ibm_amlsim_prev_reproduction import build_model
        path = ROOT / 'outputs/baseline_check_20260929_105205/ibm_amlsim/ibm_amlsim_prev_reproduction_graphsage_seed42_model.pt'
        cp = torch.load(path, map_location='cpu', weights_only=False)
        data = build_ibm_amlsim_graph(ROOT / 'data/raw/ibm_amlsim', seed=42,
            include_fraud_tx_count_features=False, include_categorical_features=False)
        model = build_model('GraphSAGE', data.num_features)
        model.load_state_dict(cp['state_dict'], strict=True)
        return data.to(device), model.to(device), 1, 64, path, cp['metrics']
    import run_marasi_5seed as baseline
    from src.models.marasi_models import MarasiGraphSAGE
    load, pyg, upstream = baseline.load_upstream_components()
    features, edges = load(str(ROOT / 'data/raw/elliptic'), noAgg=False)
    baseline.seed_everything(42)
    data = pyg(features.copy(), edges.copy()).to(device)
    trained = baseline.build_model('graphsage', upstream, data.num_features).to(device)
    retained = ROOT / 'outputs/graphsage_explanations_seed42_v1/elliptic/graphsage_seed42_new_checkpoint.pt'
    if retained.exists():
        cp = torch.load(retained, map_location=device, weights_only=False)
        trained.load_state_dict(cp['state_dict'], strict=True)
        trained.eval()
        metrics, path = cp['metrics'], retained
    else:
        baseline.train_model(trained, data, baseline.EPOCHS)
        metrics = baseline.evaluate(trained, data)
        path = folder / 'graphsage_seed42_new_checkpoint.pt'
        torch.save(dict(state_dict={k:v.cpu() for k,v in trained.state_dict().items()},
            seed=42, model='graphsage', metrics=metrics,
            provenance='New training run: earlier comparison runner did not retain Elliptic weights.'), path)
    model = MarasiGraphSAGE(data.num_features, 110).to(device)
    model.load_state_dict(trained.state_dict(), strict=True)
    model.eval()
    with torch.no_grad():
        torch.testing.assert_close(model(data.x, data.edge_index), trained((data.x, data.edge_index))[0])
    print('Elliptic NEW checkpoint test metrics:', metrics, flush=True)
    return data, model, 0, 110, path, metrics

def run_case(name, run, dgl_python):
    import numpy as np
    import torch
    from torch_geometric.utils import k_hop_subgraph
    import run_gnnexplainer_shared_model as gx
    import run_pgexplainer_shared_model as px
    from faithfulness_report import render_approved_report
    folder = run / name
    folder.mkdir()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data, model, illicit, hidden, checkpoint, metrics = load_dataset(name, folder, device)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    frozen = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    with torch.no_grad():
        full_logits = model(data.x, data.edge_index)
        targets = full_logits.argmax(1)
        probabilities = full_logits.softmax(1)[:, illicit]
    candidates = (data.val_mask & (data.y == illicit) & (targets == illicit)).nonzero().flatten().tolist()
    chosen = None
    for target in candidates:
        nodes, local_edges, mapping, edge_mask = k_hop_subgraph(target, 2, data.edge_index,
            relabel_nodes=True, num_nodes=data.num_nodes, flow='source_to_target')
        if 4 <= len(nodes) <= 100 and 2 <= local_edges.shape[1] <= 2000:
            chosen = target, nodes, local_edges, int(mapping.item()), edge_mask.nonzero().flatten()
            break
    if chosen is None:
        raise RuntimeError('No correctly detected illicit validation target with 4-100 context nodes and 2-2000 edges; do not silently change selection protocol.')
    target, nodes, local_edges, local_target, edge_ids = chosen
    x = data.x[nodes]
    with torch.no_grad():
        local_logits = model(x, local_edges)[local_target]
    torch.testing.assert_close(local_logits, full_logits[target], atol=1e-4, rtol=1e-4)
    baseline = float(probabilities[target])
    print(name, 'target model index', target, 'context', len(nodes), 'nodes', len(edge_ids), 'edges; probability', baseline, flush=True)
    bundle = dict(x=x.cpu(), edge_index=local_edges.cpu(), target=local_target,
        node_ids=nodes.cpu(), edge_ids=edge_ids.cpu(), hidden=hidden,
        state_dict=frozen, baseline_logits=full_logits[target].cpu(), illicit=illicit)
    torch.save(bundle, folder / 'context.pt')
    packet = dict(target=target, baseline=baseline, edges={}, rankings={},
        report=dict(rows=[], choices=[], stability=[]),
        model_note='Frozen seed-42 GraphSAGE. Node IDs are model indices. Full-graph physical edge removal/keep; features and GraphSAGE root transformations fixed. Parallel transaction rows remain distinct.',
        dataset=name, checkpoint=str(checkpoint), checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        model_metrics=metrics, explainer_seeds=SEEDS,
        selection_protocol='First model-index-ordered correctly detected illicit validation node with 4-100 nodes and 2-2000 edges in its incoming 2-hop context. Demonstration, not a representative benchmark.',
        explanation_protocol='GNNExplainer on verified incoming 2-hop context; PGExplainer fitted on full-graph training nodes; SubgraphX fixed-context feature coalitions. Full/local baseline logits verified. PG stability includes independent fits.',
        failures=[])
    def label(edge_id):
        key = 'E' + str(edge_id)
        a,b = data.edge_index[:,edge_id].tolist()
        packet['edges'][key] = dict(source=a, destination=b, edge_id=edge_id)
        return key
    def add_ranking(method, seed, scores):
        if not torch.isfinite(scores).all():
            raise ValueError('Nonfinite explanation scores')
        order = sorted(range(len(edge_ids)), key=lambda i: (-float(scores[i]), int(edge_ids[i])))
        # Persist only the top two scores required by the report; no giant ranking dumps.
        order = order[:2]
        ranking = [label(int(edge_ids[i])) for i in order]
        packet['rankings'].setdefault(method,{})[str(seed)] = dict(ranking=ranking,
            scores={label(int(edge_ids[i])):float(scores[i]) for i in order})
        for k in (1,2):
            packet['report']['choices'].append(dict(method=method, seed=seed, budget=k,
                selection=ranking[:k], control=None))
    for seed in SEEDS:
        seed_all(seed)
        explanation = gx.make_explainer(model)(x, local_edges, index=local_target)
        add_ranking('GNNExplainer', seed, explanation.edge_mask.detach())
        print(name, 'GNNExplainer', seed, 'complete', flush=True)
    px.ILLICIT_LABEL = illicit
    # PG's mean edge entropy is undefined for an empty incoming context.
    # Restrict fit nodes to those with at least one incoming edge, without
    # changing the classifier, split membership, or evaluation target.
    original_train_mask = data.train_mask.clone()
    incoming = torch.bincount(data.edge_index[1], minlength=data.num_nodes)
    data.train_mask = original_train_mask & (incoming > 0)
    train_nodes = px.select_pgexplainer_training_nodes(model, data, 'graphsage', px.NUM_EXPLAINER_TRAIN_NODES)
    data.train_mask = original_train_mask
    packet['pg_training_nodes'] = train_nodes
    packet['pg_training_filter'] = 'Original confidence/correctness/training split criteria, with empty incoming contexts excluded to avoid undefined edge entropy.'
    write_json(folder / 'report_input_partial.json', packet)
    for seed in SEEDS:
        seed_all(seed)
        explainer = px.make_pgexplainer(model, device)
        # Use the copied algorithm and its unchanged learning rate/epoch count.
        # Fail on invalid updates rather than silently accepting skipped fits.
        for epoch in range(px.PG_EXPLAINER_EPOCHS):
            losses = []
            for node in train_nodes:
                loss = explainer.algorithm.train(epoch, model, data.x, data.edge_index,
                    target=targets, index=node)
                if not np.isfinite(loss):
                    raise RuntimeError('Nonfinite PGExplainer training loss')
                losses.append(float(loss))
            if epoch % 5 == 0:
                print(name, 'PGExplainer', seed, 'epoch', epoch, 'loss', np.mean(losses), flush=True)
        explanation = explainer(data.x, data.edge_index, target=targets, index=target)
        add_ranking('PGExplainer', seed, explanation.edge_mask.detach()[edge_ids])
        torch.save(explainer.algorithm.state_dict(), folder / f'pg_seed{seed}.pt')
        del explainer, explanation
    with (folder / 'subgraphx.log').open('w', encoding='utf-8') as log:
        result = subprocess.run([dgl_python, '-u', '-B', str(Path(__file__).resolve()),
            '--subgraphx-worker', str(folder)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    if result.returncode:
        raise RuntimeError('SubgraphX worker failed; see subgraphx.log')
    for row in json.loads((folder / 'subgraphx.json').read_text()):
        selected = [label(e) for e in row['selection']]
        packet['report']['choices'].append(dict(method='SubgraphX_induced_edges', seed=row['seed'],
            budget=len(selected), selection=selected, selected_nodes=row['selected_nodes'], control=None))
    selections = {tuple(sorted(c['selection'])) for c in packet['report']['choices']}
    selections.add(tuple())
    for selection in sorted(selections, key=lambda s:(len(s),s)):
        ids = [packet['edges'][key]['edge_id'] for key in selection]
        keep = torch.zeros(data.num_edges, dtype=torch.bool, device=device)
        keep[ids] = True
        with torch.no_grad():
            removed_logits = model(data.x, data.edge_index[:,~keep])[target]
            kept_logits = model(data.x, data.edge_index[:,keep])[target]
        removed = float(removed_logits.softmax(0)[illicit])
        kept = float(kept_logits.softmax(0)[illicit])
        packet['report']['rows'].append(dict(selection=list(selection),
            original_illicit_probability=baseline, removed_illicit_probability=removed,
            kept_illicit_probability=kept, signed_drop_pp=100*(baseline-removed),
            signed_gap_pp=100*(baseline-kept), fidelity_gnn_acc=int(removed_logits.argmax()!=illicit),
            fidelity_gnn_acc_inv=int(kept_logits.argmax()!=illicit)))
    lookup = {tuple(sorted(r['selection'])):r for r in packet['report']['rows']}
    for choice in packet['report']['choices']:
        choice['metrics'] = lookup[tuple(sorted(choice['selection']))]
    for method in ('GNNExplainer','PGExplainer','SubgraphX_induced_edges'):
        for budget in ([1,2] if method != 'SubgraphX_induced_edges' else [None]):
            choices = [c for c in packet['report']['choices'] if c['method']==method and (budget is None or c['budget']==budget)]
            sets = [set(c['selection']) for c in choices]
            jaccards = [len(a&b)/len(a|b) if a|b else 1.0 for a,b in itertools.combinations(sets,2)]
            packet['report']['stability'].append(dict(method=method,budget=budget,runs=len(sets),
                edge_jaccard_mean=float(np.mean(jaccards)),selected_sizes=[len(s) for s in sets]))
    for key,value in model.state_dict().items():
        assert torch.equal(frozen[key],value.cpu()), 'Classifier weights changed'
    write_json(folder / 'report_input.json',packet)
    with contextlib.redirect_stdout(io.StringIO()):
        lines,_ = render_approved_report(target,baseline,packet['edges'],packet['report'],
            packet['rankings'],folder/'report_input.json',packet['model_note'])
    lines = ['Dataset: '+name+' | GraphSAGE | model seed 42',packet['selection_protocol'],
             packet['explanation_protocol'],''] + lines
    (folder/'readable_results.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(name,'report complete',flush=True)
    del data,model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--subgraphx-worker',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--dgl-python')
    args=parser.parse_args()
    if args.subgraphx_worker:
        subgraphx_worker(args.subgraphx_worker)
        return
    import torch
    torch.set_num_threads(4)
    run=args.output.resolve()
    run.mkdir(parents=True,exist_ok=False)
    failures=[]
    for name in ('elliptic','amlsim'):
        write_json(run/'status.json',dict(state='running',dataset=name,failures=failures))
        try:
            run_case(name,run,args.dgl_python)
        except Exception:
            error=traceback.format_exc()
            print(error,flush=True)
            failures.append(dict(dataset=name,error=error))
    write_json(run/'status.json',dict(state='failed' if failures else 'complete',failures=failures))

if __name__=='__main__':
    main()
