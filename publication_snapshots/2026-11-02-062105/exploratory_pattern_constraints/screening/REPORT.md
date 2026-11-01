# Exploratory graph-pattern constraints

**SCREENING COMPLETE: 20/20 target-search cases.**

Three record rewirings = six removed/inserted edge connections; best-of-40 random search versus the first structurally valid random candidate. Frozen features and model. Degree+cycle constraints preserve global multiplicity-weighted two/three-cycle totals, not every individual motif. Failure cases remain in joint denominators. Candidate-generation shortfalls and actual calls are recorded. Five fresh seeds are averaged within targets; expanded trials are also averaged within targets. Clean repeats are a variability reference, not a matched null.

| Dataset | Constraint | Selector | Targets | Feasible coverage | Joint disruption | Excess over clean repeat, 95% interval |
|---|---|---|---:|---:|---:|---|
| amlsim | degree | Best of 40 | 10 | 100.00% | 0.3641 | 0.1852 (0.1121, 0.2699) |
| amlsim | degree | First random candidate | 10 | 100.00% | 0.0456 | -0.1333 (-0.1917, -0.0595) |
| amlsim | degree_cycles | Best of 40 | 10 | 100.00% | 0.3696 | 0.1907 (0.1249, 0.2688) |
| amlsim | degree_cycles | First random candidate | 10 | 100.00% | 0.0788 | -0.1001 (-0.1727, -0.0174) |
| amlsim | source_fixed | Best of 40 | 10 | 100.00% | 0.2247 | 0.0457 (-0.0427, 0.1260) |
| amlsim | source_fixed | First random candidate | 10 | 100.00% | 0.0389 | -0.1400 (-0.2003, -0.0448) |
| hi_small | degree | Best of 40 | 10 | 90.00% | 0.3857 | 0.1205 (0.0353, 0.2318) |
| hi_small | degree | First random candidate | 10 | 80.00% | 0.2695 | 0.0425 (-0.0574, 0.1195) |
| hi_small | degree_cycles | Best of 40 | 10 | 90.00% | 0.3879 | 0.1228 (0.0407, 0.2340) |
| hi_small | degree_cycles | First random candidate | 10 | 80.00% | 0.2313 | 0.0044 (-0.1246, 0.1116) |
| hi_small | source_fixed | Best of 40 | 10 | 90.00% | 0.4543 | 0.1891 (0.0923, 0.2938) |
| hi_small | source_fixed | First random candidate | 10 | 80.00% | 0.1319 | -0.1033 (-0.2118, 0.0033) |

The prespecified primary endpoint is degree_cycles / Best of 40 excess disruption. Intervals omit graph-node dependence and model-training variation. Endpoint overlap is not explanation quality. No economic feasibility or feature consistency is claimed. Partial summaries are provisional; the gate is applied only after all screening targets.