# Exploratory graph-pattern constraints

**EXPANDED PROVISIONAL: 10/200 target-search cases.**

Three record rewirings = six removed/inserted edge connections; best-of-40 random search versus the first structurally valid random candidate. Frozen features and model. Degree+cycle constraints preserve global multiplicity-weighted two/three-cycle totals, not every individual motif. Failure cases remain in joint denominators. Candidate-generation shortfalls and actual calls are recorded. Five fresh seeds are averaged within targets; expanded trials are also averaged within targets. Clean repeats are a variability reference, not a matched null.

| Dataset | Constraint | Selector | Targets | Feasible coverage | Joint disruption | Excess over clean repeat, 95% interval |
|---|---|---|---:|---:|---:|---|
| amlsim | degree | Best of 40 | 10 | 100.00% | 0.3462 | 0.1703 (0.1015, 0.2459) |
| amlsim | degree | First random candidate | 10 | 100.00% | 0.0578 | -0.1181 (-0.1696, -0.0622) |
| amlsim | degree_cycles | Best of 40 | 10 | 100.00% | 0.3701 | 0.1942 (0.1280, 0.2648) |
| amlsim | degree_cycles | First random candidate | 10 | 100.00% | 0.0453 | -0.1306 (-0.1760, -0.0791) |
| amlsim | source_fixed | Best of 40 | 10 | 100.00% | 0.2889 | 0.1130 (0.0381, 0.2025) |
| amlsim | source_fixed | First random candidate | 10 | 100.00% | 0.0472 | -0.1287 (-0.1824, -0.0430) |

The prespecified primary endpoint is degree_cycles / Best of 40 excess disruption. Intervals omit graph-node dependence and model-training variation. Endpoint overlap is not explanation quality. No economic feasibility or feature consistency is claimed. Partial summaries are provisional; the gate is applied only after all screening targets.