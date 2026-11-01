# Multigraph explanation-resolution audit

**COMPLETE. Separate exploratory retrospective analysis.**

This is a representation-equivalence diagnostic, not a new attack or a corrected success rate. Matching can only increase overlap by construction. For GNN masks it uses original rows available in both input pools and retains the original selected-cardinality denominator. Features remain frozen.

| Scope | Dataset | Method | Selection | Targets | Row overlap | Matched overlap | Gap, 95% target interval |
|---|---|---|---|---:|---:|---:|---|
| Fresh seed audit | amlsim | Clean repeat | top10 | 50 | 0.0148 | 0.3396 | 0.3248 (0.2916, 0.3580) |
| Fresh seed audit | amlsim | Clean repeat | top25 | 50 | 0.2939 | 0.8254 | 0.5315 (0.5215, 0.5414) |
| Fresh seed audit | amlsim | GNN-targeted GX adaptation | top10 | 50 | 0.0184 | 0.2480 | 0.2296 (0.2032, 0.2576) |
| Fresh seed audit | amlsim | GNN-targeted GX adaptation | top25 | 50 | 0.2471 | 0.7004 | 0.4533 (0.4351, 0.4708) |
| Fresh seed audit | amlsim | Random flipping | top10 | 50 | 0.3524 | 0.5392 | 0.1868 (0.1476, 0.2256) |
| Fresh seed audit | amlsim | Random flipping | top25 | 50 | 0.5265 | 0.8576 | 0.3312 (0.2739, 0.3848) |
| Fresh seed audit | amlsim | Random search | top10 | 50 | 0.0140 | 0.2504 | 0.2364 (0.2096, 0.2632) |
| Fresh seed audit | amlsim | Random search | top25 | 50 | 0.2443 | 0.6958 | 0.4514 (0.4286, 0.4716) |
| Fresh seed audit | hi_small | Clean repeat | top10 | 50 | 0.2916 | 0.6308 | 0.3392 (0.2980, 0.3796) |
| Fresh seed audit | hi_small | Clean repeat | top25 | 50 | 0.3574 | 0.6980 | 0.3406 (0.3042, 0.3755) |
| Fresh seed audit | hi_small | GNN-targeted GX adaptation | top10 | 50 | 0.2394 | 0.3858 | 0.1464 (0.1080, 0.1868) |
| Fresh seed audit | hi_small | GNN-targeted GX adaptation | top25 | 50 | 0.3064 | 0.4673 | 0.1609 (0.1292, 0.1942) |
| Fresh seed audit | hi_small | Random flipping | top10 | 50 | 0.5176 | 0.7056 | 0.1880 (0.1448, 0.2332) |
| Fresh seed audit | hi_small | Random flipping | top25 | 50 | 0.5504 | 0.7449 | 0.1944 (0.1529, 0.2373) |
| Fresh seed audit | hi_small | Random search | top10 | 50 | 0.1982 | 0.3450 | 0.1468 (0.1072, 0.1872) |
| Fresh seed audit | hi_small | Random search | top25 | 50 | 0.2632 | 0.4173 | 0.1542 (0.1230, 0.1857) |
| Full three-trial GNN | amlsim | Clean repeat | top10 | 166 | 0.0444 | 0.3269 | 0.2825 (0.2645, 0.3006) |
| Full three-trial GNN | amlsim | Clean repeat | top25 | 166 | 0.3050 | 0.8187 | 0.5136 (0.5069, 0.5202) |
| Full three-trial GNN | amlsim | GNN-targeted GX adaptation | top10 | 166 | 0.0161 | 0.2365 | 0.2205 (0.2050, 0.2355) |
| Full three-trial GNN | amlsim | GNN-targeted GX adaptation | top25 | 166 | 0.2374 | 0.6673 | 0.4299 (0.4188, 0.4408) |
| Full three-trial GNN | amlsim | Random flipping | top10 | 166 | 0.3727 | 0.5406 | 0.1679 (0.1494, 0.1867) |
| Full three-trial GNN | amlsim | Random flipping | top25 | 166 | 0.5588 | 0.8559 | 0.2971 (0.2782, 0.3156) |
| Full three-trial GNN | amlsim | Random rewiring | top10 | 166 | 0.2024 | 0.4026 | 0.2002 (0.1845, 0.2161) |
| Full three-trial GNN | amlsim | Random rewiring | top25 | 166 | 0.4418 | 0.8257 | 0.3839 (0.3724, 0.3952) |
| Full three-trial GNN | amlsim | Random search | top10 | 166 | 0.0145 | 0.2295 | 0.2151 (0.2004, 0.2305) |
| Full three-trial GNN | amlsim | Random search | top25 | 166 | 0.2415 | 0.6760 | 0.4345 (0.4227, 0.4457) |
| Full three-trial GNN | hi_small | Clean repeat | top10 | 795 | 0.3228 | 0.6788 | 0.3560 (0.3447, 0.3673) |
| Full three-trial GNN | hi_small | Clean repeat | top25 | 795 | 0.3830 | 0.7182 | 0.3352 (0.3249, 0.3456) |
| Full three-trial GNN | hi_small | GNN-targeted GX adaptation | top10 | 795 | 0.1835 | 0.3865 | 0.2030 (0.1917, 0.2148) |
| Full three-trial GNN | hi_small | GNN-targeted GX adaptation | top25 | 795 | 0.2482 | 0.4635 | 0.2153 (0.2044, 0.2262) |
| Full three-trial GNN | hi_small | Random flipping | top10 | 795 | 0.4919 | 0.7034 | 0.2115 (0.2013, 0.2220) |
| Full three-trial GNN | hi_small | Random flipping | top25 | 795 | 0.5288 | 0.7367 | 0.2079 (0.1983, 0.2173) |
| Full three-trial GNN | hi_small | Random rewiring | top10 | 795 | 0.3836 | 0.6322 | 0.2486 (0.2390, 0.2586) |
| Full three-trial GNN | hi_small | Random rewiring | top25 | 795 | 0.4398 | 0.6721 | 0.2324 (0.2241, 0.2405) |
| Full three-trial GNN | hi_small | Random search | top10 | 795 | 0.1626 | 0.3327 | 0.1701 (0.1596, 0.1804) |
| Full three-trial GNN | hi_small | Random search | top25 | 795 | 0.2292 | 0.4112 | 0.1820 (0.1721, 0.1917) |
| Native SubgraphX control | amlsim | Random flipping | native | 166 | 0.3339 | 0.3339 | 0.0000 (0.0000, 0.0000) |
| Native SubgraphX control | amlsim | Random rewiring | native | 166 | 0.3767 | 0.3767 | 0.0000 (0.0000, 0.0000) |
| Native SubgraphX control | amlsim | Random search | native | 166 | 0.0013 | 0.0013 | 0.0000 (0.0000, 0.0000) |
| Native SubgraphX control | amlsim | SubgraphX-targeted search | native | 166 | 0.0039 | 0.0039 | 0.0000 (0.0000, 0.0000) |

## Mechanical zero-transaction-edit controls

| Dataset | Compared sets | Sets with changed row IDs | Mean row overlap | Maximum logit difference |
|---|---:|---:|---:|---:|
| amlsim | 250 | 250 | 0.0233 | 1.43e-06 |
| hi_small | 250 | 247 | 0.2781 | 2.38e-07 |

Equivalent sets are constructed alternatives to saved clean top-25% explanations, not independent outputs from an explainer. They preserve the number of selected rows at each ordered endpoint pair; removal and retention logits both pass numerical parity. Node features stay fixed. Actual transaction amounts/times need not be equivalent; re-extracting their account aggregates can break the property.

Native SubgraphX retains whole induced edge groups. Its permissive pair-count bound is a negative control. The full three-trial cohort overlaps the preliminary fresh-seed cohort, so it is not independent confirmation. Intervals average seeds/trials within targets and omit graph-node dependence and model-training variation.

Symmetry-aware explanation reporting is prior work: Crabbé and van der Schaar (NeurIPS 2023), https://arxiv.org/abs/2304.06715; Xu et al. (2026 preprint), https://arxiv.org/abs/2607.26344. The candidate contribution is its measured relevance to financial multigraph attack evaluation.