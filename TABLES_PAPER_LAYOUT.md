# Results arranged as Tables II and III of the supplied v2 paper

Existing completed study: known-label Elliptic graph; full AMLSim; 50% HI-Small. This is not the new complete-graph study.

## Table II — adapted attack results

Dataset columns and method/metric row groups follow page 8. Values are mean ± sample SD across five trials. GEA is unavailable. Fractions are used for DeltaLabel and DeltaProb. Sim_cos is now recomputed from the saved importance scores using binary top-25% edge-row masks (ceil rounding, stable ID tie-break). This follows the v2 thresholding approach while retaining directed multigraph row identity; it is an adaptation, not an exact simple-adjacency replication. No attack was rerun. Continuous cosine remains in Table III-A and the original CSVs.

| Method | Metric | Elliptic | AMLSim | HI-Small 50% |
|---|---|---:|---:|---:|
| Clean | O. GEA | — | — | — |
| GXAttack | P. GEA ↓ | — | — | — |
| GXAttack | Delta GEA ↑ | — | — | — |
| GXAttack | Sim_cos binary25% ↓ | 0.3179 ± 0.0363 | 0.7959 ± 0.1606 | 0.5643 ± 0.0295 |
| GXAttack | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| GXAttack | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| GXAttack | DeltaProb ↓ | 0.0407 ± 0.0040 | 0.0011 ± 0.0005 | 0.0502 ± 0.0051 |
| Random flipping | P. GEA ↓ | — | — | — |
| Random flipping | Delta GEA ↑ | — | — | — |
| Random flipping | Sim_cos binary25% ↓ | 0.5265 ± 0.1582 | 0.9596 ± 0.0212 | 0.6458 ± 0.0310 |
| Random flipping | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random flipping | DeltaLabel ↓ | 0.0293 ± 0.0204 | 0.0000 ± 0.0000 | 0.0520 ± 0.0303 |
| Random flipping | DeltaProb ↓ | 0.0289 ± 0.0062 | 0.0002 ± 0.0001 | 0.0324 ± 0.0109 |
| Random rewiring | P. GEA ↓ | — | — | — |
| Random rewiring | Delta GEA ↑ | — | — | — |
| Random rewiring | Sim_cos binary25% ↓ | 0.4399 ± 0.0959 | 0.9676 ± 0.0110 | 0.6549 ± 0.0366 |
| Random rewiring | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random rewiring | DeltaLabel ↓ | 0.0634 ± 0.0370 | 0.0000 ± 0.0000 | 0.0400 ± 0.0141 |
| Random rewiring | DeltaProb ↓ | 0.0555 ± 0.0153 | 0.0002 ± 0.0001 | 0.0291 ± 0.0077 |

## Table III — adapted clean → attacked fidelity summary

Explainer rows and dataset columns follow page 9. These entries are the equal-weight harmonic summary of necessity and sufficiency, not GEA. They aggregate five trials; the original paper shows GEA for a typical run.

| Explainer | Elliptic | AMLSim | HI-Small 50% |
|---|---:|---:|---:|
| PGExplainer | 0.0567 → 0.0567 | 0.0000 → 0.0000 | 0.1474 → 0.0534 |
| GNNExplainer | 0.0658 → 0.0658 | 0.0000 → 0.0000 | 0.1538 → 0.0970 |
| SubgraphX | 0.2003 → 0.1099 | 0.0392 → 0.0235 | 0.0839 → 0.0833 |

## Table III-A — explanation similarity under transferred GXAttack

Within-explainer clean-versus-attacked cosine. This measures change, not accuracy.

| Explainer | Elliptic | AMLSim | HI-Small 50% |
|---|---:|---:|---:|
| PGExplainer | 0.5120 ± 0.0500 | 0.8654 ± 0.1082 | 0.7428 ± 0.0173 |
| GNNExplainer | 0.4320 ± 0.0778 | 0.8534 ± 0.0935 | 0.6016 ± 0.0409 |
| SubgraphX | 0.2221 ± 0.0687 | 0.2809 ± 0.0667 | 0.4597 ± 0.0500 |
## Table IV — Additional explanation metrics

See [the supplementary table](SUPPLEMENTARY_TABLE.md) for Clean / GXAttack / Random flipping / Random rewiring comparisons: Jaccard at k=5/10/20, Fidelity+, Fidelity−, harmonic fidelity, and explicitly marked unavailable metrics.
