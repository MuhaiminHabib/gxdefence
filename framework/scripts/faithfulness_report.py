"""Faithfulness report presentation extracted from examine_node.py.

Preserves rankings, same-size comparisons, per-seed metrics and stability.
Input JSON keys: target, baseline, edges, report, rankings, model_note;
optional probability_name (default: illicit). Report contains rows, choices,
and stability in the original approved report schema. Metrics must already
be evaluated and validated by the caller. This file only formats results.
"""
import argparse
import json
from pathlib import Path

def render_approved_report(node, baseline, edges, report, rankings, source, model_note, probability_name='illicit'):
    """Single console format for all explainers, datasets and graph states."""
    lookup = {tuple(sorted(row['selection'])): row for row in report['rows']}
    lines = []
    def say(text=''):
        lines.append(text)
        print(text)
    name = lambda subset: '+'.join(subset) or 'None'
    say(f'Target {node} | Original {probability_name} probability: {baseline:.2%}')
    say('Saved evaluation viewer: NO model runs. Only presentation files are created.')
    say('Displaying supplied evaluation metrics; this renderer does not recalculate fidelity or run models.')
    for label, edge in edges.items():
        say(f"{label}: {edge['source']} -> {edge['destination']} | edge {edge['edge_id']}")
    available = {c['method'] for c in report['choices']}
    preferred = ['GNNExplainer', 'PGExplainer', 'SubgraphX_induced_edges']
    methods = [m for m in preferred if m in available] + sorted(available - set(preferred))
    previews = {}
    say('\nEXPLAINER RANKINGS -- first saved seed, not an average')
    say(f'Importance scores are not {probability_name} probabilities or comparable across methods.')
    for method in methods:
        choices = [c for c in report['choices'] if c['method'] == method]
        seed = min(c['seed'] for c in choices)
        previews[method] = [c for c in choices if c['seed'] == seed]
        say(f'\n{method} | seed {seed}')
        if method in rankings:
            run_row = rankings[method][str(seed)]
            for choice in previews[method]:
                if set(run_row['ranking'][:choice['budget']]) != set(choice['selection']):
                    raise ValueError('Ranking and evaluated selection differ.')
            for rank, label in enumerate(run_row['ranking'], 1):
                edge = edges[label]
                say(f"{rank:>2}. {label:<3} {edge['source']} -> {edge['destination']} | score {run_row['scores'][label]:.6f}")
        else:
            choice = previews[method][0]
            say('Selects a NODE GROUP, not a ranked edge list.')
            say(f"Nodes: {choice['selected_nodes']} | induced edges: {name(choice['selection'])}")
    say('\nNECESSITY: remove selected edges. Necessity = 1 if the original class changes; higher is better.')
    say('SUFFICIENCY: keep ONLY selected edges globally. Sufficiency = 1 if class changes; lower is better.')
    say(model_note)
    say(f'Positive drop/gap = reduced {probability_name} probability; negative = increased probability.')
    for budget in sorted({c['budget'] for group in previews.values() for c in group}):
        say(f'\nSAME-SIZE COMPARISON | {budget} selected edges | first saved seeds')
        say(f"{'Selection':<15}{'Selected by':<44}{'Remove P':>10}{'Drop pp':>10}{'Necessity':>11}{'Keep P':>10}{'Gap pp':>10}{'Sufficiency':>13}")
        for key, row in lookup.items():
            if len(key) != budget:
                continue
            selected_by = [m.replace('_induced_edges','') for m,g in previews.items()
                           if any(tuple(sorted(c['selection'])) == key for c in g)]
            say(f"{name(key):<15}{', '.join(selected_by) or 'Not selected':<44}{row['removed_illicit_probability']:>10.2%}{row['signed_drop_pp']:>+10.2f}{row['fidelity_gnn_acc']:>11.0f}{row['kept_illicit_probability']:>10.2%}{row['signed_gap_pp']:>+10.2f}{row['fidelity_gnn_acc_inv']:>13.0f}")
    say('\nALL SAVED SEEDS -- each row is a run, not a new transaction')
    for c in report['choices']:
        row = c['metrics']
        say(f"{c['method']:<25} seed {c['seed']:<6} edges {name(c['selection']):<15} remove {row['removed_illicit_probability']:.2%} / keep {row['kept_illicit_probability']:.2%} | Necessity {row['fidelity_gnn_acc']:.0f}, Sufficiency {row['fidelity_gnn_acc_inv']:.0f} | control: {c['control'] or 'none'}")
    say('\nSTABILITY -- edge-set Jaccard: 1 = identical sets; repeatability, NOT proof of faithfulness')
    for row in report['stability']:
        say(f"{row['method']} | budget {row['budget']} | {row['runs']} runs | Jaccard {format(row['edge_jaccard_mean'], '.3f') if row['edge_jaccard_mean'] is not None else 'N/A'} | sizes {row['selected_sizes']}")
    say('Empty/full-candidate controls are not discriminating explanations. Empty-empty Jaccard is defined as 1.')
    say('Compare equal edge budgets. SubgraphX stability here concerns induced edges, not its full node groups.')
    say(f'Source: {source.resolve()}')

    return lines, previews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Saved report input JSON')
    parser.add_argument('--output', type=Path, required=True, help='New text report path')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; select a fresh report path.')
    packet = json.loads(args.input.read_text(encoding='utf-8-sig'))
    lines, _ = render_approved_report(
        packet['target'], packet['baseline'], packet['edges'], packet['report'],
        packet['rankings'], args.input, packet['model_note'],
        packet.get('probability_name', 'illicit'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        output.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
