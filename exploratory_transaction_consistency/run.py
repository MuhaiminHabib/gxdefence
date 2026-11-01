"""Isolated transaction-consistency replay and matched SubgraphX search pilot."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import argparse
import copy
import ctypes
import hashlib
import json
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import torch
from torch_geometric.utils import k_hop_subgraph

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
sys.path.insert(0, str(STUDY / 'complete_graphs'))
from prepare import MarasiGraphSAGE, save, sha
from features import Records
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
if os.name == 'nt':
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)

OUT = ROOT / 'results'
CONFIG = dict(datasets=['amlsim', 'hi_small'], targets_per_dataset=20, subset_seed=173205,
              budget=6, proposals=40, selection_seed=93001,
              evaluation_seeds=list(range(94001, 94006)), repeat_seeds=list(range(95001, 95006)),
              probability_cap=.02, random_masks=20, bootstrap_draws=5000,
              expansion_targets=50, expansion_trials=[1,2], minimum_expansion_effect=.10,
              scenarios=['frozen', 'refreshed'], subgraphx=dict(num_hops=2, num_child=6,
              num_rollouts=5, shapley_steps=5, node_min=3))
DGL_PY = r'D:\habib dissertation\Projects\AML-GNN-Replication-v2\.venv-subgraphx\Scripts\python.exe'
METHODS = ['Replay adaptive', 'Replay random search', 'Search frozen', 'Search refreshed', 'First random']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sources():
    paths = [Path(__file__), ROOT/'features.py', ROOT/'README.md',
             STUDY/'complete_graphs/prepare.py', STUDY/'complete_graphs/subgraph_worker.py',
             STUDY/'framework/src/models/marasi_models.py',
             STUDY/'framework/src/data/ibm_amlsim_prev_reproduction.py']
    return {str(p.relative_to(STUDY)): sha(p) for p in paths}


def manifest():
    old = json.loads((STUDY/'deletion_access/results/manifest.json').read_text())
    rng = random.Random(CONFIG['subset_seed'])
    targets = {n: sorted(rng.sample(sorted(old['targets'][n]), CONFIG['targets_per_dataset']))
               for n in CONFIG['datasets']}
    paths = [STUDY/'deletion_access/results/manifest.json']; expanded = {}; census = {}
    for n in CONFIG['datasets']:
        paths.append(STUDY/f'complete_graphs/prepared/{n}.pt')
        for t in targets[n]:
            paths.append(STUDY/f'deletion_access/results/full/cases/{n}_{t}_2026.json')
        for t in old['pilot'][n]:
            paths.append(STUDY/f'deletion_access/results/pilot/cases/{n}_{t}_2026.json')
        census_path = STUDY/f'complete_graphs/results/full/{n}_targets.json'
        paths.append(census_path)
        bundle = torch.load(STUDY/f'complete_graphs/prepared/{n}.pt', map_location='cpu', weights_only=False)
        eligible = []
        for t in sorted(json.loads(census_path.read_text())['selected']):
            if t in targets[n] or t in old['pilot'][n]:
                continue
            p = STUDY/f'gnn_three_trials/results/full/cases/{n}_{t}_2026.json'
            scores = json.loads(p.read_text())['clean']['GNNExplainer']
            rows = torch.tensor([int(v[1:]) for v in scores], dtype=torch.long)
            edges = bundle['data'].edge_index[:, rows]
            if int((edges[0]!=edges[1]).sum()) >= CONFIG['budget']:
                eligible.append(t)
        assert len(eligible) >= CONFIG['expansion_targets']
        expanded[n] = sorted(rng.sample(eligible, CONFIG['expansion_targets']))
        census[n] = dict(remaining_feasible=len(eligible), candidate_targets=eligible)
        for t in expanded[n]:
            paths.append(STUDY/f'gnn_three_trials/results/full/cases/{n}_{t}_2026.json')
        del bundle
    raw = STUDY/'framework/data/raw/ibm_amlsim'
    paths.extend([raw/'accounts.csv', raw/'transactions.csv'])
    meta = STUDY/'complete_graphs/prepared/hi_small_provenance.json'
    paths.extend([meta, Path(json.loads(meta.read_text())['source']),
                  STUDY/'complete_graphs/prepared/hi_small_account_ids.npy'])
    d = dict(config=CONFIG, targets=targets, expanded_targets=expanded, expansion_census=census,
             validation_targets=old['pilot'], sources=sources(),
             inputs={str(p): sha(p) for p in paths}, torch=torch.__version__,
             pyg=__import__('torch_geometric').__version__)
    return d


class Worker:
    def __init__(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        self.folder = folder
        self.log = open(folder/'subgraphx_stderr.log', 'a', encoding='utf8')
        flags = (subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name == 'nt' else 0
        self.p = subprocess.Popen([DGL_PY, '-u', str(STUDY/'complete_graphs/subgraph_worker.py')],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                                  text=True, creationflags=flags)

    def explain(self, model, g, seed, hidden):
        path = self.folder/'worker_context.pt'
        torch.save(dict(x=g['x'].cpu(), edge=g['edge'].cpu(), target=g['target'], hidden=hidden,
                        state={k: v.detach().cpu() for k, v in model.state_dict().items()},
                        nodes=torch.tensor(g['nodes']), ids=[f'E{v}' for v in g['ids']],
                        logits=g['logits'].cpu(), label=g['label']), path)
        self.p.stdin.write(json.dumps(dict(path=str(path), seed=seed))+'\n')
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError('SubgraphX worker exited; inspect its isolated log')
        result = json.loads(line)
        if 'error' in result:
            raise RuntimeError(result['error'])
        ids = sorted(int(v[1:]) for v in result['ids'])
        assert set(ids) <= set(g['ids'])
        return dict(ids=ids, nodes=result['nodes'])

    def close(self):
        self.p.stdin.close()
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.p.terminate(); self.p.wait(timeout=10)
        self.log.close()


class Context:
    def __init__(self, records, model, target):
        self.records, self.model, self.target = records, model, target
        data = records.data
        nodes, edge, mapping, mask = k_hop_subgraph(target, 2, data.edge_index,
                                                   relabel_nodes=True, num_nodes=data.num_nodes)
        self.nodes, self.edge, self.mapping = nodes, edge, int(mapping)
        self.ids = mask.nonzero().flatten().numpy()
        self.allowed = self.ids[(edge[0] != edge[1]).numpy()].tolist()
        assert len(self.allowed) >= 6
        self.feature_cache = {}
        # Validate incident-record reconstruction for the whole candidate node domain.
        rebuilt = torch.from_numpy(np.stack([records.vector(int(n), set()) for n in nodes]))
        torch.testing.assert_close(rebuilt, data.x[nodes], atol=3e-5, rtol=3e-5)
        self.clean_local_feature_error = float((rebuilt-data.x[nodes]).abs().max())

    @torch.no_grad()
    def graph(self, removed, scenario):
        removed = set(removed)
        assert removed <= set(self.allowed)
        keep = ~np.isin(self.ids, list(removed))
        node_ids, edge, mapping, mask = k_hop_subgraph(self.mapping, 2, self.edge[:, keep],
                                                     relabel_nodes=True, num_nodes=len(self.nodes))
        nodes = self.nodes[node_ids].tolist()
        ids = self.ids[keep][mask.numpy()].tolist()
        x = (self.records.data.x[nodes] if scenario == 'frozen'
             else self.records.features(nodes, removed))
        x, edge = x.to('cuda'), edge.to('cuda')
        logits = self.model(x, edge)[int(mapping)]
        assert torch.isfinite(logits).all()
        return dict(x=x, edge=edge, target=int(mapping), nodes=nodes, ids=ids,
                    removed=sorted(removed), scenario=scenario, logits=logits,
                    label=int(logits.argmax()))

    @torch.no_grad()
    def fidelity(self, g, selected):
        selected = set(selected)
        assert selected <= set(g['ids'])
        mask = torch.tensor([v in selected for v in g['ids']], device='cuda')
        label = g['label']; base = float(g['logits'].softmax(-1)[label])
        output = {}
        # A record intervention has a coherent baseline only when features already
        # correspond to the current record set. Avoid folding a refresh-only shift
        # into the measured effect of deleting explanatory records.
        modes = ('edge', 'record') if g['scenario']=='refreshed' or not g['removed'] else ('edge',)
        for mode in modes:
            if mode == 'edge':
                removed_x = retained_x = g['x']
            else:
                removed_x = self.records.features(g['nodes'], set(g['removed']) | selected).to('cuda')
                retained_x = self.records.features(g['nodes'], set(), retained=selected).to('cuda')
            removed = self.model(removed_x, g['edge'][:, ~mask])[g['target']]
            retained = self.model(retained_x, g['edge'][:, mask])[g['target']]
            output[mode] = dict(hard_plus=int(removed.argmax()) != label,
                                hard_minus=int(retained.argmax()) != label,
                                soft_plus=base-float(removed.softmax(-1)[label]),
                                soft_minus=base-float(retained.softmax(-1)[label]))
        return output


def overlap(a, b):
    a, b = set(a), set(b)
    sim = len(a & b)/(len(a)*len(b))**.5 if a and b else float(not a and not b)
    jac = len(a & b)/len(a | b) if a or b else 1.
    return dict(similarity=sim, jaccard=jac, clean_size=len(a), attacked_size=len(b),
                clean_empty=int(not a), attacked_empty=int(not b))


def preservation(g, label, probability):
    dp = abs(float(g['logits'].softmax(-1)[label])-probability)
    preserved = int(g['label'] == label)
    return dict(preserved=preserved, delta_prob=dp, feasible=int(preserved and dp <= CONFIG['probability_cap']))


def rank(r):
    return r['preserved'], r['feasible'], 1-r['similarity']


def load(name):
    b = torch.load(STUDY/f'complete_graphs/prepared/{name}.pt', map_location='cpu', weights_only=False)
    model = MarasiGraphSAGE(b['data'].num_features, b['hidden']).to('cuda')
    model.load_state_dict(b['state']); model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    print('RECONSTRUCT', name, flush=True)
    rec = Records(name, b['data'])
    print('RECONSTRUCTED', name, 'max_clean_error', rec.clean_max_error, flush=True)
    return b, model, rec


def full_check(rec, model, ctx, removed, scenario, retained=None):
    """Independent full raw rebuild and full graph model; only for technical validation."""
    if retained is None:
        keep = torch.ones(rec.edges.shape[1], dtype=torch.bool)
        keep[list(removed)] = False
        edges = rec.data.edge_index[:, keep]
    else:
        edges = rec.data.edge_index[:, sorted(retained)]
    ref_x = rec.data.x if scenario == 'frozen' else rec.full_reference(set(removed), retained)
    if scenario == 'refreshed':
        affected = (np.unique(rec.edges[:, sorted(removed)]) if retained is None
                    else np.asarray(ctx.nodes))
        fast = rec.features(affected, set(removed), retained)
        torch.testing.assert_close(fast, ref_x[affected], atol=3e-5, rtol=3e-5)
        if retained is None:
            rebuilt = rec.data.x.clone(); rebuilt[affected] = fast
            torch.testing.assert_close(rebuilt, ref_x, atol=3e-5, rtol=3e-5)
    cpu = copy.deepcopy(model).cpu().eval()
    with torch.no_grad():
        full = cpu(ref_x, edges)[ctx.target]
    del cpu
    return full


def validate_one(name, target, b, model, rec, worker):
    begin = time.time(); ctx = Context(rec, model, target)
    old = json.loads((STUDY/f'deletion_access/results/pilot/cases/{name}_{target}_2026.json').read_text())
    edits = [int(v[1:]) for v in old['attacks']['deletion_only']['Adaptive search']['edge_ids']]
    clean = ctx.graph([], 'frozen')
    native = worker.explain(model, clean, 2026, b['hidden'])
    assert {f'E{i}' for i in native['ids']} == set(old['clean']), 'Clean native SubgraphX parity failed'
    attacked = ctx.graph(edits, 'frozen')
    native_attack = worker.explain(model, attacked, 2026, b['hidden'])
    assert {f'E{i}' for i in native_attack['ids']} == set(old['attacks']['deletion_only']['Adaptive search']['scores'])
    max_prediction_error = 0.
    for scenario in CONFIG['scenarios']:
        for removed in ([], edits):
            g = ctx.graph(removed, scenario)
            full = full_check(rec, model, ctx, removed, scenario)
            torch.testing.assert_close(g['logits'].cpu(), full, atol=3e-4, rtol=3e-4)
            max_prediction_error = max(max_prediction_error, float((g['logits'].cpu()-full).abs().max()))
    # Independently verify both fidelity interventions on the refreshed attacked graph.
    g = ctx.graph(edits, 'refreshed')
    selected = set(g['ids'][:min(10, len(g['ids']))])
    fids = ctx.fidelity(g, selected)
    base = float(g['logits'].softmax(-1)[g['label']])
    for operation in ('remove', 'retain'):
        if operation == 'remove':
            full = full_check(rec, model, ctx, set(edits)|selected, 'refreshed')
            metric = 'soft_plus'
        else:
            full = full_check(rec, model, ctx, set(), 'refreshed', retained=selected)
            metric = 'soft_minus'
        expected = base-float(full.softmax(-1)[g['label']])
        assert abs(fids['record'][metric]-expected) < 3e-5
    for k, v in b['state'].items():
        torch.testing.assert_close(model.state_dict()[k].cpu(), v, atol=0, rtol=0)
    return dict(dataset=name, target=target, seconds=time.time()-begin,
                clean_full_feature_max_error=rec.clean_max_error,
                clean_incident_feature_max_error=ctx.clean_local_feature_error,
                full_local_prediction_max_error=max_prediction_error,
                changed_features_full_rebuild_parity=True, record_fidelity_full_rebuild_parity=True,
                original_subgraphx_clean_and_attack_parity=True, frozen_weights=True)


def one_case(name, target, b, model, rec, worker, mid, trial=0):
    begin = time.time(); ctx = Context(rec, model, target)
    old_path = (STUDY/f'deletion_access/results/full/cases/{name}_{target}_2026.json' if trial==0
                else STUDY/f'gnn_three_trials/results/full/cases/{name}_{target}_2026.json')
    old = json.loads(old_path.read_text())
    clean = ctx.graph([], 'frozen'); label = clean['label']
    probability = float(clean['logits'].softmax(-1)[label])
    if trial==0:
        assert label == old['clean_label'] and abs(probability-old['clean_probability']) < 3e-4
        native = worker.explain(model, clean, 2026, b['hidden'])
        assert {f'E{i}' for i in native['ids']} == set(old['clean'])
    else:
        assert label == b['illicit'] and int(rec.data.y[target]) == b['illicit']
        assert {f'E{i}' for i in clean['ids']} == set(old['clean']['GNNExplainer'])
    selection_seed = CONFIG['selection_seed']+trial
    evaluation_seeds = CONFIG['evaluation_seeds'] if trial==0 else list(range(96001+(trial-1)*100,96006+(trial-1)*100))
    repeat_seeds = CONFIG['repeat_seeds'] if trial==0 else [s+10000 for s in evaluation_seeds]
    clean_selection = worker.explain(model, clean, selection_seed, b['hidden'])
    rng = random.Random(1000003*target + (0 if name == 'amlsim' else 314159) + selection_seed)
    pool = [sorted(rng.sample(ctx.allowed, CONFIG['budget'])) for _ in range(CONFIG['proposals'])]
    candidates = []; memo = {}
    for i, edits in enumerate(pool):
        key = tuple(edits)
        for scenario in CONFIG['scenarios']:
            if (key, scenario) not in memo:
                g = ctx.graph(edits, scenario)
                scores = worker.explain(model, g, selection_seed, b['hidden'])
                memo[key, scenario] = dict(edits=edits, scenario=scenario, explanation=scores,
                                          **overlap(clean_selection['ids'], scores['ids']),
                                          **preservation(g, label, probability))
            candidates.append(dict(proposal=i+1, **memo[key, scenario]))
        if (i+1) % 10 == 0:
            print(name, target, 'matched proposals', i+1, flush=True)
    chosen = {
        'Search frozen': max((r for r in candidates if r['scenario']=='frozen'), key=rank)['edits'],
        'Search refreshed': max((r for r in candidates if r['scenario']=='refreshed'), key=rank)['edits'],
        'First random': pool[0]}
    if trial==0:
        chosen.update({
            'Replay adaptive': [int(v[1:]) for v in old['attacks']['deletion_only']['Adaptive search']['edge_ids']],
            'Replay random search': [int(v[1:]) for v in old['attacks']['deletion_only']['Random search']['edge_ids']]})
    assert all(len(set(v)) == 6 and set(v) <= set(ctx.allowed) for v in chosen.values())
    graphs = {(tuple(sorted(edits)), scenario): ctx.graph(edits, scenario)
              for edits in chosen.values() for scenario in CONFIG['scenarios']}
    evidence = {}; rows = []; fidelity_rows = []; random_evidence = []; fid_memo = {}

    def fid(g, selected):
        key = (tuple(g['removed']), g['scenario'], tuple(sorted(selected)))
        if key not in fid_memo:
            fid_memo[key] = ctx.fidelity(g, selected)
        return fid_memo[key]

    def evaluate_fidelity(method, scenario, g, scores, s):
        selected = scores['ids']; f = fid(g, selected)
        rseed = int(digest([name, target, method, scenario, s])[:8], 16)
        random_rng = random.Random(rseed)
        sets = [sorted(random_rng.sample(g['ids'], len(selected))) for _ in range(CONFIG['random_masks'])]
        controls = [fid(g, v) for v in sets]
        random_evidence.append(dict(method=method, scenario=scenario, seed=s,
                                    random_seed=rseed, selected_size=len(selected), pool_size=len(g['ids']),
                                    edge_sets=sets, fidelities=controls))
        for mode in f:
            row = dict(dataset=name, target=target, method=method, scenario=scenario, seed=s,
                       intervention=mode, selected_size=len(selected), predicted_class=g['label'],
                       **preservation(g, label, probability))
            for metric in ('hard_plus', 'hard_minus', 'soft_plus', 'soft_minus'):
                average = float(np.mean([r[mode][metric] for r in controls]))
                row[metric] = float(f[mode][metric])
                row['random_'+metric] = average
                row['excess_'+metric] = float(f[mode][metric])-average
            fidelity_rows.append(row)

    for s, repeat_seed in zip(evaluation_seeds, repeat_seeds):
        clean_scores = worker.explain(model, clean, s, b['hidden'])
        repeat = worker.explain(model, clean, repeat_seed, b['hidden'])
        repeat_metrics = overlap(clean_scores['ids'], repeat['ids'])
        scores_memo = {}
        evaluate_fidelity('Clean', 'frozen', clean, clean_scores, s)
        stage = dict(clean=clean_scores, clean_repeat=repeat, attacks={})
        for method, edits in chosen.items():
            stage['attacks'][method] = {}
            for scenario in CONFIG['scenarios']:
                key = tuple(sorted(edits)), scenario
                g = graphs[key]
                if key not in scores_memo:
                    scores_memo[key] = worker.explain(model, g, s, b['hidden'])
                scores = scores_memo[key]
                stage['attacks'][method][scenario] = scores
                pres = preservation(g, label, probability)
                metrics = overlap(clean_scores['ids'], scores['ids'])
                row = dict(dataset=name, target=target, method=method, scenario=scenario, seed=s,
                           **metrics, **pres, joint_disruption=pres['feasible']*(1-metrics['similarity']),
                           clean_repeat_similarity=repeat_metrics['similarity'],
                           directly_deleted_clean_edges=len(set(edits)&set(clean_scores['ids'])))
                rows.append(row)
                evaluate_fidelity(method, scenario, g, scores, s)
        evidence[str(s)] = stage
        print(name, target, 'fresh seed', s, flush=True)
    updates = {}
    for method, edits in chosen.items():
        nodes = sorted(set(rec.edges[:, edits].reshape(-1).tolist()))
        before = rec.data.x[nodes]; after = rec.features(nodes, set(edits))
        updates[method] = dict(affected_nodes=nodes, before=before.tolist(), after=after.tolist(),
                               max_standardized_change=float((before-after).abs().max()))
    for k, v in b['state'].items():
        torch.testing.assert_close(model.state_dict()[k].cpu(), v, atol=0, rtol=0)
    torch.cuda.synchronize()
    return dict(dataset=name, target=target, trial=trial, manifest_id=mid, source_hash=sha(old_path),
                selection_seed=selection_seed, evaluation_seeds=evaluation_seeds,
                seconds=time.time()-begin, clean_probability=probability, clean_label=label,
                feature_names=rec.names, source_feature_max_error=rec.clean_max_error,
                incident_feature_max_error=ctx.clean_local_feature_error,
                chosen=chosen, candidates=candidates, selection_clean=clean_selection,
                proposals=len(pool), unique_candidates=len({tuple(v) for v in pool}),
                unique_selection_explainer_calls=len(memo), explanations=evidence,
                feature_updates=updates, random_controls=random_evidence,
                rows=rows, fidelity_rows=fidelity_rows, frozen_weights=True)


def report(m, mid, phase='pilot', qualified=None):
    qualified = CONFIG['datasets'] if qualified is None else qualified
    cohort = m['targets'] if phase=='pilot' else m['expanded_targets']
    trials = [0] if phase=='pilot' else CONFIG['expansion_trials']
    expected = sum(len(cohort[n])*len(trials) for n in qualified)
    folder = OUT/phase; folder.mkdir(parents=True,exist_ok=True); cases = []
    for p in sorted((folder/'cases').glob('*.json')):
        d = json.loads(p.read_text()); assert d['manifest_id'] == mid
        assert d['target'] in cohort[d['dataset']] and d['trial'] in trials
        cases.append(d)
    coverage = dict(completed=len(cases), expected=expected, complete=len(cases)==expected,
                    per_dataset={n: sum(c['dataset']==n for c in cases) for n in CONFIG['datasets']})
    save(folder/'coverage.json', coverage)
    if not cases:
        return coverage
    df = pd.DataFrame([dict(trial=c['trial'],**r) for c in cases for r in c['rows']])
    ff = pd.DataFrame([dict(trial=c['trial'],**r) for c in cases for r in c['fidelity_rows']])
    df.to_csv(folder/'per_seed.csv', index=False); ff.to_csv(folder/'fidelity_per_seed.csv', index=False)
    metrics = ['similarity', 'jaccard', 'preserved', 'feasible', 'delta_prob', 'joint_disruption',
               'clean_size', 'attacked_size', 'clean_empty', 'attacked_empty', 'clean_repeat_similarity',
               'directly_deleted_clean_edges']
    target = df.groupby(['dataset','target','method','scenario'])[metrics].mean().reset_index()
    target.to_csv(folder/'per_target.csv', index=False)
    fmetrics = [p+k for p in ('','random_','excess_') for k in ('hard_plus','hard_minus','soft_plus','soft_minus')]
    ft = ff.groupby(['dataset','target','method','scenario','intervention'])[fmetrics+['preserved','feasible']].mean().reset_index()
    ft.to_csv(folder/'fidelity_per_target.csv', index=False)
    rng = np.random.default_rng(42017)
    def ci(values):
        a = np.asarray(values, dtype=float)
        boot = a[rng.integers(0,len(a),(CONFIG['bootstrap_draws'],len(a)))].mean(1)
        return dict(mean=float(a.mean()), lo=float(np.quantile(boot,.025)), hi=float(np.quantile(boot,.975)))
    summary = []
    for (name, method, scenario), group in target.groupby(['dataset','method','scenario']):
        for metric in metrics:
            summary.append(dict(dataset=name, method=method, scenario=scenario, metric=metric,
                                targets=len(group), **ci(group[metric])))
    pd.DataFrame(summary).to_csv(folder/'summary.csv', index=False)
    paired = []
    for name, group in target.groupby('dataset'):
        for method in sorted(group.method.unique()):
            gg = group[group.method==method]
            for metric in ('similarity','preserved','feasible','delta_prob','joint_disruption'):
                table = gg.pivot(index='target',columns='scenario',values=metric)
                paired.append(dict(dataset=name, comparison=method+' / same edits', metric=metric,
                                   targets=len(table), **ci(table.refreshed-table.frozen)))
        a = group[(group.method=='Search frozen')&(group.scenario=='frozen')].set_index('target')
        b = group[(group.method=='Search refreshed')&(group.scenario=='refreshed')].set_index('target').loc[a.index]
        for metric in ('similarity','preserved','feasible','delta_prob','joint_disruption'):
            paired.append(dict(dataset=name, comparison='Matched search / own scenario', metric=metric,
                               targets=len(a), **ci(b[metric]-a[metric])))
            both = (a.feasible==1)&(b.feasible==1)
            if both.any():
                paired.append(dict(dataset=name, comparison='Matched search / both feasible', metric=metric,
                                   targets=int(both.sum()), **ci((b[metric]-a[metric])[both])))
    pdf = pd.DataFrame(paired); pdf.to_csv(folder/'paired_effects.csv',index=False)
    fp = []
    for (name, method, scenario), group in ft.groupby(['dataset','method','scenario']):
        if set(group.intervention) != {'edge','record'}:
            continue
        for metric in fmetrics:
            table = group.pivot(index='target',columns='intervention',values=metric)
            fp.append(dict(dataset=name, method=method, scenario=scenario, metric=metric,
                           targets=len(table), **ci(table.record-table.edge)))
    pd.DataFrame(fp).to_csv(folder/'fidelity_paired_effects.csv',index=False)
    lines = [f'# Transaction-consistency {phase}', '',
             f'**{"COMPLETE" if coverage["complete"] else "PROVISIONAL"}: {len(cases)}/{expected} target-trial cases.**', '',
             'SubgraphX; six deleted transaction rows; matched pools of 40 proposals; five fresh evaluation seeds. '
             'Frozen features model graph-store corruption; refreshed features model upstream record suppression. '
             'Classifiers, labels, static account fields and original preprocessing remain fixed. '
             'Expansion follows the frozen screening rule; screening and expansion are reported separately.', '',
             '| Dataset | Selection origin | Processing | N | Similarity | Label preserved | Within label/2pp constraint | Joint disruption |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for (n,method,scenario),g in target.groupby(['dataset','method','scenario']):
        lines.append(f'| {n} | {method} | {scenario} | {len(g)} | {g.similarity.mean():.4f} | '
                     f'{g.preserved.mean():.4f} | {g.feasible.mean():.4f} | {g.joint_disruption.mean():.4f} |')
    lines += ['', 'Lower similarity means greater explanation disruption. Joint disruption is (1-similarity) '
              'with zero credit unless the label and 2pp probability constraint are both preserved. '
              'All targets remain in denominators, including cases with no feasible candidate. '
              'Saved replay attacks were selected under frozen features; interpret them as transfer evidence.', '',
              '| Dataset | Matched search: refreshed minus frozen | Mean | 95% target interval |',
              '|---|---|---:|---:|']
    for r in paired:
        if r['comparison']=='Matched search / own scenario':
            lines.append(f'| {r["dataset"]} | {r["metric"]} | {r["mean"]:.4f} | ({r["lo"]:.4f}, {r["hi"]:.4f}) |')
    lines += ['', 'Paired intervals average seeds within targets before resampling. They are conditional descriptive '
              'intervals and do not include graph-node dependence or model-training uncertainty. The cohort has '
              'been evaluated previously. Empty/native-set cardinalities and clean-repeat variability are saved.', '',
              'On clean and refreshed graphs, fidelity compares edge-only removal/retention with input '
              'features fixed versus raw-record removal/retention with feature refresh. Frozen attacked graphs '
              'have edge fidelity only: adding a refresh there would confound the intervention with a baseline '
              'feature correction. Fidelity concerns the '
              'current graph\'s predicted class; prediction-changing cases are flagged. Twenty size-matched random '
              'sets control cardinality, not connectivity or other distribution shift. Retention removes all other '
              'transaction records globally. These are distinct intervention questions, not evidence of ground-truth '
              'explanation correctness or a universal preferred metric.', '',
              f'Mean completed target runtime: {np.mean([c["seconds"] for c in cases]):.1f} seconds.', '',
              'Original studies and the ongoing HI-Small run are read-only. The HI-Small detector is weak and the '
              'legacy AMLSim scaling is reproduced as trained; neither limitation is silently repaired.']
    (folder/'REPORT.md').write_text('\n'.join(lines),encoding='utf8')
    return coverage


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['validate','pipeline','report'])
    args = parser.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available()
    torch.cuda.set_per_process_memory_fraction(.25)
    lock = OUT/'controller.lock'
    fd = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode()); os.close(fd)
    worker = None
    try:
        m = manifest(); mid = digest(m)
        if args.mode == 'validate':
            worker = Worker(OUT/'validation/worker')
            validations = []
            for name in CONFIG['datasets']:
                save(OUT/'status.json',dict(state='validating',pid=os.getpid(),dataset=name))
                b, model, rec = load(name)
                r = validate_one(name,m['validation_targets'][name][0],b,model,rec,worker)
                validations.append(r); print('VALIDATED',json.dumps(r),flush=True)
                save(OUT/'validation/progress.json',dict(manifest_id=mid,checks=validations))
                del b,model,rec; torch.cuda.empty_cache()
            assert sources()==m['sources']
            save(OUT/'validation.json',dict(manifest_id=mid,checks=validations,complete=True))
            save(OUT/'status.json',dict(state='validated',pid=os.getpid(),manifest_id=mid))
            return
        validation = json.loads((OUT/'validation.json').read_text())
        assert validation['complete'] and validation['manifest_id']==mid, 'Technical validation is missing or stale'
        mp = OUT/'manifest.json'
        if mp.exists():
            assert json.loads(mp.read_text())==m, 'Resume inputs/source changed; preserve evidence and use a new run'
        else:
            save(mp,m)
        folder = OUT/'pilot'; (folder/'cases').mkdir(parents=True,exist_ok=True)
        if args.mode=='report':
            report(m,mid); return
        worker = Worker(OUT/'worker')
        for name in CONFIG['datasets']:
            b,model,rec = load(name)
            for target in m['targets'][name]:
                p = folder/f'cases/{name}_{target}.json'
                if p.exists():
                    assert json.loads(p.read_text())['manifest_id']==mid
                    continue
                save(OUT/'status.json',dict(state='running',pid=os.getpid(),worker_pid=worker.p.pid,
                                          dataset=name,target=target,manifest_id=mid))
                print('START',name,target,flush=True)
                result = one_case(name,target,b,model,rec,worker,mid)
                save(p,result)
                coverage = report(m,mid)
                print('SAVED',name,target,'seconds',round(result['seconds'],1),
                      'completed',coverage['completed'],'GPU_peak_MB',round(torch.cuda.max_memory_allocated()/1024**2),flush=True)
                torch.cuda.empty_cache()
            del b,model,rec; torch.cuda.empty_cache()
        coverage = report(m,mid)
        assert coverage['complete'] and sources()==m['sources']
        paired = pd.read_csv(OUT/'pilot/paired_effects.csv')
        decisions = []; qualified = []
        for name in CONFIG['datasets']:
            row = paired[(paired.dataset==name)&(paired.comparison=='Matched search / own scenario')&
                         (paired.metric=='joint_disruption')].iloc[0]
            promising = (abs(float(row['mean'])) >= CONFIG['minimum_expansion_effect'] and
                         (float(row['lo']) > 0 or float(row['hi']) < 0))
            decisions.append(dict(dataset=name, primary='fresh-seed joint disruption',
                                  mean=float(row['mean']), lo=float(row['lo']), hi=float(row['hi']),
                                  promising=bool(promising)))
            if promising:
                qualified.append(name)
        save(OUT/'promotion_decision.json',dict(manifest_id=mid,qualified_datasets=qualified,
                rule='Complete technical coverage; abs paired joint-disruption difference >=0.10 and 95% interval excludes zero',
                details=decisions))
        expanded_coverage = None
        if qualified:
            expanded = OUT/'expanded'; (expanded/'cases').mkdir(parents=True,exist_ok=True)
            for name in qualified:
                b,model,rec = load(name)
                for target in m['expanded_targets'][name]:
                    for trial in CONFIG['expansion_trials']:
                        p = expanded/f'cases/{name}_{target}_{trial}.json'
                        if p.exists():
                            assert json.loads(p.read_text())['manifest_id']==mid
                            continue
                        save(OUT/'status.json',dict(state='running_expansion',pid=os.getpid(),worker_pid=worker.p.pid,
                              dataset=name,target=target,trial=trial,qualified_datasets=qualified,manifest_id=mid))
                        print('EXPANSION START',name,target,trial,flush=True)
                        result = one_case(name,target,b,model,rec,worker,mid,trial=trial)
                        save(p,result)
                        expanded_coverage = report(m,mid,phase='expanded',qualified=qualified)
                        print('EXPANSION SAVED',name,target,trial,'seconds',round(result['seconds'],1),
                              'completed',expanded_coverage['completed'],flush=True)
                        torch.cuda.empty_cache()
                del b,model,rec; torch.cuda.empty_cache()
            assert expanded_coverage['complete'] and sources()==m['sources']
        save(OUT/'status.json',dict(state='complete',pid=os.getpid(),manifest_id=mid,
                                    pilot=coverage,expanded_datasets=qualified,expanded=expanded_coverage))
    except Exception:
        save(OUT/'status.json',dict(state='failed',pid=os.getpid(),traceback=traceback.format_exc()))
        raise
    finally:
        if worker is not None:
            worker.close()
        lock.unlink(missing_ok=True)


if __name__=='__main__':
    main()
