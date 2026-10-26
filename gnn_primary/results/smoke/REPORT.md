# GNNExplainer-primary results

GXAttack-objective adaptation with differentiation through GNNExplainer mask fitting. Direct targeting is distinct from the original paper's PGExplainer targeting. Native PyG explanations score every candidate and all reported outcomes.

Current saved target-trial cases: 2. Check status.json for completion. Pilot/smoke data are validation-only, not final test results.

| Dataset | Method | Explainer | Binary top25 similarity | Label change fraction | Clean soft+ | Attacked soft+ |
|---|---|---|---:|---:|---:|---:|
| amlsim | Clean repeat | GNNExplainer | 0.31579 | 0.00000 | nan | nan |
| amlsim | GNN-targeted GX adaptation | GNNExplainer | 0.49937 | 0.00000 | 0.00000 | 0.00000 |
| amlsim | GNN-targeted GX adaptation | PGExplainer | 0.99875 | 0.00000 | 0.00000 | 0.00000 |
| amlsim | GNN-targeted GX adaptation | SubgraphX | 1.00000 | 0.00000 | 0.00000 | 0.00000 |
| amlsim | Random flipping | GNNExplainer | 0.87860 | 0.00000 | 0.00000 | 0.00000 |
| amlsim | Random rewiring | GNNExplainer | 0.80702 | 0.00000 | 0.00000 | 0.00000 |
| amlsim | Random search | GNNExplainer | 0.31830 | 0.00000 | 0.00000 | 0.00000 |
| hi_small | Clean repeat | GNNExplainer | 0.28571 | 0.00000 | nan | nan |
| hi_small | GNN-targeted GX adaptation | GNNExplainer | 0.42857 | 0.00000 | -0.00102 | -0.01436 |
| hi_small | GNN-targeted GX adaptation | PGExplainer | 0.85714 | 0.00000 | -0.01325 | -0.00022 |
| hi_small | GNN-targeted GX adaptation | SubgraphX | 0.00000 | 0.00000 | -0.00882 | -0.00160 |
| hi_small | Random flipping | GNNExplainer | 0.75907 | 0.00000 | -0.00102 | 0.00115 |
| hi_small | Random rewiring | GNNExplainer | 0.10911 | 0.00000 | -0.00102 | 0.01138 |
| hi_small | Random search | GNNExplainer | 0.71429 | 0.00000 | -0.00102 | -0.02546 |

Soft values are signed probability differences, not percentage points. Clean repeat uses a different explanation seed; its fidelity fields are unavailable. Random search uses the same number of native candidate evaluations as the attack, but does not match gradient-computation effort. Features remain fixed.