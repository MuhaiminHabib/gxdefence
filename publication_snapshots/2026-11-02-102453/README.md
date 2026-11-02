# Latest results snapshot: 2026-11-02-102453

Capture began **2026-11-02T10:24:53+08:00** (Australia/Perth).

Reports were rebuilt in an isolated temporary directory from verified copies of saved cases. Live study outputs were not edited. Source/input hashes, target membership and case identities were checked. The resolution audit includes all five fresh seeds per target; the selected degree/cycle attacks have independent cycle-check records. Completed screening promotion decisions agree with recomputed summaries.

| Experiment / phase | Saved / planned | Interpretation | Report |
|---|---:|---|---|
| exploratory_resolution_validation | 100/100 | Complete | [Report](exploratory_resolution_validation/REPORT.md) |
| exploratory_pattern_constraints/screening | 20/20 | Complete | [Report](exploratory_pattern_constraints/screening/REPORT.md) |
| exploratory_pattern_constraints/expanded | 200/200 | Complete | [Report](exploratory_pattern_constraints/expanded/REPORT.md) |
| exploratory_transaction_consistency/pilot | 40/40 | Complete | [Report](exploratory_transaction_consistency/pilot/REPORT.md) |
| subgraphx_hi_small | 795/795 | Complete | [Report](subgraphx_hi_small/REPORT.md) |
| exploratory_subgraphx_fresh_seed | 100/100 | Complete | [Report](exploratory_subgraphx_fresh_seed/REPORT.md) |

The pattern expansion is complete: 50 separate targets per dataset, two search trials per target and five fresh explainer seeds per trial. Seeds and trials are averaged within targets for uncertainty estimates; screening and expansion remain separate. Transaction-consistency pilot completeness is determined by its coverage row; its verified promotion decision is published separately. HI-Small SubgraphX is complete: 795/795 targets in one trial. The final report includes native-set overlap and fidelity; between-trial uncertainty is unavailable.

The additional resolution cohort excludes the original fresh-seed cohort but was included in the earlier retrospective aggregates. It supplies new explainer draws and native permutation controls, not an independent dataset or trained-model replication.

[Updated contribution register](../../RESEARCH_CONTRIBUTIONS.md) | [Case/input hash manifest](snapshot.json)

Raw datasets, checkpoints, per-target records and machine logs remain local. Case hashes identify the exact saved inputs. Previous publication snapshots are preserved in sibling directories. Later live progress requires another upload.

The separate HI-Small SubgraphX fresh-seed audit evaluates fixed saved attacks on 100 sampled targets with five unseen paired seeds. It measures seed attenuation and residual overlap disruption, not a new attack-search trial or an independent trained-model replication. Its validation summary verifies the file-lock recovery and unchanged completed cases.
