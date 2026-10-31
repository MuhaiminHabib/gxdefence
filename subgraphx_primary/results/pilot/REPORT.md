# SubgraphX-primary AMLSim results

6 / 6 evaluations saved. COMPLETE.

Direct discrete SubgraphX-targeted search, not original GXAttack or its gradient objective. Six edits; 40 adaptive proposals versus 40 independent random candidates. Native SubgraphX sets, not top-10 or top-25% truncations. Fixed features and model.

## Table II — Attack results

| Method | Similarity ↓ | Edge edits | ΔLabel ↓ | ΔProb ↓ |
|---|---:|---:|---:|---:|
| SubgraphX-targeted search | 0.0000 ± 0.0000 | 6 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random flipping | 0.1442 ± 0.1328 | 6 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random rewiring | 0.1190 ± 0.1684 | 6 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random search | 0.0000 ± 0.0000 | 6 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |

## Table III — Harmonic fidelity before → after

| Explainer | Clean | Attacked |
|---|---:|---:|
| SubgraphX | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| GNNExplainer | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| PGExplainer | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |

Our harmonic summary combines Fidelity+ with 1 − Fidelity−; it is not ground-truth explanation accuracy. PG/GNN use top-10 edges; SubgraphX uses its native set.

## Table IV — Native SubgraphX fidelity and overlap

| Metric | Clean | Targeted search | Random flipping | Random rewiring | Random search |
|---|---:|---:|---:|---:|---:|
| jaccard | 1.0000 (self-reference) | 0.0000 ± 0.0000 | 0.0998 ± 0.1207 | 0.0926 ± 0.1309 | 0.0000 ± 0.0000 |
| hard_plus | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| hard_minus | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| soft_plus | -0.0000 ± 0.0000 | 0.0000 ± 0.0000 | -0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| soft_minus | -0.0001 ± 0.0001 | -0.0002 ± 0.0000 | -0.0002 ± 0.0001 | 0.0005 ± 0.0011 | -0.0002 ± 0.0001 |

Clean-repeat native similarity: 0.1546 ± 0.1181. Clean-repeat native Jaccard: 0.1002 ± 0.1202.
Means ± sample SD across trial means. Hard fidelity values are fractions; soft values are signed probability differences, with negative meaning increased confidence. Similarity change alone does not establish poorer fidelity or human deception.
