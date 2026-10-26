# Complete-graph GXAttack study

All supplied raw graph records; all eligible illicit test targets, five trials. Pilot uses separate validation targets. Layout follows Tables II and III of the supplied v2 paper.

## Pilot — complete

| Dataset | Correctly detected illicit candidates | Eligible | Selected | Trials |
|---|---:|---:|---:|---:|
| elliptic | 627 | 9 | 3 | 2 |
| amlsim | 239 | 131 | 3 | 2 |
| hi_small | 819 | 592 | 3 | 2 |

### Table II — adapted attack results

GEA requires independent ground-truth explanations and is unavailable. Sim_cos uses binary top25% edge-row masks (ceil rounding); directed multigraph conventions remain an adaptation. Values are mean ± sample SD across trial means. DeltaLabel and DeltaProb are fractions.

| Method | Metric | Elliptic | AMLSim | HI-Small 100% |
|---|---|---:|---:|---:|
| Clean | O. GEA | — | — | — |
| GXAttack | P. GEA ↓ | — | — | — |
| GXAttack | Delta GEA ↑ | — | — | — |
| GXAttack | Sim_cos binary25% ↓ | 0.0680 ± 0.0962 | 0.9257 ± 0.0869 | 0.7059 ± 0.0371 |
| GXAttack | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| GXAttack | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| GXAttack | DeltaProb ↓ | 0.0533 ± 0.0042 | 0.0000 ± 0.0000 | 0.0283 ± 0.0182 |
| Random flipping | P. GEA ↓ | — | — | — |
| Random flipping | Delta GEA ↑ | — | — | — |
| Random flipping | Sim_cos binary25% ↓ | 0.2601 ± 0.2012 | 0.9952 ± 0.0014 | 0.8042 ± 0.0216 |
| Random flipping | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random flipping | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random flipping | DeltaProb ↓ | 0.0273 ± 0.0135 | 0.0000 ± 0.0000 | 0.0230 ± 0.0014 |
| Random rewiring | P. GEA ↓ | — | — | — |
| Random rewiring | Delta GEA ↑ | — | — | — |
| Random rewiring | Sim_cos binary25% ↓ | 0.4206 ± 0.1667 | 0.9961 ± 0.0017 | 0.6310 ± 0.2750 |
| Random rewiring | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random rewiring | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random rewiring | DeltaProb ↓ | 0.0545 ± 0.0438 | 0.0000 ± 0.0000 | 0.0211 ± 0.0109 |

### Table III — adapted clean → attacked fidelity summary

Explainer rows and dataset columns follow the paper. Entries are equal-weight harmonic fidelity summaries, NOT GEA; five-trial averages rather than typical-run GEA. PG/GNN use top10 capped by available edges; SubgraphX uses its whole native induced set.

| Explainer | Elliptic | AMLSim | HI-Small 100% |
|---|---:|---:|---:|
| PGExplainer | 0.0000 → 0.0000 | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| GNNExplainer | 0.0000 → 0.0000 | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| SubgraphX | 0.2500 → 0.0000 | 0.0000 → 0.0000 | 0.0000 → 0.0000 |

### Supplement: transferred similarity and clean-repeat controls

Continuous cosine for PG/GNN and native binary cosine for SubgraphX. Within-explainer comparisons only.

| Explainer | Comparison | Elliptic | AMLSim | HI-Small 100% |
|---|---|---:|---:|---:|
| PGExplainer | Clean repeat | 0.9978 ± 0.0000 | 0.9831 ± 0.0150 | 0.9991 ± 0.0007 |
| PGExplainer | GXAttack | 0.5140 ± 0.0181 | 0.9437 ± 0.0737 | 0.8910 ± 0.0056 |
| GNNExplainer | Clean repeat | 0.7922 ± 0.0155 | 0.9826 ± 0.0014 | 0.7371 ± 0.0274 |
| GNNExplainer | GXAttack | 0.4715 ± 0.1293 | 0.9273 ± 0.0856 | 0.7375 ± 0.0425 |
| SubgraphX | Clean repeat | 0.8333 ± 0.2357 | 0.1546 ± 0.1181 | 0.6078 ± 0.2728 |
| SubgraphX | GXAttack | 0.4694 ± 0.0433 | 0.1667 ± 0.2357 | 0.5390 ± 0.1249 |

Additional metrics below reflect only the cases currently saved for this phase; treat them as provisional until phase completion.

## Table IV — Additional explanation metrics

PGExplainer; mean ± sample SD across available trial means. Completed initial study uses five trials. Fidelity uses top-10 edges, capped by available edges. Clean overlap with itself is 1 by definition; independent clean-repeat controls appear below.

### Elliptic

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.2798 ± 0.1431 | 0.2216 ± 0.1431 | 0.3782 ± 0.0578 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.3395 ± 0.0519 | 0.4203 ± 0.0342 | 0.4222 ± 0.0371 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.3395 ± 0.0519 | 0.5309 ± 0.0274 | 0.4222 ± 0.0371 |
| Fidelity+ / necessity ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Fidelity− / sufficiency failure ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Harmonic fidelity summary ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **1.0000 ± 0.0000**.

### AMLSim

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.6528 ± 0.0196 | 0.7937 ± 0.0224 | 1.0000 ± 0.0000 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.7261 ± 0.0841 | 0.8838 ± 0.0071 | 1.0000 ± 0.0000 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.7740 ± 0.1518 | 0.9380 ± 0.0020 | 0.9841 ± 0.0224 |
| Fidelity+ / necessity ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Fidelity− / sufficiency failure ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Harmonic fidelity summary ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.1405 ± 0.1987**.

### HI-Small 100%

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.4511 ± 0.1534 | 0.5635 ± 0.0786 | 0.4623 ± 0.2497 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.5912 ± 0.0912 | 0.7078 ± 0.0990 | 0.5381 ± 0.1928 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.7120 ± 0.0005 | 0.7457 ± 0.0004 | 0.6169 ± 0.2753 |
| Fidelity+ / necessity ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Fidelity− / sufficiency failure ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.1667 ± 0.2357 | 0.1667 ± 0.2357 |
| Harmonic fidelity summary ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.1493 ± 0.2111**.

Fidelity+ is the fraction of targets whose predicted class changes when selected edges are removed. Fidelity− is the fraction whose class changes when only selected edges are retained. The harmonic summary is 2 × Fidelity+ × (1 − Fidelity−) / (Fidelity+ + 1 − Fidelity−), computed within each trial before averaging; it is an adapted characterization summary, not ground-truth explanation accuracy.

Arrows indicate metric direction: lower Jaccard means greater explanation disruption; higher necessity and lower sufficiency failure indicate stronger explanatory fidelity. Compare attack overlap with clean-repeat overlap before attributing changes to the attack. Missing metrics are not zero.


All metrics: results/pilot/per_target_metrics.csv. Mean/SD: results/pilot/summary.csv. Case evidence: results/pilot/cases/.

## Full — complete

| Dataset | Correctly detected illicit candidates | Eligible | Selected | Trials |
|---|---:|---:|---:|---:|
| elliptic | 827 | 8 | 8 | 5 |
| amlsim | 306 | 166 | 166 | 5 |
| hi_small | 1109 | 795 | 795 | 5 |

### Table II — adapted attack results

GEA requires independent ground-truth explanations and is unavailable. Sim_cos uses binary top25% edge-row masks (ceil rounding); directed multigraph conventions remain an adaptation. Values are mean ± sample SD across trial means. DeltaLabel and DeltaProb are fractions.

| Method | Metric | Elliptic | AMLSim | HI-Small 100% |
|---|---|---:|---:|---:|
| Clean | O. GEA | — | — | — |
| GXAttack | P. GEA ↓ | — | — | — |
| GXAttack | Delta GEA ↑ | — | — | — |
| GXAttack | Sim_cos binary25% ↓ | 0.2466 ± 0.0517 | 0.8137 ± 0.1263 | 0.6872 ± 0.0174 |
| GXAttack | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| GXAttack | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0035 ± 0.0011 |
| GXAttack | DeltaProb ↓ | 0.0256 ± 0.0211 | 0.0014 ± 0.0012 | 0.0286 ± 0.0032 |
| Random flipping | P. GEA ↓ | — | — | — |
| Random flipping | Delta GEA ↑ | — | — | — |
| Random flipping | Sim_cos binary25% ↓ | 0.4684 ± 0.0671 | 0.9702 ± 0.0082 | 0.7763 ± 0.0183 |
| Random flipping | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random flipping | DeltaLabel ↓ | 0.0000 ± 0.0000 | 0.0012 ± 0.0027 | 0.0103 ± 0.0037 |
| Random flipping | DeltaProb ↓ | 0.0199 ± 0.0095 | 0.0002 ± 0.0001 | 0.0119 ± 0.0007 |
| Random rewiring | P. GEA ↓ | — | — | — |
| Random rewiring | Delta GEA ↑ | — | — | — |
| Random rewiring | Sim_cos binary25% ↓ | 0.3314 ± 0.1704 | 0.9762 ± 0.0049 | 0.7606 ± 0.0138 |
| Random rewiring | #Pert. ↓ | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 | 6.0000 ± 0.0000 |
| Random rewiring | DeltaLabel ↓ | 0.0250 ± 0.0559 | 0.0012 ± 0.0027 | 0.0146 ± 0.0057 |
| Random rewiring | DeltaProb ↓ | 0.0335 ± 0.0348 | 0.0001 ± 0.0000 | 0.0149 ± 0.0010 |

### Table III — adapted clean → attacked fidelity summary

Explainer rows and dataset columns follow the paper. Entries are equal-weight harmonic fidelity summaries, NOT GEA; five-trial averages rather than typical-run GEA. PG/GNN use top10 capped by available edges; SubgraphX uses its whole native induced set.

| Explainer | Elliptic | AMLSim | HI-Small 100% |
|---|---:|---:|---:|
| PGExplainer | 0.0000 → 0.0000 | 0.0048 → 0.0000 | 0.1076 → 0.0795 |
| GNNExplainer | 0.0000 → 0.0000 | 0.0120 → 0.0096 | 0.1054 → 0.0744 |
| SubgraphX | 0.0000 → 0.0000 | 0.0261 → 0.0072 | 0.1730 → 0.1099 |

### Supplement: transferred similarity and clean-repeat controls

Continuous cosine for PG/GNN and native binary cosine for SubgraphX. Within-explainer comparisons only.

| Explainer | Comparison | Elliptic | AMLSim | HI-Small 100% |
|---|---|---:|---:|---:|
| PGExplainer | Clean repeat | 0.9586 ± 0.0334 | 0.9706 ± 0.0198 | 0.9989 ± 0.0006 |
| PGExplainer | GXAttack | 0.3832 ± 0.1647 | 0.8841 ± 0.0807 | 0.8353 ± 0.0124 |
| GNNExplainer | Clean repeat | 0.7463 ± 0.1109 | 0.9697 ± 0.0019 | 0.7536 ± 0.0268 |
| GNNExplainer | GXAttack | 0.3163 ± 0.1721 | 0.8744 ± 0.0685 | 0.6755 ± 0.0317 |
| SubgraphX | Clean repeat | 0.7354 ± 0.1358 | 0.4011 ± 0.0151 | 0.6959 ± 0.0116 |
| SubgraphX | GXAttack | 0.2434 ± 0.1210 | 0.2957 ± 0.0326 | 0.5352 ± 0.0206 |

Additional metrics below reflect only the cases currently saved for this phase; treat them as provisional until phase completion.

## Table IV — Additional explanation metrics

PGExplainer; mean ± sample SD across available trial means. Completed initial study uses five trials. Fidelity uses top-10 edges, capped by available edges. Clean overlap with itself is 1 by definition; independent clean-repeat controls appear below.

### Elliptic

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.2257 ± 0.0846 | 0.3548 ± 0.0466 | 0.2859 ± 0.0971 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.2519 ± 0.1167 | 0.3987 ± 0.0380 | 0.3036 ± 0.0869 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.2853 ± 0.1304 | 0.4557 ± 0.0414 | 0.3298 ± 0.0963 |
| Fidelity+ / necessity ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0250 ± 0.0559 |
| Fidelity− / sufficiency failure ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Harmonic fidelity summary ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0444 ± 0.0994 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.8532 ± 0.0292**.

### AMLSim

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.6169 ± 0.0885 | 0.9034 ± 0.0415 | 0.9355 ± 0.0444 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.6854 ± 0.1022 | 0.9265 ± 0.0188 | 0.9525 ± 0.0292 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.7295 ± 0.1249 | 0.9428 ± 0.0100 | 0.9611 ± 0.0227 |
| Fidelity+ / necessity ↑ | 0.0024 ± 0.0033 | 0.0000 ± 0.0000 | 0.0012 ± 0.0027 | 0.0012 ± 0.0027 |
| Fidelity− / sufficiency failure ↓ | 0.0169 ± 0.0210 | 0.0145 ± 0.0125 | 0.0193 ± 0.0264 | 0.0169 ± 0.0183 |
| Harmonic fidelity summary ↑ | 0.0048 ± 0.0066 | 0.0000 ± 0.0000 | 0.0024 ± 0.0054 | 0.0024 ± 0.0054 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.1527 ± 0.1686**.

### HI-Small 100%

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.4481 ± 0.0699 | 0.5732 ± 0.0753 | 0.5627 ± 0.0678 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.5299 ± 0.0387 | 0.6318 ± 0.0531 | 0.6389 ± 0.0414 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.6077 ± 0.0118 | 0.6976 ± 0.0290 | 0.7022 ± 0.0224 |
| Fidelity+ / necessity ↑ | 0.0574 ± 0.0194 | 0.0415 ± 0.0062 | 0.0501 ± 0.0145 | 0.0574 ± 0.0160 |
| Fidelity− / sufficiency failure ↓ | 0.0629 ± 0.0343 | 0.0523 ± 0.0235 | 0.0652 ± 0.0383 | 0.0606 ± 0.0352 |
| Harmonic fidelity summary ↑ | 0.1076 ± 0.0346 | 0.0795 ± 0.0113 | 0.0948 ± 0.0267 | 0.1078 ± 0.0287 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.1969 ± 0.1229**.

Fidelity+ is the fraction of targets whose predicted class changes when selected edges are removed. Fidelity− is the fraction whose class changes when only selected edges are retained. The harmonic summary is 2 × Fidelity+ × (1 − Fidelity−) / (Fidelity+ + 1 − Fidelity−), computed within each trial before averaging; it is an adapted characterization summary, not ground-truth explanation accuracy.

Arrows indicate metric direction: lower Jaccard means greater explanation disruption; higher necessity and lower sufficiency failure indicate stronger explanatory fidelity. Compare attack overlap with clean-repeat overlap before attributing changes to the attack. Missing metrics are not zero.


All metrics: results/full/per_target_metrics.csv. Mean/SD: results/full/summary.csv. Case evidence: results/full/cases/.

## Model performance and interpretation

| Dataset | Test F1 | Test average precision |
|---|---:|---:|
| elliptic | 0.8337 | 0.9388 |
| hi_small | 0.0549 | 0.0501 |

AMLSim retains its existing complete-graph checkpoint. HI-Small uses an incident-laundering account-label proxy and eight aggregate features; weak detector performance, if present, limits conclusions.

Eligibility excludes unknown labels, incorrect predictions and contexts outside registered bounds. Graph data are complete, but this is not an attack on every node. Features stay fixed; additions are graph-store edits, not validated financial transactions.

GXAttack selects among40 discretizations; random controls use one draw. Edit budgets match, search effort does not. Six edits need not be small relative to a tiny context. Similarity changes do not prove explanation incorrectness or human deception. No defence experiment or literature review is included.