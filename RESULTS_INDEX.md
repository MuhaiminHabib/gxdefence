# Saved experiment results

GitHub contains reports and aggregate CSVs. Raw graphs, model checkpoints and individual case files remain local. Running experiments are uploaded as snapshots, not live updates.

Read the [research objective, questions and claim register](RESEARCH_CONTRIBUTIONS.md) and the [1 November 2026 snapshot](publication_snapshots/2026-11-01/README.md) first. Later local progress is not automatically reflected on GitHub.

| Experiment | Coverage | Report |
|---|---|---|
| PGExplainer-targeted complete-graph study | Complete; five trials | [Report](complete_graphs/REPORT.md) |
| GNNExplainer-targeted AMLSim and HI-Small | Complete; 166 + 795 targets, three trials, 2,883 evaluations | [Tables](gnn_three_trials/results/full/TABLES_PAPER_LAYOUT.md) |
| SubgraphX-targeted AMLSim | Complete; 166 targets, three trials, 498 evaluations | [Report](subgraphx_primary/results/full/REPORT.md) |
| SubgraphX-targeted HI-Small | Incomplete; one trial planned over 795 targets. The dated copy is the latest uploaded snapshot. | [Dated report](publication_snapshots/2026-11-01/subgraphx_hi_small/REPORT.md), [dated coverage](publication_snapshots/2026-11-01/subgraphx_hi_small/coverage.json) |
| Fresh-seed GNN audit and random-explanation fidelity controls | Complete; 50 targets per dataset, five unseen seeds, 20 random explanation masks per graph | [Report](followup_audit/results/gnn_audit/REPORT.md) |
| AMLSim SubgraphX proposal-budget analysis | Complete retrospective analysis; 166 targets, three trials, 498 trajectories | [Report](followup_audit/results/search_budget/REPORT.md) |
| Deletion-only versus mixed access | Complete; 30 paired targets per dataset, one trial | [Report](deletion_access/results/full/REPORT.md) |
| Multigraph explanation-resolution diagnostic | Complete exploratory analysis; 500 mechanical comparisons, fresh-seed audit and larger retrospective cohorts | [Report](exploratory_multigraph_resolution/results/REPORT.md), [paired baseline analysis](exploratory_multigraph_resolution/results/PAIRED_BASELINE.md) |
| Fidelity-objective selector | Completed negative pilot; 20 targets per dataset, promotion criterion not met | [Report](exploratory_fidelity_objective/results/screening/REPORT.md) |
| Transaction-consistency study | Incomplete; code and protocol published, conclusions pending | [Protocol](exploratory_transaction_consistency/README.md) |
| Additional resolution/permutation validation | Incomplete; 50 additional targets per dataset planned | [Protocol](exploratory_resolution_validation/README.md) |
| Pattern-constrained explanation attacks | Incomplete; 10 targets per dataset in screening; conditional expansion only | [Protocol](exploratory_pattern_constraints/README.md) |
| Earlier HI-Small GNNExplainer preview | Complete; 30 targets, one trial; superseded by the full three-trial study | [Preview](hi_small_preview/results/preview/REPORT.md) |
| Earlier stopped AMLSim GNNExplainer run | Historical partial run; superseded by the full three-trial study | [Saved completed-trial report](gnn_primary/results/amlsim_stopped/REPORT.md) |

SubgraphX-targeted discrete search is a separate method, not original GXAttack. Its native selected-set overlap is different from the top-quarter or top-10 selections used for PGExplainer/GNNExplainer. Incomplete trial CSVs are provisional and must not be presented as completed-cohort averages. Pilot results use validation targets and are separate from full test evaluation.
