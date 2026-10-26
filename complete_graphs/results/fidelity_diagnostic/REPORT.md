# Fidelity diagnostic pilot

Ten reproducibly sampled eligible targets per dataset; saved trial 2026. PGExplainer and GNNExplainer, clean and GXAttack graphs. No retraining, new attacks or protocol tuning. These descriptive pilot means are not full-cohort estimates.

## Independent verification

Physical full-graph removal/retention matched local two-hop evaluation for every selected set. Maximum absolute logit difference: 1.9073486e-06. Saved top-10 hard and soft metrics reproduced within 0.0003; model weights unchanged.

Soft+ = probability before minus probability after removing explanation edges. Soft- = probability before minus probability after keeping only explanation edges. Both are signed and reference each graph's original predicted class; negative values mean probability increased. Hard metrics count class changes.

## Results

| Dataset | Explainer | Graph | Selection | Mean edges | Hard+ | Hard- | Soft+ | Soft- |
|---|---|---|---|---:|---:|---:|---:|---:|
| amlsim | GNNExplainer | GXAttack | top10 | 10.00 | 0.0000 | 0.0000 | 0.00000 | -0.00262 |
| amlsim | GNNExplainer | GXAttack | top20 | 20.00 | 0.0000 | 0.1000 | -0.00022 | 0.07242 |
| amlsim | GNNExplainer | GXAttack | top25pct | 245.60 | 0.0000 | 0.0000 | 0.00024 | 0.00021 |
| amlsim | GNNExplainer | GXAttack | top5 | 5.00 | 0.0000 | 0.0000 | -0.00000 | -0.00136 |
| amlsim | GNNExplainer | clean | top10 | 10.00 | 0.0000 | 0.0000 | 0.00000 | -0.00342 |
| amlsim | GNNExplainer | clean | top20 | 20.00 | 0.0000 | 0.0000 | 0.00002 | -0.00396 |
| amlsim | GNNExplainer | clean | top25pct | 241.20 | 0.0000 | 0.0000 | 0.00024 | 0.02411 |
| amlsim | GNNExplainer | clean | top5 | 5.00 | 0.0000 | 0.0000 | 0.00000 | -0.00233 |
| amlsim | PGExplainer | GXAttack | top10 | 10.00 | 0.0000 | 0.0000 | 0.00004 | -0.00363 |
| amlsim | PGExplainer | GXAttack | top20 | 20.00 | 0.0000 | 0.0000 | 0.00004 | -0.00363 |
| amlsim | PGExplainer | GXAttack | top25pct | 245.60 | 0.0000 | 0.0000 | -0.00012 | -0.00363 |
| amlsim | PGExplainer | GXAttack | top5 | 5.00 | 0.0000 | 0.0000 | 0.00009 | -0.00363 |
| amlsim | PGExplainer | clean | top10 | 10.00 | 0.0000 | 0.0000 | -0.00004 | -0.00460 |
| amlsim | PGExplainer | clean | top20 | 20.00 | 0.0000 | 0.0000 | -0.00003 | -0.00460 |
| amlsim | PGExplainer | clean | top25pct | 241.20 | 0.0000 | 0.0000 | -0.00043 | -0.00460 |
| amlsim | PGExplainer | clean | top5 | 5.00 | 0.0000 | 0.0000 | -0.00005 | -0.00460 |
| hi_small | GNNExplainer | GXAttack | top10 | 9.70 | 0.0000 | 0.2000 | 0.02327 | 0.07652 |
| hi_small | GNNExplainer | GXAttack | top20 | 18.70 | 0.0000 | 0.0000 | 0.09614 | -0.00912 |
| hi_small | GNNExplainer | GXAttack | top25pct | 21.30 | 0.1000 | 0.1000 | 0.02829 | 0.07826 |
| hi_small | GNNExplainer | GXAttack | top5 | 5.00 | 0.0000 | 0.2000 | 0.01005 | 0.07225 |
| hi_small | GNNExplainer | clean | top10 | 9.70 | 0.0000 | 0.1000 | 0.02085 | 0.03820 |
| hi_small | GNNExplainer | clean | top20 | 18.70 | 0.0000 | 0.0000 | 0.06550 | -0.00240 |
| hi_small | GNNExplainer | clean | top25pct | 21.80 | 0.0000 | 0.1000 | 0.02417 | 0.10640 |
| hi_small | GNNExplainer | clean | top5 | 5.00 | 0.1000 | 0.0000 | 0.02945 | 0.02539 |
| hi_small | PGExplainer | GXAttack | top10 | 9.70 | 0.0000 | 0.0000 | 0.01652 | 0.01852 |
| hi_small | PGExplainer | GXAttack | top20 | 18.70 | 0.0000 | 0.0000 | 0.03387 | -0.00428 |
| hi_small | PGExplainer | GXAttack | top25pct | 21.30 | 0.1000 | 0.0000 | 0.06043 | 0.00734 |
| hi_small | PGExplainer | GXAttack | top5 | 5.00 | 0.0000 | 0.0000 | 0.01660 | 0.01852 |
| hi_small | PGExplainer | clean | top10 | 9.70 | 0.0000 | 0.0000 | 0.02283 | -0.00060 |
| hi_small | PGExplainer | clean | top20 | 18.70 | 0.1000 | 0.0000 | 0.05304 | -0.01733 |
| hi_small | PGExplainer | clean | top25pct | 21.80 | 0.0000 | 0.0000 | 0.01912 | 0.00167 |
| hi_small | PGExplainer | clean | top5 | 5.00 | 0.1000 | 0.0000 | 0.03626 | -0.00264 |

## Removing every graph edge

| Dataset | Targets retaining label | Mean clean probability | Mean no-edge probability |
|---|---:|---:|---:|
| amlsim | 10/10 | 0.99516 | 0.99976 |
| hi_small | 10/10 | 0.70229 | 0.68640 |

Removing every edge leaves node features and the trained GraphSAGE root transformations intact. This is an inference-time ablation, not a separately trained feature-only baseline. HI-Small features themselves aggregate transaction activity, so it does not demonstrate independence from transaction information. Larger explanation sets are exploratory sensitivity checks, not a selected new evaluation protocol.

## Interpretation and next decision

- No edge-removal or local-versus-full evaluation error was detected in this pilot. This is a sampled audit, not proof for every possible graph or model.
- All 20 sampled targets retained their illicit class after every edge was removed. The frozen model can therefore retain these decisions using the remaining features/root transformations; this is evidence relevant to low hard necessity, not proof it ignores graph structure generally.
- AMLSim clean confidence averaged 0.99516 and increased to 0.99976 without edges. Its soft necessity was also near zero for the tested explanation sizes, so the issue is not solely the hard classification threshold.
- HI-Small clean top-10 PG soft necessity was 0.02283 (2.283 percentage points) despite zero hard necessity in the sample. After attack it was 0.01652. Clean GNN soft necessity was 0.02085 and attacked was 0.02327, illustrating mixed attack effects.
- Increasing size from top-10 to top-20 raised clean HI-Small PG soft necessity from 0.02283 to 0.05304, with hard necessity increasing from 0 to 0.1. The effect is not monotonic across all sizes and explainers. Top-25% varies per target and is not necessarily larger than top-20.
- Do not choose a new explanation size to maximize a test-set result. Retain predefined reporting sizes and expand soft-fidelity summaries across the existing cohort. Assess both probability and label outcomes before selecting or evaluating robustness methods.
- The next method-comparison stage remains pending; no defence was trained or evaluated during this audit.
