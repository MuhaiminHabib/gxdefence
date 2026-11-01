# Exploratory graph-pattern constraints

**EXPANDED COMPLETE: 200/200 target-search cases.**

Three record rewirings = six removed/inserted edge connections; best-of-40 random search versus the first structurally valid random candidate. Frozen features and model. Degree+cycle constraints preserve global multiplicity-weighted two/three-cycle totals, not every individual motif. Failure cases remain in joint denominators. Candidate-generation shortfalls and actual calls are recorded. Five fresh seeds are averaged within targets; expanded trials are also averaged within targets. Clean repeats are a variability reference, not a matched null.

| Dataset | Constraint | Selector | Targets | Feasible coverage | Joint disruption | Excess over clean repeat, 95% interval |
|---|---|---|---:|---:|---:|---|
| amlsim | degree | Best of 40 | 50 | 100.00% | 0.3798 | 0.1948 (0.1661, 0.2233) |
| amlsim | degree | First random candidate | 50 | 100.00% | 0.0872 | -0.0978 (-0.1229, -0.0708) |
| amlsim | degree_cycles | Best of 40 | 50 | 100.00% | 0.3662 | 0.1812 (0.1538, 0.2096) |
| amlsim | degree_cycles | First random candidate | 50 | 99.00% | 0.1136 | -0.0694 (-0.0978, -0.0416) |
| amlsim | source_fixed | Best of 40 | 50 | 100.00% | 0.2911 | 0.1060 (0.0772, 0.1364) |
| amlsim | source_fixed | First random candidate | 50 | 99.00% | 0.0233 | -0.1598 (-0.1755, -0.1423) |
| hi_small | degree | Best of 40 | 50 | 79.00% | 0.4180 | 0.1831 (0.1121, 0.2574) |
| hi_small | degree | First random candidate | 50 | 54.00% | 0.1564 | 0.0025 (-0.0414, 0.0472) |
| hi_small | degree_cycles | Best of 40 | 50 | 75.00% | 0.3784 | 0.1555 (0.0893, 0.2238) |
| hi_small | degree_cycles | First random candidate | 50 | 55.00% | 0.1591 | 0.0018 (-0.0410, 0.0459) |
| hi_small | source_fixed | Best of 40 | 50 | 80.00% | 0.4336 | 0.1948 (0.1220, 0.2701) |
| hi_small | source_fixed | First random candidate | 50 | 69.00% | 0.1512 | -0.0529 (-0.1007, -0.0017) |

The prespecified primary endpoint is degree_cycles / Best of 40 excess disruption. Intervals omit graph-node dependence and model-training variation. Endpoint overlap is not explanation quality. No economic feasibility or feature consistency is claimed. Partial summaries are provisional; the gate is applied only after all screening targets.