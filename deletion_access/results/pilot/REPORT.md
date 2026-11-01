# SubgraphX: deletion-only versus mixed edit access

**COMPLETE: 2/2 paired target cases.**

Six edits, 40 proposals per search method and access condition, one trial (2026). Same targets and frozen classifiers/features in both conditions. Predictions that change are retained. No between-trial SD is available.

| Dataset | Access | Method | Targets | Similarity | Label change | Probability change |
|---|---|---|---:|---:|---:|---:|
| amlsim | deletion_only | Adaptive search | 1 | 0.0000 | 0.0000 | 0.00000 |
| amlsim | deletion_only | Random flipping | 1 | 1.0000 | 0.0000 | 0.00000 |
| amlsim | deletion_only | Random search | 1 | 0.0000 | 0.0000 | 0.00000 |
| amlsim | mixed | Adaptive search | 1 | 0.0000 | 0.0000 | 0.00000 |
| amlsim | mixed | Random flipping | 1 | 0.0000 | 0.0000 | 0.00000 |
| amlsim | mixed | Random search | 1 | 0.0000 | 0.0000 | 0.00000 |
| hi_small | deletion_only | Adaptive search | 1 | 0.0000 | 0.0000 | 0.20992 |
| hi_small | deletion_only | Random flipping | 1 | 1.0000 | 0.0000 | 0.00185 |
| hi_small | deletion_only | Random search | 1 | 0.0000 | 0.0000 | 0.10632 |
| hi_small | mixed | Adaptive search | 1 | 0.0000 | 0.0000 | 0.00519 |
| hi_small | mixed | Random flipping | 1 | 0.3381 | 0.0000 | 0.04795 |
| hi_small | mixed | Random search | 1 | 0.0000 | 0.0000 | 0.01168 |

| Dataset | Method | Deletion-minus-mixed similarity | 95% target-resampling interval |
|---|---|---:|---:|
| amlsim | Adaptive search | 0.0000 | (0.0000, 0.0000) |
| amlsim | Random flipping | 1.0000 | (1.0000, 1.0000) |
| amlsim | Random search | 0.0000 | (0.0000, 0.0000) |
| hi_small | Adaptive search | 0.0000 | (0.0000, 0.0000) |
| hi_small | Random flipping | 0.6619 | (0.6619, 0.6619) |
| hi_small | Random search | 0.0000 | (0.0000, 0.0000) |

Positive paired similarity differences mean less disruption with deletion-only access. Intervals are conditional target resampling; they do not account for dependence between connected nodes or classifier-training variation. All-target tables are primary; paired both-preserved analyses are separately saved. Empty explanations and direct deletion of explanatory edges are reported in CSVs. Restricted common-original-edge overlap is supplementary, not a replacement for native-set overlap.

The experiment uses graph-store corruption with frozen transaction-derived features. It does not establish economic feasibility, human deception, explanation accuracy, a defense, or a black-box attack. Both search conditions are newly executed. Proposals and unique explainer evaluations differ because duplicate candidates are cached.

Mean completed paired-case runtime: 250.1 seconds.