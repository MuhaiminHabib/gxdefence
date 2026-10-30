# GNNExplainer-primary: three-trial report

**COMPLETE**

| Dataset | Eligible illicit test targets | Planned trials | Saved evaluations | Expected evaluations |
|---|---:|---:|---:|---:|
| AMLSim | 166 | 3 | 498 | 498 |
| HI-Small | 795 | 3 | 2385 | 2385 |
| Total | 961 | 3 | 2883 | 2883 |

All previously eligible targets on the complete graphs; Elliptic excluded. Six directed edge edits, frozen features and classifiers. Trial seeds 2026, 2027 and 2028. This is a GNNExplainer-targeted GXAttack-objective adaptation, not an exact reproduction of the original PGExplainer attack.

Eligibility: correctly classified illicit test nodes, incoming two-hop neighbourhood of 4–100 nodes and 5–2000 edge rows, at least three removable non-self edges and three absent ordered pairs. These are our registered limits.

## Table II — Attack results

| Method | Metric | AMLSim | HI-Small |
|---|---|---:|---:|
| GNN-targeted GX adaptation | Cosine similarity ↓ | 0.2374 ± 0.0045 | 0.2482 ± 0.0073 |
| GNN-targeted GX adaptation | Edge edits | 6 | 6 |
| GNN-targeted GX adaptation | ΔLabel ↓ | 0.0000 ± 0.0000 | 0.0021 ± 0.0007 |
| GNN-targeted GX adaptation | ΔProb ↓ | 0.0014 ± 0.0002 | 0.0273 ± 0.0014 |
| Random flipping | Cosine similarity ↓ | 0.5588 ± 0.0148 | 0.5288 ± 0.0179 |
| Random flipping | Edge edits | 6 | 6 |
| Random flipping | ΔLabel ↓ | 0.0020 ± 0.0035 | 0.0096 ± 0.0051 |
| Random flipping | ΔProb ↓ | 0.0002 ± 0.0000 | 0.0122 ± 0.0003 |
| Random rewiring | Cosine similarity ↓ | 0.4418 ± 0.0120 | 0.4398 ± 0.0158 |
| Random rewiring | Edge edits | 6 | 6 |
| Random rewiring | ΔLabel ↓ | 0.0020 ± 0.0035 | 0.0151 ± 0.0025 |
| Random rewiring | ΔProb ↓ | 0.0001 ± 0.0000 | 0.0154 ± 0.0004 |
| Random search | Cosine similarity ↓ | 0.2415 ± 0.0010 | 0.2292 ± 0.0037 |
| Random search | Edge edits | 6 | 6 |
| Random search | ΔLabel ↓ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Random search | ΔProb ↓ | 0.0009 ± 0.0004 | 0.0241 ± 0.0017 |

Mean ± sample standard deviation across three trial means. Similarity uses binary top-25% edge selections; lower means more explanation change. ΔLabel is the fraction of changed predictions. ΔProb is the average absolute change in probability for the original class. Fractions and probability differences are not percentages.

## Table III — Explanation fidelity before → after GXAttack

| Explainer | AMLSim | HI-Small |
|---|---:|---:|
| GNNExplainer | 0.0120 ± 0.0000 → 0.0080 ± 0.0069 | 0.0893 ± 0.0166 → 0.0687 ± 0.0049 |
| PGExplainer | 0.0080 ± 0.0069 → 0.0000 ± 0.0000 | 0.1019 ± 0.0329 → 0.0629 ± 0.0309 |
| SubgraphX | 0.0237 ± 0.0118 → 0.0159 ± 0.0068 | 0.1727 ± 0.0139 → 0.0947 ± 0.0133 |

This is our harmonic summary of Fidelity+ and (1 − Fidelity−), computed within each trial before averaging. It is not ground-truth explanation accuracy (GEA), and is not a direct harmonic mean of Fidelity+ and Fidelity−. PG/GNN use top-10 edges; SubgraphX uses its native set.

## Table IV — Additional GNNExplainer results

| Dataset | Metric | Clean | GX adaptation | Random flipping | Random rewiring | Random search |
|---|---|---:|---:|---:|---:|---:|
| AMLSim | Jaccard@10 ↓ | 1.0000 (self-reference) | 0.0089 ± 0.0013 | 0.3043 ± 0.0041 | 0.1328 ± 0.0105 | 0.0082 ± 0.0006 |
| AMLSim | Fidelity+ ↑ | 0.0060 ± 0.0000 | 0.0040 ± 0.0035 | 0.0080 ± 0.0035 | 0.0080 ± 0.0035 | 0.0100 ± 0.0035 |
| AMLSim | Fidelity− ↓ | 0.0181 ± 0.0120 | 0.0120 ± 0.0060 | 0.0141 ± 0.0152 | 0.0100 ± 0.0035 | 0.0161 ± 0.0092 |
| AMLSim | Soft Fidelity+ | 0.0013 ± 0.0002 | 0.0012 ± 0.0000 | 0.0016 ± 0.0004 | 0.0015 ± 0.0005 | 0.0013 ± 0.0002 |
| AMLSim | Soft Fidelity− | -0.0011 ± 0.0089 | -0.0060 ± 0.0046 | -0.0038 ± 0.0081 | -0.0065 ± 0.0024 | -0.0021 ± 0.0064 |
| HI-Small | Jaccard@10 ↓ | 1.0000 (self-reference) | 0.1179 ± 0.0068 | 0.3868 ± 0.0240 | 0.2627 ± 0.0221 | 0.1062 ± 0.0049 |
| HI-Small | Fidelity+ ↑ | 0.0470 ± 0.0091 | 0.0356 ± 0.0026 | 0.0507 ± 0.0073 | 0.0495 ± 0.0026 | 0.0612 ± 0.0040 |
| HI-Small | Fidelity− ↓ | 0.0671 ± 0.0026 | 0.0478 ± 0.0067 | 0.0562 ± 0.0019 | 0.0549 ± 0.0091 | 0.0436 ± 0.0069 |
| HI-Small | Soft Fidelity+ | 0.0227 ± 0.0038 | 0.0330 ± 0.0035 | 0.0229 ± 0.0031 | 0.0256 ± 0.0014 | 0.0300 ± 0.0021 |
| HI-Small | Soft Fidelity− | 0.0014 ± 0.0034 | -0.0094 ± 0.0042 | -0.0045 ± 0.0036 | -0.0030 ± 0.0023 | -0.0205 ± 0.0012 |

Fidelity+: how often removing the selected edges changes the label. Fidelity−: how often keeping only those edges changes the label. Soft versions measure the signed drop in class probability under the same removal/retention tests. Negative means confidence increased. Lower overlap alone does not demonstrate poorer fidelity or investigator deception.

## Clean-repeat controls and prediction preservation

| Dataset | Repeat binary top25 similarity | Repeat Jaccard@10 | GX label changes / evaluations |
|---|---:|---:|---:|
| AMLSim | 0.3050 ± 0.0240 | 0.0249 ± 0.0205 | 0 / 498 |
| HI-Small | 0.3830 ± 0.0309 | 0.2154 ± 0.0221 | 5 / 2385 |

Clean repeat reruns the explainer with a different seed on the unchanged graph. Random search selects among 40 candidates, matching native candidate-evaluation count but not gradient computation. No defence evaluation is included.
