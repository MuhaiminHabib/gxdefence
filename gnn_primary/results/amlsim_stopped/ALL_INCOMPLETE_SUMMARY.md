# AMLSim partial results - stopped at user request

Saved 277 target-trial evaluations, 166 unique targets. Trial counts: {2026: 166, 2027: 111}. This is an incomplete five-trial experiment. Do not treat unequal trial coverage as a completed five-trial estimate. Use the completed first trial for a uniform single-trial comparison, or matched targets when comparing trials.

# GNNExplainer-primary results

GXAttack-objective adaptation with differentiation through GNNExplainer mask fitting. Direct targeting is distinct from the original paper's PGExplainer targeting. Native PyG explanations score every candidate and all reported outcomes.

Current saved target-trial cases: 277. Check status.json for completion. Pilot/smoke data are validation-only, not final test results.

| Dataset | Method | Explainer | Binary top25 similarity | Label change fraction | Clean soft+ | Attacked soft+ |
|---|---|---|---:|---:|---:|---:|
| amlsim | Clean repeat | GNNExplainer | 0.30012 | 0.00000 | nan | nan |
| amlsim | GNN-targeted GX adaptation | GNNExplainer | 0.23407 | 0.00000 | 0.00176 | 0.00146 |
| amlsim | GNN-targeted GX adaptation | PGExplainer | 0.69658 | 0.00000 | 0.00001 | 0.00001 |
| amlsim | GNN-targeted GX adaptation | SubgraphX | 0.28675 | 0.00000 | 0.00943 | 0.00123 |
| amlsim | Random flipping | GNNExplainer | 0.53995 | 0.00000 | 0.00176 | 0.00164 |
| amlsim | Random rewiring | GNNExplainer | 0.44141 | 0.00000 | 0.00176 | 0.00150 |
| amlsim | Random search | GNNExplainer | 0.23461 | 0.00000 | 0.00176 | 0.00174 |

Soft values are signed probability differences, not percentage points. Clean repeat uses a different explanation seed; its fidelity fields are unavailable. Random search uses the same number of native candidate evaluations as the attack, but does not match gradient-computation effort. Features remain fixed.