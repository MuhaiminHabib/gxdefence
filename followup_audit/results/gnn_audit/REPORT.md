# Fresh-seed and random-explanation audit

**COMPLETE: 100/100 preselected targets saved.**

Source attack trial 2026; five fresh paired explanation seeds per target. One classifier per dataset. Target-subset selection was independent of attack outcomes. No attack optimization was repeated. Technical validation checks native-mask, saved-mask, probability and physical-fidelity parity. All results remain conditional on these frozen graphs and classifiers.

| Dataset | Method | Targets | Selection-seed similarity | Fresh-seed similarity | Fresh clean-repeat similarity |
|---|---|---:|---:|---:|---:|
| amlsim | GNN-targeted GX adaptation | 50 | 0.2451 | 0.2471 | 0.2939 |
| amlsim | Random flipping | 50 | 0.5240 | 0.5265 | 0.2939 |
| amlsim | Random search | 50 | 0.2439 | 0.2443 | 0.2939 |
| hi_small | GNN-targeted GX adaptation | 50 | 0.2591 | 0.3064 | 0.3574 |
| hi_small | Random flipping | 50 | 0.5560 | 0.5504 | 0.3574 |
| hi_small | Random search | 50 | 0.2164 | 0.2632 | 0.3574 |

Fresh-seed similarity compares clean/attacked graphs using the same unseen seed. Clean-repeat similarity uses independent seeds on the unchanged graph; it is a variability reference, not a perfectly matched null for the paired statistic. Higher fresh-minus-selection similarity indicates reduced disruption under fresh randomness. It does not alone establish attack failure.

| Dataset | Method | Clean excess soft necessity (pp) | Attacked excess soft necessity (pp) | Paired change (pp) |
|---|---|---:|---:|---:|
| amlsim | GNN-targeted GX adaptation | 0.0473 | 0.0436 | -0.0038 |
| amlsim | Random flipping | 0.0473 | 0.0442 | -0.0031 |
| amlsim | Random search | 0.0473 | 0.0249 | -0.0224 |
| hi_small | GNN-targeted GX adaptation | 0.6799 | 3.1886 | 2.5088 |
| hi_small | Random flipping | 0.6799 | 2.0766 | 1.3968 |
| hi_small | Random search | 0.6799 | 1.6134 | 0.9335 |

Excess soft necessity is explainer removal-induced probability drop minus the mean for 20 uniform size-matched edge sets on the same graph. Negative paired change means a smaller advantage over random edges after attack. This controls size, not connectivity or degree, and does not fix distribution-shift concerns of edge-removal fidelity. Signed values are retained. The 20 subsets are Monte Carlo controls, not independent targets.

CSV summaries include hard/soft necessity and sufficiency-failure, unconditional and label-preserved results, and 95% target-resampling intervals. Repeated seeds are averaged before resampling; graph-node dependence and model-training uncertainty are not represented. Do not infer statistical superiority from overlapping/unpaired marginal intervals.

Mean saved target runtime: 11.8 seconds. Existing HI-Small SubgraphX source and output files were not modified.