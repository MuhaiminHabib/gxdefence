# SubgraphX-primary HI-Small results

3 / 3 evaluations saved. COMPLETE.

Direct discrete SubgraphX-targeted search, not original GXAttack or its gradient objective. Six edits; 40 adaptive proposals versus 40 independent random candidates. Native SubgraphX sets, not top-10 or top-25% truncations. Fixed features and model.

## Table II — Attack results

| Method | Similarity ↓ | Edge edits | ΔLabel ↓ | ΔProb ↓ |
|---|---:|---:|---:|---:|
| SubgraphX-targeted search | 0.3210 | 6 | 0.0000 | 0.0091 |
| Random flipping | 0.6682 | 6 | 0.0000 | 0.0240 |
| Random rewiring | 0.5718 | 6 | 0.0000 | 0.0133 |
| Random search | 0.1027 | 6 | 0.0000 | 0.0234 |

## Table III — Harmonic fidelity before → after

| Explainer | Clean | Attacked |
|---|---:|---:|
| SubgraphX | 0.0000 | 0.0000 |
| GNNExplainer | 0.0000 | 0.0000 |
| PGExplainer | 0.0000 | 0.0000 |

Our harmonic summary combines Fidelity+ with 1 − Fidelity−; it is not ground-truth explanation accuracy. PG/GNN use top-10 edges; SubgraphX uses its native set.

## Table IV — Native SubgraphX fidelity and overlap

| Metric | Clean | Targeted search | Random flipping | Random rewiring | Random search |
|---|---:|---:|---:|---:|---:|
| jaccard | 1.0000 (self-reference) | 0.2589 | 0.5481 | 0.4148 | 0.0460 |
| hard_plus | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hard_minus | 0.0000 | 0.3333 | 0.0000 | 0.0000 | 0.0000 |
| soft_plus | 0.0646 | 0.0372 | 0.1324 | 0.0853 | 0.0128 |
| soft_minus | 0.0121 | 0.0950 | -0.0968 | 0.0168 | 0.0273 |

Clean-repeat native similarity: 0.8007. Clean-repeat native Jaccard: 0.7500.
Single-trial means; between-trial standard deviation is unavailable. Hard fidelity values are fractions; soft values are signed probability differences, with negative meaning increased confidence. Similarity change alone does not establish poorer fidelity or human deception.
