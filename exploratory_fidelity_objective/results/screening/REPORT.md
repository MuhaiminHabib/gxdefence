# EXPLORATORY: candidate-selection objective comparison

**SCREENING - COMPLETE: 40/40 target-search cases; 40 with a feasible candidate.**

Separate from the main study. Common 40-candidate pools, six edits, unchanged class, probability gap <= 0.02 and exactly ten selected explanation edges. No-feasible-candidate cases remain in coverage. Selection-seed objective improvement is expected by construction and is not evidence for promotion. All comparisons below use fresh explanation seeds.

| Dataset | Comparator | Paired extra necessity reduction (pp) | 95% interval (pp) | Random-adjusted advantage (pp) |
|---|---|---:|---:|---:|
| amlsim | Cosine selector | -0.0669 | (-0.2262, 0.0256) | -0.0673 |
| amlsim | First feasible candidate | -0.0043 | (-0.0314, 0.0246) | 0.0061 |
| hi_small | Cosine selector | -0.0472 | (-1.3578, 1.4673) | -0.6951 |
| hi_small | First feasible candidate | 0.5347 | (-1.1250, 2.3732) | 0.0139 |

Positive values indicate larger soft-necessity reduction for the necessity selector. These are conditional descriptive intervals from target resampling; they omit graph-node dependence and classifier-training variation. Random-adjusted values subtract size-matched random-mask necessity within each graph. Soft necessity is one metric, not explanation accuracy or a universal quality measure. Sufficiency, hard fidelity and overlap are secondary outcomes and must be inspected for tradeoffs.

The larger pilot, if triggered, uses disjoint preselected targets and additional search seeds. Screening and expansion must be reported separately. No results are automatically incorporated into the main study.

Mean saved case runtime: 33.1 seconds.