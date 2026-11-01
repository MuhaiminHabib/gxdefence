# SubgraphX: deletion-only versus mixed edit access

**COMPLETE: 60/60 paired target cases.**

Six edits, 40 proposals per search method and access condition, one trial (2026). Same targets and frozen classifiers/features in both conditions. Predictions that change are retained. No between-trial SD is available.

| Dataset | Access | Method | Targets | Similarity | Label change | Probability change |
|---|---|---|---:|---:|---:|---:|
| amlsim | deletion_only | Adaptive search | 30 | 0.2468 | 0.0000 | 0.00078 |
| amlsim | deletion_only | Random flipping | 30 | 0.6754 | 0.0000 | 0.00004 |
| amlsim | deletion_only | Random search | 30 | 0.0991 | 0.0000 | 0.00028 |
| amlsim | mixed | Adaptive search | 30 | 0.0000 | 0.0000 | 0.00002 |
| amlsim | mixed | Random flipping | 30 | 0.2446 | 0.0000 | 0.00019 |
| amlsim | mixed | Random search | 30 | 0.0000 | 0.0000 | 0.00019 |
| hi_small | deletion_only | Adaptive search | 30 | 0.3783 | 0.0000 | 0.02214 |
| hi_small | deletion_only | Random flipping | 30 | 0.7415 | 0.0000 | 0.00810 |
| hi_small | deletion_only | Random search | 30 | 0.3039 | 0.0000 | 0.01856 |
| hi_small | mixed | Adaptive search | 30 | 0.2064 | 0.0000 | 0.01811 |
| hi_small | mixed | Random flipping | 30 | 0.5455 | 0.0000 | 0.01920 |
| hi_small | mixed | Random search | 30 | 0.1311 | 0.0000 | 0.01769 |

| Dataset | Method | Deletion-minus-mixed similarity | 95% target-resampling interval |
|---|---|---:|---:|
| amlsim | Adaptive search | 0.2468 | (0.1128, 0.3916) |
| amlsim | Random flipping | 0.4308 | (0.2426, 0.6116) |
| amlsim | Random search | 0.0991 | (0.0000, 0.2000) |
| hi_small | Adaptive search | 0.1719 | (0.0664, 0.2820) |
| hi_small | Random flipping | 0.1959 | (0.0271, 0.3586) |
| hi_small | Random search | 0.1728 | (0.0815, 0.2751) |

Positive paired similarity differences mean less disruption with deletion-only access. Intervals are conditional target resampling; they do not account for dependence between connected nodes or classifier-training variation. All-target tables are primary; paired both-preserved analyses are separately saved. Empty explanations and direct deletion of explanatory edges are reported in CSVs. Restricted common-original-edge overlap is supplementary, not a replacement for native-set overlap.

The experiment uses graph-store corruption with frozen transaction-derived features. It does not establish economic feasibility, human deception, explanation accuracy, a defense, or a black-box attack. Both search conditions are newly executed. Proposals and unique explainer evaluations differ because duplicate candidates are cached.

Mean completed paired-case runtime: 164.5 seconds.