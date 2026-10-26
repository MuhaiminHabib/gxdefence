# GXAttack financial study results

Adapted directed-multigraph GXAttack on frozen GraphSAGE models. See PROTOCOL.md for assumptions and deviations from the reference implementation. No literature review or defence experiment.

## Pilot

Execution status: **complete**.

| Dataset | Method | Completed targets | Trials | PG cosine mean ± trial SD | Target label preserved | Absolute probability change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| amlsim | Clean repeat | 3 | 2 | 0.9831 ± 0.0150 | 100.0% | 0.0000 |
| amlsim | GXAttack | 3 | 2 | 0.9437 ± 0.0737 | 100.0% | 0.0000 |
| amlsim | Random flipping | 3 | 2 | 0.9968 ± 0.0002 | 100.0% | 0.0000 |
| amlsim | Random rewiring | 3 | 2 | 0.9970 ± 0.0001 | 100.0% | 0.0000 |
| elliptic | Clean repeat | 3 | 2 | 0.9137 ± 0.0469 | 100.0% | 0.0000 |
| elliptic | GXAttack | 3 | 2 | 0.5018 ± 0.0023 | 100.0% | 0.0223 |
| elliptic | Random flipping | 3 | 2 | 0.8230 ± 0.0339 | 100.0% | 0.0054 |
| elliptic | Random rewiring | 3 | 2 | 0.6587 ± 0.0493 | 100.0% | 0.0082 |
| hi_small | Clean repeat | 3 | 2 | 0.9978 ± 0.0009 | 100.0% | 0.0000 |
| hi_small | GXAttack | 3 | 2 | 0.7941 ± 0.0099 | 100.0% | 0.0187 |
| hi_small | Random flipping | 3 | 2 | 0.8773 ± 0.0012 | 100.0% | 0.0103 |
| hi_small | Random rewiring | 3 | 2 | 0.8019 ± 0.0024 | 100.0% | 0.0097 |

Per-target evidence: results/pilot/cases/. All explainer and fidelity metrics: results/pilot/per_target_metrics.csv; trial means and sample SD: results/pilot/summary.csv.

### Transfer on the same GXAttack graph

| Dataset | Explainer | Cosine mean ± trial SD | Selected-set Jaccard | Clean necessity → attacked | Clean sufficiency-failure → attacked |
| --- | --- | ---: | ---: | ---: | ---: |
| amlsim | GNNExplainer | 0.9273 ± 0.0856 | 0.2407 | 0.000 → 0.000 | 0.000 → 0.000 |
| amlsim | PGExplainer | 0.9437 ± 0.0737 | 0.7261 | 0.000 → 0.000 | 0.000 → 0.000 |
| amlsim | SubgraphX | 0.1667 ± 0.2357 | 0.1667 | 0.000 → 0.000 | 0.000 → 0.000 |
| elliptic | GNNExplainer | 0.1790 ± 0.0044 | 0.2094 | 0.000 → 0.000 | 0.000 → 0.000 |
| elliptic | PGExplainer | 0.5018 ± 0.0023 | 0.2916 | 0.000 → 0.000 | 0.000 → 0.000 |
| elliptic | SubgraphX | 0.0000 ± 0.0000 | 0.0000 | 0.000 → 0.000 | 0.000 → 0.000 |
| hi_small | GNNExplainer | 0.7725 ± 0.0356 | 0.4509 | 0.000 → 0.000 | 0.000 → 0.000 |
| hi_small | PGExplainer | 0.7941 ± 0.0099 | 0.4995 | 0.000 → 0.000 | 0.000 → 0.000 |
| hi_small | SubgraphX | 0.4580 ± 0.1219 | 0.3444 | 0.000 → 0.000 | 0.000 → 0.000 |

PG/GNN selected sets use k=10, capped by available edges; SubgraphX uses its full variable-size induced edge set. Cosine is within each explainer, not a calibration comparison across explainers. Fidelity entries here include all attempts; the CSV additionally provides prediction-preserved trial means.

## Full

Execution status: **complete**.

| Dataset | Method | Completed targets | Trials | PG cosine mean ± trial SD | Target label preserved | Absolute probability change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| amlsim | Clean repeat | 50 | 5 | 0.9723 ± 0.0184 | 100.0% | 0.0000 |
| amlsim | GXAttack | 50 | 5 | 0.8654 ± 0.1082 | 100.0% | 0.0011 |
| amlsim | Random flipping | 50 | 5 | 0.9802 ± 0.0084 | 100.0% | 0.0002 |
| amlsim | Random rewiring | 50 | 5 | 0.9809 ± 0.0046 | 100.0% | 0.0002 |
| elliptic | Clean repeat | 41 | 5 | 0.8565 ± 0.0832 | 100.0% | 0.0000 |
| elliptic | GXAttack | 41 | 5 | 0.5120 ± 0.0500 | 100.0% | 0.0407 |
| elliptic | Random flipping | 41 | 5 | 0.7066 ± 0.0658 | 97.1% | 0.0289 |
| elliptic | Random rewiring | 41 | 5 | 0.5724 ± 0.0525 | 93.7% | 0.0555 |
| hi_small | Clean repeat | 50 | 5 | 0.9991 ± 0.0004 | 100.0% | 0.0000 |
| hi_small | GXAttack | 50 | 5 | 0.7428 ± 0.0173 | 100.0% | 0.0502 |
| hi_small | Random flipping | 50 | 5 | 0.8143 ± 0.0123 | 94.8% | 0.0324 |
| hi_small | Random rewiring | 50 | 5 | 0.8029 ± 0.0178 | 96.0% | 0.0291 |

Per-target evidence: results/full/cases/. All explainer and fidelity metrics: results/full/per_target_metrics.csv; trial means and sample SD: results/full/summary.csv.

### Transfer on the same GXAttack graph

| Dataset | Explainer | Cosine mean ± trial SD | Selected-set Jaccard | Clean necessity → attacked | Clean sufficiency-failure → attacked |
| --- | --- | ---: | ---: | ---: | ---: |
| amlsim | GNNExplainer | 0.8534 ± 0.0935 | 0.1519 | 0.000 → 0.000 | 0.004 → 0.000 |
| amlsim | PGExplainer | 0.8654 ± 0.1082 | 0.6577 | 0.000 → 0.000 | 0.028 → 0.024 |
| amlsim | SubgraphX | 0.2809 ± 0.0667 | 0.2655 | 0.020 → 0.012 | 0.032 → 0.032 |
| elliptic | GNNExplainer | 0.4320 ± 0.0778 | 0.3668 | 0.034 → 0.034 | 0.000 → 0.000 |
| elliptic | PGExplainer | 0.5120 ± 0.0500 | 0.3592 | 0.029 → 0.029 | 0.005 → 0.010 |
| elliptic | SubgraphX | 0.2221 ± 0.0687 | 0.1707 | 0.112 → 0.059 | 0.059 → 0.020 |
| hi_small | GNNExplainer | 0.6016 ± 0.0409 | 0.3092 | 0.084 → 0.052 | 0.024 → 0.004 |
| hi_small | PGExplainer | 0.7428 ± 0.0173 | 0.4764 | 0.080 → 0.028 | 0.044 → 0.032 |
| hi_small | SubgraphX | 0.4597 ± 0.0500 | 0.3702 | 0.044 → 0.044 | 0.060 → 0.056 |

PG/GNN selected sets use k=10, capped by available edges; SubgraphX uses its full variable-size induced edge set. Cosine is within each explainer, not a calibration comparison across explainers. Fidelity entries here include all attempts; the CSV additionally provides prediction-preserved trial means.

## Interpretation limits

- Pilot targets are validation cases and are excluded from the test study. A pilot is a technical feasibility check.
- Test results are conditional on one classifier checkpoint, correctly detected illicit nodes, and bounded contexts. Eligibility counts are saved in each dataset target file.
- Features are frozen. Synthetic additions are graph-store edits, not validated financial transactions.
- HI-Small account labels are derived from incident laundering transactions. Its new eight-feature classifier is a limited baseline; consult prepared/hi_small_training.csv and the checkpoint metadata.
- SubgraphX has variable-size node coalitions; its induced edge sets are not top-k rankings.
- Lower cosine or overlap demonstrates changed explanations, not human deception or ground-truth explanation error.
- PG clean-repeat controls use another independently fitted network; GNNExplainer and SubgraphX controls rerun the same algorithm with a different seed.
- The repository random-flipping implementation deletes existing edges. This study uses explicit uniform addition/deletion flips and separately matched deletion/addition rewiring; these are adapted controls.
- Early pilot failure logs are retained for provenance; the current status.json determines whether repaired runs passed.

HI-Small classifier test F1: 0.0337; test average precision: 0.0304. These are weak detector results and limit the scope of conclusions.
