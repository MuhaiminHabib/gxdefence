# SubgraphX-primary AMLSim results

498 / 498 evaluations saved. COMPLETE.

Direct discrete SubgraphX-targeted search, not original GXAttack or its gradient objective. Six edits; 40 adaptive proposals versus 40 independent random candidates. Native SubgraphX sets, not top-10 or top-25% truncations. Fixed features and model.

## Table II — Attack results

| Method | Similarity ↓ | Edge edits | ΔLabel ↓ | ΔProb ↓ |
|---|---:|---:|---:|---:|
| SubgraphX-targeted search | 0.0039 ± 0.0033 | 6 | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 |
| Random flipping | 0.3339 ± 0.0029 | 6 | 0.0020 ± 0.0035 | 0.0002 ± 0.0000 |
| Random rewiring | 0.3767 ± 0.0191 | 6 | 0.0020 ± 0.0035 | 0.0001 ± 0.0000 |
| Random search | 0.0013 ± 0.0023 | 6 | 0.0000 ± 0.0000 | 0.0001 ± 0.0000 |

## Table III — Harmonic fidelity before → after

| Explainer | Clean | Attacked |
|---|---:|---:|
| SubgraphX | 0.0237 ± 0.0118 | 0.0080 ± 0.0069 |
| GNNExplainer | 0.0120 ± 0.0000 | 0.0120 ± 0.0000 |
| PGExplainer | 0.0080 ± 0.0069 | 0.0040 ± 0.0069 |

Our harmonic summary combines Fidelity+ with 1 − Fidelity−; it is not ground-truth explanation accuracy. PG/GNN use top-10 edges; SubgraphX uses its native set.

## Table IV — Native SubgraphX fidelity and overlap

| Metric | Clean | Targeted search | Random flipping | Random rewiring | Random search |
|---|---:|---:|---:|---:|---:|
| jaccard | 1.0000 (self-reference) | 0.0035 ± 0.0030 | 0.3081 ± 0.0058 | 0.3488 ± 0.0176 | 0.0009 ± 0.0015 |
| hard_plus | 0.0120 ± 0.0060 | 0.0040 ± 0.0035 | 0.0120 ± 0.0060 | 0.0141 ± 0.0070 | 0.0040 ± 0.0070 |
| hard_minus | 0.0341 ± 0.0070 | 0.0643 ± 0.0125 | 0.0442 ± 0.0139 | 0.0321 ± 0.0212 | 0.0542 ± 0.0060 |
| soft_plus | 0.0099 ± 0.0025 | 0.0042 ± 0.0026 | 0.0077 ± 0.0033 | 0.0074 ± 0.0026 | 0.0035 ± 0.0036 |
| soft_minus | 0.0211 ± 0.0052 | 0.0459 ± 0.0119 | 0.0335 ± 0.0088 | 0.0205 ± 0.0167 | 0.0453 ± 0.0001 |

Clean-repeat native similarity: 0.4082 ± 0.0161. Clean-repeat native Jaccard: 0.3788 ± 0.0149.
Means ± sample SD across trial means. Hard fidelity values are fractions; soft values are signed probability differences, with negative meaning increased confidence. Similarity change alone does not establish poorer fidelity or human deception.
