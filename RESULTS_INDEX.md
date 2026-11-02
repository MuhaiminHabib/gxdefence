# Saved experiment results

GitHub contains reports and aggregate CSVs. Raw graphs, model checkpoints and individual case files remain local. Running experiments are uploaded as snapshots, not live updates.

Read the [research objective, questions and claim register](RESEARCH_CONTRIBUTIONS.md) and the [2 November 2026 completed snapshot](publication_snapshots/2026-11-02-102453/README.md) first. Reports were rebuilt from verified saved cases. All phases in that snapshot are complete; earlier partial snapshots remain preserved.

| Experiment | Coverage | Report |
|---|---|---|
| PGExplainer-targeted complete-graph study | Complete; five trials | [Report](complete_graphs/REPORT.md) |
| GNNExplainer-targeted AMLSim and HI-Small | Complete; 166 + 795 targets, three trials, 2,883 evaluations | [Tables](gnn_three_trials/results/full/TABLES_PAPER_LAYOUT.md) |
| SubgraphX-targeted AMLSim | Complete; 166 targets, three trials, 498 evaluations | [Report](subgraphx_primary/results/full/REPORT.md) |
| SubgraphX-targeted HI-Small | Complete; 795/795 targets in one trial. Final overlap and fidelity tables are available; between-trial uncertainty is unavailable. | [Completed report](publication_snapshots/2026-11-02-102453/subgraphx_hi_small/REPORT.md), [verified coverage](publication_snapshots/2026-11-02-102453/subgraphx_hi_small/coverage.json) |
| Fresh-seed GNN audit and random-explanation fidelity controls | Complete; 50 targets per dataset, five unseen seeds, 20 random explanation masks per graph | [Report](followup_audit/results/gnn_audit/REPORT.md) |
| Fresh-seed SubgraphX audit on HI-Small | Complete; 100 preselected targets, five unseen paired seeds, fixed adaptive/random-search attacks. Attenuation with residual overlap disruption; fresh method-comparison interval includes zero. | [Report](publication_snapshots/2026-11-02-102453/exploratory_subgraphx_fresh_seed/REPORT.md), [validation](publication_snapshots/2026-11-02-102453/exploratory_subgraphx_fresh_seed/validation_summary.json), [separate protocol](exploratory_subgraphx_fresh_seed/README.md) |
| AMLSim SubgraphX proposal-budget analysis | Complete retrospective analysis; 166 targets, three trials, 498 trajectories | [Report](followup_audit/results/search_budget/REPORT.md) |
| Deletion-only versus mixed access | Complete; 30 paired targets per dataset, one trial | [Report](deletion_access/results/full/REPORT.md) |
| Multigraph explanation-resolution diagnostic | Complete exploratory analysis; 500 mechanical comparisons, fresh-seed audit and larger retrospective cohorts | [Report](exploratory_multigraph_resolution/results/REPORT.md), [paired baseline analysis](exploratory_multigraph_resolution/results/PAIRED_BASELINE.md) |
| Fidelity-objective selector | Completed negative pilot; 20 targets per dataset, promotion criterion not met | [Report](exploratory_fidelity_objective/results/screening/REPORT.md) |
| Transaction-consistency study | Complete pilot; 20 targets per dataset. Primary expansion criterion failed; secondary fidelity differences reported separately. | [Report](publication_snapshots/2026-11-02-102453/exploratory_transaction_consistency/pilot/REPORT.md), [decision](publication_snapshots/2026-11-02-102453/exploratory_transaction_consistency/promotion_decision.json) |
| Additional resolution/permutation validation | Complete; 50 additional targets per dataset, five new seeds, 500 native permutation comparisons | [Report](publication_snapshots/2026-11-02-102453/exploratory_resolution_validation/REPORT.md) |
| Pattern-constrained explanation attacks: screening | Complete; 10 targets per dataset; both passed the prespecified expansion gate | [Screening report](publication_snapshots/2026-11-02-102453/exploratory_pattern_constraints/screening/REPORT.md) |
| Pattern-constrained explanation attacks: expansion | Complete; 50 separate targets per dataset, two search trials, 200/200 cases. Degree/cycle-constrained feasible coverage: 100/100 AMLSim and 75/100 HI-Small search cases. | [Completed report](publication_snapshots/2026-11-02-102453/exploratory_pattern_constraints/expanded/REPORT.md), [validation](publication_snapshots/2026-11-02-102453/exploratory_pattern_constraints/expanded/validation_summary.json) |
| Earlier HI-Small GNNExplainer preview | Complete; 30 targets, one trial; superseded by the full three-trial study | [Preview](hi_small_preview/results/preview/REPORT.md) |
| Earlier stopped AMLSim GNNExplainer run | Historical partial run; superseded by the full three-trial study | [Saved completed-trial report](gnn_primary/results/amlsim_stopped/REPORT.md) |

SubgraphX-targeted discrete search is a separate method, not original GXAttack. Its native selected-set overlap is different from the top-quarter or top-10 selections used for PGExplainer/GNNExplainer. Incomplete trial CSVs are provisional and must not be presented as completed-cohort averages. Pilot results use validation targets and are separate from full test evaluation.
