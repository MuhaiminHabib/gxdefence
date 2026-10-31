# GNNExplainer-primary results

GXAttack-objective adaptation with differentiation through GNNExplainer mask fitting. Direct targeting is distinct from the original paper's PGExplainer targeting. Native PyG explanations score every candidate and all reported outcomes.

Current saved target-trial cases: 12. Check status.json for completion. Pilot/smoke data are validation-only, not final test results.

| Dataset | Method | Explainer | Binary top25 similarity | Label change fraction | Clean soft+ | Attacked soft+ |
|---|---|---|---:|---:|---:|---:|
| amlsim | Clean repeat | GNNExplainer | 0.34345 | 0.00000 | nan | nan |
| amlsim | GNN-targeted GX adaptation | GNNExplainer | 0.29056 | 0.00000 | 0.00000 | 0.00001 |
| amlsim | GNN-targeted GX adaptation | PGExplainer | 0.77663 | 0.00000 | 0.00001 | 0.00001 |
| amlsim | GNN-targeted GX adaptation | SubgraphX | 0.45238 | 0.00000 | -0.00001 | 0.00001 |
| amlsim | Random flipping | GNNExplainer | 0.60209 | 0.00000 | 0.00000 | -0.00000 |
| amlsim | Random rewiring | GNNExplainer | 0.57219 | 0.00000 | 0.00000 | -0.00000 |
| amlsim | Random search | GNNExplainer | 0.24591 | 0.00000 | 0.00000 | 0.00000 |
| hi_small | Clean repeat | GNNExplainer | 0.32937 | 0.00000 | nan | nan |
| hi_small | GNN-targeted GX adaptation | GNNExplainer | 0.19735 | 0.00000 | 0.04853 | 0.04659 |
| hi_small | GNN-targeted GX adaptation | PGExplainer | 0.46463 | 0.00000 | -0.00627 | -0.01548 |
| hi_small | GNN-targeted GX adaptation | SubgraphX | 0.74767 | 0.00000 | 0.06961 | 0.06959 |
| hi_small | Random flipping | GNNExplainer | 0.60871 | 0.00000 | 0.04853 | 0.04856 |
| hi_small | Random rewiring | GNNExplainer | 0.32204 | 0.00000 | 0.04853 | 0.02130 |
| hi_small | Random search | GNNExplainer | 0.04925 | 0.00000 | 0.04853 | 0.10703 |

Soft values are signed probability differences, not percentage points. Clean repeat uses a different explanation seed; its fidelity fields are unavailable. Random search uses the same number of native candidate evaluations as the attack, but does not match gradient-computation effort. Features remain fixed.