# SubgraphX-primary HI-Small results

795 / 795 evaluations saved. COMPLETE.

Direct discrete SubgraphX-targeted search, not original GXAttack or its gradient objective. Six edits; 40 adaptive proposals versus 40 independent random candidates. Native SubgraphX sets, not top-10 or top-25% truncations. Fixed features and model.

## Table II — Attack results

| Method | Similarity ↓ | Edge edits | ΔLabel ↓ | ΔProb ↓ |
|---|---:|---:|---:|---:|
| SubgraphX-targeted search | 0.1497 | 6 | 0.0000 | 0.0159 |
| Random flipping | 0.5393 | 6 | 0.0088 | 0.0122 |
| Random rewiring | 0.5309 | 6 | 0.0126 | 0.0150 |
| Random search | 0.1159 | 6 | 0.0000 | 0.0169 |

## Table III — Harmonic fidelity before → after

| Explainer | Clean | Attacked |
|---|---:|---:|
| SubgraphX | 0.1567 | 0.0864 |
| GNNExplainer | 0.1000 | 0.0955 |
| PGExplainer | 0.1334 | 0.1290 |

Our harmonic summary combines Fidelity+ with 1 − Fidelity−; it is not ground-truth explanation accuracy. PG/GNN use top-10 edges; SubgraphX uses its native set.

## Table IV — Native SubgraphX fidelity and overlap

| Metric | Clean | Targeted search | Random flipping | Random rewiring | Random search |
|---|---:|---:|---:|---:|---:|
| jaccard | 1.0000 (self-reference) | 0.0797 | 0.4381 | 0.4278 | 0.0583 |
| hard_plus | 0.0855 | 0.0453 | 0.0755 | 0.0805 | 0.0541 |
| hard_minus | 0.0679 | 0.0629 | 0.0654 | 0.0591 | 0.0755 |
| soft_plus | 0.0544 | 0.0294 | 0.0484 | 0.0497 | 0.0256 |
| soft_minus | -0.0476 | -0.0213 | -0.0421 | -0.0486 | -0.0154 |

Clean-repeat native similarity: 0.7047. Clean-repeat native Jaccard: 0.6308.
Single-trial means; between-trial standard deviation is unavailable. Hard fidelity values are fractions; soft values are signed probability differences, with negative meaning increased confidence. Similarity change alone does not establish poorer fidelity or human deception.
