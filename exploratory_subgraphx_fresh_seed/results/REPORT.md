# HI-Small SubgraphX fresh-seed audit

**COMPLETE: 100/100 preselected targets, five fresh paired seeds each.**

Saved seed-2026 attacks are fixed. Seeds are averaged within each target before paired target bootstrap resampling. Native explanation sets are not truncated. Clean repeats are an independent variability reference, not a matched null.

| Method | Selection similarity | Fresh similarity | Clean-repeat similarity | Fresh minus selection, 95% target interval |
|---|---:|---:|---:|---|
| SubgraphX-targeted search | 0.1491 | 0.3680 | 0.7042 | 0.2189 [0.1793, 0.2597] |
| Random search | 0.1119 | 0.3256 | 0.7042 | 0.2137 [0.1729, 0.2553] |

Fresh random-minus-adaptive similarity: -0.0424 [-0.0902, 0.0043]. Negative means lower overlap for random search.

Primary endpoint: adaptive fresh-minus-selection similarity. Other comparisons and fidelity intervals are secondary, descriptive, and not multiplicity-adjusted. Positive attenuation does not by itself establish attack failure. All sampled targets are retained; preservation is reported separately, without a retrospective probability cap.

CSV summaries include Jaccard, empty sets, native hard/soft removal/retention fidelity, and paired differences. Intervals omit graph-node dependence, common seed effects and retraining variation. This audit does not establish generalization beyond the fixed classifier and source attack run, ground-truth explanation error or human deception.

Mean completed-target runtime: 12.1 seconds.
