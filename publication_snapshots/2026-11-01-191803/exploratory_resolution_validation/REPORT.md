# Additional fresh-randomness resolution audit

**COMPLETE: 100/100 targets.**

Targets exclude the original fresh-seed cohort but were part of the retrospective aggregate audit. All fresh and permutation explanations are newly evaluated. Clean repeats are a variability reference, not a perfectly matched null. Matching is a conditional diagnostic, not corrected accuracy.

| Dataset | Method | Selection | Targets | Row excess disruption | Matched excess | Change, 95% target interval |
|---|---|---|---:|---:|---:|---|
| amlsim | GNN-targeted GX adaptation | top10 | 50 | 0.0196 | 0.1340 | 0.1144 (0.0844, 0.1448) |
| amlsim | Random search | top10 | 50 | 0.0216 | 0.1172 | 0.0956 (0.0600, 0.1328) |
| amlsim | Random flipping | top10 | 50 | -0.2452 | -0.1336 | 0.1116 (0.0748, 0.1488) |
| amlsim | GNN-targeted GX adaptation | top25 | 50 | 0.0542 | 0.1666 | 0.1123 (0.0905, 0.1337) |
| amlsim | Random search | top25 | 50 | 0.0511 | 0.1608 | 0.1097 (0.0882, 0.1329) |
| amlsim | Random flipping | top25 | 50 | -0.2212 | -0.0338 | 0.1874 (0.1445, 0.2343) |
| hi_small | GNN-targeted GX adaptation | top10 | 50 | 0.1149 | 0.2401 | 0.1252 (0.0792, 0.1724) |
| hi_small | Random search | top10 | 50 | 0.1148 | 0.2988 | 0.1840 (0.1368, 0.2360) |
| hi_small | Random flipping | top10 | 50 | -0.1545 | -0.0365 | 0.1180 (0.0764, 0.1608) |
| hi_small | GNN-targeted GX adaptation | top25 | 50 | 0.0860 | 0.2114 | 0.1254 (0.0898, 0.1671) |
| hi_small | Random search | top25 | 50 | 0.0924 | 0.2550 | 0.1626 (0.1203, 0.2063) |
| hi_small | Random flipping | top25 | 50 | -0.1357 | -0.0115 | 0.1242 (0.0875, 0.1634) |

Primary endpoint is GNN-targeted top-25% contrast change; all other endpoints are secondary. Seeds are averaged within targets. Intervals omit graph-node dependence and training variation. Permutation outputs, original masks, top-10 fidelity and checks are in individual case files.