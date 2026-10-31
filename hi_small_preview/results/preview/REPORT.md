# GNNExplainer-primary results

GXAttack-objective adaptation with differentiation through GNNExplainer mask fitting. Direct targeting is distinct from the original paper's PGExplainer targeting. Native PyG explanations score every candidate and all reported outcomes.

Current saved target-trial cases: 30. Check status.json for completion. This preview uses 30 randomly selected eligible HI-Small test targets, one trial each. Descriptive sample averages are not full-cohort or five-trial results.

| Dataset | Method | Explainer | Binary top25 similarity | Label change fraction | Clean soft+ | Attacked soft+ |
|---|---|---|---:|---:|---:|---:|
| hi_small | Clean repeat | GNNExplainer | 0.38240 | 0.00000 | nan | nan |
| hi_small | GNN-targeted GX adaptation | GNNExplainer | 0.20522 | 0.00000 | 0.01558 | 0.04895 |
| hi_small | GNN-targeted GX adaptation | PGExplainer | 0.52097 | 0.00000 | 0.02825 | 0.03352 |
| hi_small | GNN-targeted GX adaptation | SubgraphX | 0.53421 | 0.00000 | 0.06588 | 0.06498 |
| hi_small | Random flipping | GNNExplainer | 0.55007 | 0.03333 | 0.01558 | 0.01925 |
| hi_small | Random rewiring | GNNExplainer | 0.46522 | 0.00000 | 0.01558 | 0.02877 |
| hi_small | Random search | GNNExplainer | 0.17737 | 0.00000 | 0.01558 | 0.04076 |

Soft values are signed probability differences, not percentage points. Clean repeat uses a different explanation seed; its fidelity fields are unavailable. Random search uses the same number of native candidate evaluations as the attack, but does not match gradient-computation effort. Features remain fixed.