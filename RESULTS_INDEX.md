# Saved experiment results

GitHub contains reports and aggregate CSVs. Raw graphs, model checkpoints and individual case files remain local. Running experiments are uploaded as snapshots, not live updates.

| Experiment | Coverage | Report |
|---|---|---|
| PGExplainer-targeted complete-graph study | Complete; five trials | [Report](complete_graphs/REPORT.md) |
| GNNExplainer-targeted AMLSim and HI-Small | Complete; 166 + 795 targets, three trials, 2,883 evaluations | [Tables](gnn_three_trials/results/full/TABLES_PAPER_LAYOUT.md) |
| SubgraphX-targeted AMLSim | Complete; 166 targets, three trials, 498 evaluations | [Report](subgraphx_primary/results/full/REPORT.md) |
| SubgraphX-targeted HI-Small | In progress; one trial planned over 795 targets. See coverage.json for the uploaded count. | [Report](subgraphx_hi_small/results/full/REPORT.md), [coverage](subgraphx_hi_small/results/full/coverage.json) |
| Earlier HI-Small GNNExplainer preview | Complete; 30 targets, one trial; superseded by the full three-trial study | [Preview](hi_small_preview/results/preview/REPORT.md) |
| Earlier stopped AMLSim GNNExplainer run | Historical partial run; superseded by the full three-trial study | [Saved completed-trial report](gnn_primary/results/amlsim_stopped/REPORT.md) |

SubgraphX-targeted discrete search is a separate method, not original GXAttack. Its native selected-set overlap is different from the top-quarter or top-10 selections used for PGExplainer/GNNExplainer. Incomplete trial CSVs are provisional and must not be presented as completed-cohort averages. Pilot results use validation targets and are separate from full test evaluation.
