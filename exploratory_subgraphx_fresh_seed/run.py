"""Audit fixed HI-Small SubgraphX attacks using unseen explanation randomness."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import argparse
import ctypes
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
OUT = ROOT / 'results'
SOURCE = STUDY / 'subgraphx_hi_small/results/full'
spec = importlib.util.spec_from_file_location('fresh_seed_graph_helpers', STUDY/'followup_audit/run.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
np, pd, torch, save, sha = H.np, H.pd, H.torch, H.save, H.sha
METHODS = ['SubgraphX-targeted search', 'Random search']
FID = ['hard_plus', 'hard_minus', 'soft_plus', 'soft_minus']
DGL_PY = r'D:\habib dissertation\Projects\AML-GNN-Replication-v2\.venv-subgraphx\Scripts\python.exe'
FLAGS = (subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name == 'nt' else 0
CONFIG = dict(dataset='hi_small', targets=100, subset_seed=20261102, source_trial=2026,
              fresh_seeds=list(range(131001, 131006)), repeat_seeds=list(range(132001, 132006)),
              methods=METHODS, bootstrap_draws=5000, bootstrap_seed=133001,
              technical_targets=3, gpu_fraction=.25,
              subgraphx=dict(num_hops=2, num_child=6, num_rollouts=5, node_min=3, shapley_steps=5))


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def priority():
    if os.name == 'nt':
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)


def freeze():
    original = read(SOURCE/'manifest.json')
    coverage = read(SOURCE/'coverage.json')
    assert coverage == dict(saved=795, expected=795, complete=True)
    assert original['trials'] == [2026] and original['params']['subgraphx'] == CONFIG['subgraphx']
    for rel, expected in original['sources'].items():
        assert sha(STUDY/rel) == expected, ('changed original source', rel)
    targets = sorted(random.Random(CONFIG['subset_seed']).sample(sorted(original['targets']), CONFIG['targets']))
    assert len(targets) == len(set(targets)) == 100
    seeds = CONFIG['fresh_seeds'] + CONFIG['repeat_seeds']
    assert len(set(seeds)) == 10 and not set(seeds) & {2026, 12026}
    paths = [SOURCE/'manifest.json', STUDY/'complete_graphs/prepared/hi_small.pt']
    paths += [SOURCE/f'cases/hi_small_{t}_2026.json' for t in targets]
    code = [Path(__file__), ROOT/'README.md', STUDY/'followup_audit/run.py',
            STUDY/'complete_graphs/prepare.py', STUDY/'complete_graphs/attack_core.py',
            STUDY/'complete_graphs/subgraph_worker.py', STUDY/'framework/src/models/marasi_models.py']
    versions = json.loads(subprocess.check_output(
        [DGL_PY, '-c', 'import json,torch,dgl;print(json.dumps(dict(torch=torch.__version__,dgl=dgl.__version__)))'],
        text=True, creationflags=FLAGS))
    manifest = dict(config=CONFIG, targets=targets, eligible_targets=original['targets'],
                    sources={p.relative_to(STUDY).as_posix(): sha(p) for p in code},
                    inputs={p.relative_to(STUDY).as_posix(): sha(p) for p in paths},
                    original_sources=original['sources'], original_params=original['params'],
                    python=sys.version, torch=torch.__version__, pyg=__import__('torch_geometric').__version__,
                    worker_environment=versions)
    path = OUT/'manifest.json'
    if path.exists():
        assert read(path) == manifest, 'Inputs/configuration changed: use a new audit folder.'
    else:
        save(path, manifest)
    return manifest


def overlap(a, b):
    aa, bb = set(a), set(b)
    assert all(v == 1. for v in a.values()) and all(v == 1. for v in b.values())
    union = aa | bb
    similarity = len(aa & bb)/(len(aa)*len(bb))**.5 if aa and bb else float(not union)
    return dict(similarity=similarity, jaccard=len(aa & bb)/len(union) if union else 1.,
                clean_size=len(aa), attacked_size=len(bb), clean_empty=int(not aa), attacked_empty=int(not bb))


def native_fidelity(model, graph, scores):
    assert set(scores) <= set(graph['ids'])
    return H.fid_indices(model, graph, [i for i, key in enumerate(graph['ids']) if key in scores])


class Worker:
    def __init__(self, folder):
        self.folder = folder
        self.log = (folder/'subgraphx_stderr.log').open('a', encoding='utf-8')
        self.p = subprocess.Popen([DGL_PY, '-u', str(STUDY/'complete_graphs/subgraph_worker.py')],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                                  text=True, creationflags=FLAGS)

    def explain(self, model, graph, seed, hidden):
        path = self.folder/'worker_context.pt'
        torch.save(dict(x=graph['x'].cpu(), edge=graph['edge'].cpu(), target=graph['target'],
                        hidden=hidden, state={k: v.detach().cpu() for k, v in model.state_dict().items()},
                        nodes=torch.tensor(graph['global_nodes']), ids=graph['ids'],
                        logits=graph['logits'].cpu(), label=graph['label']), path)
        self.p.stdin.write(json.dumps(dict(path=str(path), seed=seed))+'\n')
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            raise RuntimeError('SubgraphX worker exited; inspect results/subgraphx_stderr.log')
        result = json.loads(line)
        if 'error' in result:
            raise RuntimeError(result['error'])
        scores = {key: 1. for key in result['ids']}
        assert len(scores) == len(result['ids']) and set(scores) <= set(graph['ids'])
        return dict(scores=scores, nodes=result['nodes'])

    def close(self):
        try:
            self.p.stdin.close()
            try:
                self.p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.p.terminate()
                self.p.wait(timeout=15)
        finally:
            self.p.stdout.close()
            self.log.close()


def status(manifest_id, target=None, **extra):
    save(OUT/'status.json', dict(state='running', pid=os.getpid(), target=target,
                               manifest_id=manifest_id, updated_unix=time.time(), **extra))


@torch.no_grad()
def full_parity(model, data, target, graph, scores=None):
    e, ids = H.physical(data, graph['edit_ids'])
    x, edge = data.x.to('cuda'), e.to('cuda')
    full = model(x, edge)[target]
    torch.testing.assert_close(full, graph['logits'], atol=3e-4, rtol=3e-4)
    checks = dict(full_local_logit_max_error=float((full-graph['logits']).abs().max()))
    if scores is not None:
        selected = torch.zeros(edge.shape[1], dtype=torch.bool, device='cuda')
        removed_count = sum(k.startswith('E') for k in graph['edit_ids'])
        deleted = sorted(int(k[1:]) for k in graph['edit_ids'] if k.startswith('E'))
        for key in scores:
            if key.startswith('E'):
                original_index = int(key[1:])
                index = original_index - sum(v < original_index for v in deleted)
            else:
                added = [k for k in graph['edit_ids'] if k.startswith('A')]
                index = data.edge_index.shape[1] - removed_count + added.index(key)
            assert ids[index] == key
            selected[index] = True
        removed = model(x, edge[:, ~selected])[target]
        kept = model(x, edge[:, selected])[target]
        label = int(full.argmax()); prob = float(full.softmax(-1)[label])
        reference = dict(hard_plus=int(removed.argmax()!=label), hard_minus=int(kept.argmax()!=label),
                         soft_plus=prob-float(removed.softmax(-1)[label]),
                         soft_minus=prob-float(kept.softmax(-1)[label]))
        local = native_fidelity(model, graph, scores)
        assert all(abs(local[k]-reference[k]) < 3e-5 for k in FID), (local, reference)
        checks['full_local_physical_fidelity_parity'] = True
    return checks


def make_rows(target, seed, stage, explanations, repeat, fids, predictions):
    base = overlap(explanations['Clean']['scores'], repeat['scores'])
    output = []
    for method in METHODS:
        metric = overlap(explanations['Clean']['scores'], explanations[method]['scores'])
        row = dict(dataset='hi_small', target=target, seed=seed, stage=stage, method=method,
                   preserved=predictions[method]['preserved'], delta_prob=predictions[method]['delta_prob'],
                   **metric, clean_repeat_similarity=base['similarity'], clean_repeat_jaccard=base['jaccard'],
                   excess_disruption=base['similarity']-metric['similarity'])
        for key in FID:
            row['clean_'+key] = fids['Clean'][key]
            row['attacked_'+key] = fids[method][key]
            row['delta_'+key] = fids[method][key]-fids['Clean'][key]
        output.append(row)
    return output


def validate_record(record, manifest, complete):
    assert record['manifest_id'] == identity(manifest) and record['target'] in manifest['targets']
    target = record['target']
    assert record['source_sha256'] == manifest['inputs'][f'subgraphx_hi_small/results/full/cases/hi_small_{target}_2026.json']
    actual = {int(k) for k in record['explanations']}
    expected = {2026, *CONFIG['fresh_seeds']}
    assert actual <= expected and 2026 in actual
    if complete:
        assert actual == expected and record['checks']['model_unchanged']
    assert {(r['method'], r['seed']) for r in record['rows']} == {(m, s) for m in METHODS for s in actual}
    assert len(record['rows']) == len(METHODS)*len(actual)
    for s in actual - {2026}:
        assert record['explanations'][str(s)]['repeat_seed'] == CONFIG['repeat_seeds'][CONFIG['fresh_seeds'].index(s)]


def one(target, data, model, hidden, worker, manifest, technical):
    start = time.time(); mid = identity(manifest)
    source_path = SOURCE/f'cases/hi_small_{target}_2026.json'
    source = read(source_path)
    assert source['target'] == target and source['trial'] == 2026 and all(source['checks'].values())
    assert source['params'] == manifest['original_params'] and source['sources'] == manifest['original_sources']
    frozen = {k: v.clone() for k, v in model.state_dict().items()}
    graphs, checks, predictions = {}, {}, {}
    for method in ['Clean']+METHODS:
        edits = [] if method == 'Clean' else source['attacks'][method]['edge_ids']
        assert method == 'Clean' or len(set(edits)) == len(edits) == 6
        e, ids = H.physical(data, edits)
        graph = H.local_graph(data, e, ids, target)
        graph['logits'], graph['label'] = H.predict(model, graph)
        graph['edit_ids'] = edits; graphs[method] = graph
        if method == 'Clean':
            clean_label = graph['label']; clean_prob = float(graph['logits'].softmax(-1)[clean_label])
        else:
            old = source['attacks'][method]
            preserved = graph['label'] == clean_label
            prob = float(graph['logits'].softmax(-1)[clean_label])
            assert preserved == old['preserved'] and abs(prob-old['probability']) < 3e-4
            predictions[method] = dict(preserved=int(preserved), delta_prob=abs(prob-clean_prob))
        checks[method] = full_parity(model, data, target, graph) if technical else {}
        del e, ids
    progress = OUT/f'progress/hi_small_{target}.json'
    if progress.exists():
        result = read(progress); validate_record(result, manifest, complete=False)
    else:
        original, fids = {}, {}
        for method, graph in graphs.items():
            status(mid, target, stage='source_parity', method=method, seed=2026)
            original[method] = worker.explain(model, graph, 2026, hidden)
            scores = source['clean']['SubgraphX'] if method == 'Clean' else source['attacks'][method]['scores']
            nodes = source['clean_nodes'] if method == 'Clean' else source['attacks'][method]['nodes']
            assert original[method]['scores'] == scores and set(original[method]['nodes']) == set(nodes), ('source-seed mismatch', target, method)
            fids[method] = native_fidelity(model, graph, scores)
            checks[method]['source_seed_native_set_parity'] = True
        for method in METHODS:
            saved = next(r for r in source['rows'] if r['method']==method and r['explainer']=='SubgraphX' and r['selection']=='native')
            for prefix, key in [('clean', 'Clean'), ('attacked', method)]:
                assert all(abs(saved[prefix+'_'+k]-fids[key][k]) < 3e-5 for k in FID)
            metric = overlap(original['Clean']['scores'], original[method]['scores'])
            assert abs(metric['similarity']-saved['binary_top25_cosine']) < 1e-10
            assert abs(metric['jaccard']-saved['jaccard']) < 1e-10
            checks[method]['source_prediction_fidelity_parity'] = True
        repeat = dict(scores=source['clean_repeat'], nodes=source['repeat_nodes'])
        ev = dict(graphs=original, clean_repeat=repeat, repeat_seed=12026, fidelity=fids)
        result = dict(dataset='hi_small', target=target, manifest_id=mid, source_sha256=sha(source_path),
                      technical=technical, checks=checks, predictions=predictions, seconds=0.,
                      explanations={'2026': ev}, rows=make_rows(target, 2026, 'selection_seed', original, repeat, fids, predictions),
                      graph_details={m:dict(ids=g['ids'], global_nodes=g['global_nodes'], edits=g['edit_ids'],
                                           logits=g['logits'].cpu().tolist()) for m,g in graphs.items()})
        result['seconds'] += time.time()-start; start=time.time(); save(progress, result)
    for i, seed in enumerate(CONFIG['fresh_seeds']):
        if str(seed) in result['explanations']:
            continue
        fresh, fids = {}, {}
        for method, graph in graphs.items():
            status(mid, target, stage='fresh', method=method, seed=seed)
            fresh[method] = worker.explain(model, graph, seed, hidden)
            fids[method] = native_fidelity(model, graph, fresh[method]['scores'])
            if technical and i == 0:
                result['checks'][method].update(full_parity(model, data, target, graph, fresh[method]['scores']))
        status(mid, target, stage='clean_repeat', seed=CONFIG['repeat_seeds'][i])
        repeat = worker.explain(model, graphs['Clean'], CONFIG['repeat_seeds'][i], hidden)
        if technical and i == 0:
            again = worker.explain(model, graphs['Clean'], seed, hidden)
            assert again == fresh['Clean'], 'same-seed SubgraphX repeat differs'
            result['checks']['same_seed_repeat'] = True
        result['explanations'][str(seed)] = dict(graphs=fresh, clean_repeat=repeat,
                                               repeat_seed=CONFIG['repeat_seeds'][i], fidelity=fids)
        result['rows'].extend(make_rows(target, seed, 'fresh', fresh, repeat, fids, predictions))
        result['seconds'] += time.time()-start; start=time.time(); save(progress, result)
        print('SEED_SAVED', target, seed, flush=True)
    for key, value in frozen.items():
        torch.testing.assert_close(model.state_dict()[key], value, atol=0, rtol=0)
    result['checks']['model_unchanged'] = True
    result['seconds'] += time.time()-start
    validate_record(result, manifest, complete=True)
    return result


def interval(values, rng):
    a = np.asarray(values, dtype=float)
    assert len(a) and np.isfinite(a).all()
    boot = a[rng.integers(0, len(a), (CONFIG['bootstrap_draws'], len(a)))].mean(axis=1)
    return dict(mean=float(a.mean()), lo=float(np.quantile(boot,.025)), hi=float(np.quantile(boot,.975)))


def report(manifest):
    cases = [read(p) for p in sorted((OUT/'cases').glob('*.json'))]
    assert len({c['target'] for c in cases}) == len(cases)
    for c in cases:
        validate_record(c, manifest, complete=True)
    coverage = dict(saved=len(cases), expected=100, complete=len(cases)==100, fresh_seeds_per_target=5)
    save(OUT/'coverage.json', coverage)
    if not cases:
        return coverage
    df = pd.DataFrame([r for c in cases for r in c['rows']])
    df.to_csv(OUT/'per_seed.csv', index=False)
    metrics = ['similarity','jaccard','clean_repeat_similarity','clean_repeat_jaccard','excess_disruption',
               'clean_size','attacked_size','clean_empty','attacked_empty','preserved','delta_prob']
    metrics += [prefix+'_'+key for prefix in ['clean','attacked','delta'] for key in FID]
    target = df.groupby(['target','method','stage'])[metrics].mean().reset_index()
    target.to_csv(OUT/'per_target.csv', index=False)
    rng = np.random.default_rng(CONFIG['bootstrap_seed']); summary=[]; paired=[]
    for (method,stage), group in target.groupby(['method','stage']):
        for metric in metrics:
            summary.append(dict(method=method,stage=stage,metric=metric,targets=len(group),**interval(group[metric],rng)))
    for method in METHODS:
        group = target[target.method.eq(method)]
        for metric in ['similarity','jaccard','excess_disruption']+[p+'_'+k for p in ['clean','attacked','delta'] for k in FID]:
            table = group.pivot(index='target', columns='stage', values=metric)
            paired.append(dict(comparison='Fresh minus selection',method=method,metric=metric,targets=len(table),
                               **interval(table['fresh']-table['selection_seed'],rng)))
    contrasts={}
    for stage in ['selection_seed','fresh']:
        table=target[target.stage.eq(stage)].pivot(index='target',columns='method',values='similarity')
        contrasts[stage]=table['Random search']-table['SubgraphX-targeted search']
        paired.append(dict(comparison='Random minus adaptive',method=stage,metric='similarity',targets=len(table),
                           **interval(contrasts[stage],rng)))
    paired.append(dict(comparison='Fresh minus selection in random-adaptive contrast',method='both',metric='similarity',
                       targets=len(cases),**interval(contrasts['fresh']-contrasts['selection_seed'],rng)))
    pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
    pd.DataFrame(paired).to_csv(OUT/'paired_effects.csv',index=False)
    lines=['# HI-Small SubgraphX fresh-seed audit','',
           f'**{"COMPLETE" if coverage["complete"] else "PROVISIONAL"}: {len(cases)}/100 preselected targets, five fresh paired seeds each.**','',
           'Saved seed-2026 attacks are fixed. Seeds are averaged within each target before paired target bootstrap resampling. '
           'Native explanation sets are not truncated. Clean repeats are an independent variability reference, not a matched null.','',
           '| Method | Selection similarity | Fresh similarity | Clean-repeat similarity | Fresh minus selection, 95% target interval |',
           '|---|---:|---:|---:|---|']
    for method in METHODS:
        g=target[target.method.eq(method)];old=g[g.stage.eq('selection_seed')];new=g[g.stage.eq('fresh')]
        p=next(r for r in paired if r['comparison']=='Fresh minus selection' and r['method']==method and r['metric']=='similarity')
        lines.append(f'| {method} | {old.similarity.mean():.4f} | {new.similarity.mean():.4f} | '
                     f'{new.clean_repeat_similarity.mean():.4f} | {p["mean"]:.4f} [{p["lo"]:.4f}, {p["hi"]:.4f}] |')
    method_effect=next(r for r in paired if r['comparison']=='Random minus adaptive' and r['method']=='fresh')
    lines += ['',f'Fresh random-minus-adaptive similarity: {method_effect["mean"]:.4f} '
              f'[{method_effect["lo"]:.4f}, {method_effect["hi"]:.4f}]. Negative means lower overlap for random search.', '',
              'Primary endpoint: adaptive fresh-minus-selection similarity. Other comparisons and fidelity intervals are secondary, descriptive, '
              'and not multiplicity-adjusted. Positive attenuation does not by itself establish attack failure. '
              'All sampled targets are retained; preservation is reported separately, without a retrospective probability cap.', '',
              'CSV summaries include Jaccard, empty sets, native hard/soft removal/retention fidelity, and paired differences. '
              'Intervals omit graph-node dependence, common seed effects and retraining variation. This audit does not establish '
              'generalization beyond the fixed classifier and source attack run, ground-truth explanation error or human deception.', '',
              f'Mean completed-target runtime: {np.mean([c["seconds"] for c in cases]):.1f} seconds.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return coverage


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['pilot','pipeline','report']);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    for sub in ['cases','progress']:
        (OUT/sub).mkdir(exist_ok=True)
    lock=OUT/'controller.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    worker=None
    try:
        priority();manifest=freeze();mid=identity(manifest)
        if args.mode=='report':
            report(manifest);return
        assert torch.cuda.is_available()
        torch.cuda.set_per_process_memory_fraction(CONFIG['gpu_fraction'])
        bundle=torch.load(STUDY/'complete_graphs/prepared/hi_small.pt',map_location='cpu',weights_only=False)
        data=bundle['data'];model=H.MarasiGraphSAGE(data.num_features,bundle['hidden']).to('cuda')
        model.load_state_dict(bundle['state']);model.eval()
        for p in model.parameters():p.requires_grad_(False)
        worker=Worker(OUT)
        planned=manifest['targets'][:3] if args.mode=='pilot' else manifest['targets']
        for i,target in enumerate(planned):
            path=OUT/f'cases/hi_small_{target}.json'
            if path.exists():validate_record(read(path),manifest,complete=True)
            else:
                print('START',target,'index',i+1,'of',len(planned),flush=True);status(mid,target,stage='prepare')
                result=one(target,data,model,bundle['hidden'],worker,manifest,technical=i<3)
                save(path,result);report(manifest)
                print('SAVED',target,'seconds',round(result['seconds'],1),flush=True)
            if i==2:
                technical=[read(OUT/f'cases/hi_small_{t}.json') for t in manifest['targets'][:3]]
                assert all(c['technical'] and c['checks']['same_seed_repeat'] and all(
                    c['checks'][m]['full_local_physical_fidelity_parity'] for m in ['Clean']+METHODS) for c in technical)
                save(OUT/'validation.json',dict(passed=True,manifest_id=mid,targets=manifest['targets'][:3]))
                print('TECHNICAL_VALIDATION_PASSED',flush=True)
            if i>=3:assert read(OUT/'validation.json')==dict(passed=True,manifest_id=mid,targets=manifest['targets'][:3])
        coverage=report(manifest)
        save(OUT/'status.json',dict(state='complete' if coverage['complete'] else 'pilot_complete',pid=os.getpid(),
                                  manifest_id=mid,updated_unix=time.time(),**coverage))
    except Exception:
        save(OUT/'status.json',dict(state='failed',pid=os.getpid(),updated_unix=time.time(),traceback=traceback.format_exc()))
        raise
    finally:
        try:
            if worker is not None:worker.close()
        finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    main()
