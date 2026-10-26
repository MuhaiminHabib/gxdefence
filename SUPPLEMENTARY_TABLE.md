# Supplementary results — completed initial study

Known-label Elliptic graph; full AMLSim; random 50% of HI-Small transaction rows. These are the completed initial results, not the ongoing complete-graph expansion.

## Table IV — Additional explanation metrics

PGExplainer; mean ± sample SD across available trial means. Completed initial study uses five trials. Fidelity uses top-10 edges, capped by available edges. Clean overlap with itself is 1 by definition; independent clean-repeat controls appear below.

### Elliptic

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.2801 ± 0.0220 | 0.4283 ± 0.1297 | 0.3750 ± 0.0303 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.3592 ± 0.0476 | 0.4874 ± 0.0569 | 0.4078 ± 0.0101 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.4046 ± 0.0584 | 0.5342 ± 0.0248 | 0.4227 ± 0.0127 |
| Fidelity+ / necessity ↑ | 0.0293 ± 0.0109 | 0.0293 ± 0.0109 | 0.0439 ± 0.0109 | 0.0780 ± 0.0204 |
| Fidelity− / sufficiency failure ↓ | 0.0049 ± 0.0109 | 0.0098 ± 0.0134 | 0.0195 ± 0.0318 | 0.0049 ± 0.0109 |
| Harmonic fidelity summary ↑ | 0.0567 ± 0.0203 | 0.0567 ± 0.0203 | 0.0839 ± 0.0203 | 0.1442 ± 0.0354 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.8305 ± 0.0285**.

### AMLSim

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.5903 ± 0.1446 | 0.8687 ± 0.0475 | 0.9161 ± 0.0637 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.6577 ± 0.1573 | 0.8982 ± 0.0168 | 0.9313 ± 0.0489 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.7021 ± 0.1804 | 0.9228 ± 0.0156 | 0.9407 ± 0.0458 |
| Fidelity+ / necessity ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Fidelity− / sufficiency failure ↓ | 0.0280 ± 0.0179 | 0.0240 ± 0.0089 | 0.0280 ± 0.0179 | 0.0240 ± 0.0089 |
| Harmonic fidelity summary ↑ | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.1559 ± 0.1890**.

### HI-Small 50%

| Metric | Clean | GXAttack | Random flipping | Random rewiring |
|---|---:|---:|---:|---:|
| Top-5 Jaccard ↓ | 1.0000 (reference) | 0.4149 ± 0.0574 | 0.4736 ± 0.0615 | 0.4919 ± 0.0399 |
| Top-10 Jaccard ↓ | 1.0000 (reference) | 0.4764 ± 0.0387 | 0.5427 ± 0.0378 | 0.5709 ± 0.0125 |
| Top-20 Jaccard ↓ | 1.0000 (reference) | 0.5542 ± 0.0151 | 0.6309 ± 0.0108 | 0.6527 ± 0.0074 |
| Fidelity+ / necessity ↑ | 0.0800 ± 0.0141 | 0.0280 ± 0.0268 | 0.0920 ± 0.0110 | 0.0920 ± 0.0228 |
| Fidelity− / sufficiency failure ↓ | 0.0440 ± 0.0219 | 0.0320 ± 0.0268 | 0.0440 ± 0.0167 | 0.0440 ± 0.0261 |
| Harmonic fidelity summary ↑ | 0.1474 ± 0.0242 | 0.0534 ± 0.0509 | 0.1677 ± 0.0184 | 0.1673 ± 0.0384 |
| RBO (not computed) | — | — | — | — |
| Recall / NDCG (no independent relevance labels) | — | — | — | — |

Independent clean-repeat Jaccard@10: **0.3200 ± 0.1113**.

Fidelity+ is the fraction of targets whose predicted class changes when selected edges are removed. Fidelity− is the fraction whose class changes when only selected edges are retained. The harmonic summary is 2 × Fidelity+ × (1 − Fidelity−) / (Fidelity+ + 1 − Fidelity−), computed within each trial before averaging; it is an adapted characterization summary, not ground-truth explanation accuracy.

Arrows indicate metric direction: lower Jaccard means greater explanation disruption; higher necessity and lower sufficiency failure indicate stronger explanatory fidelity. Compare attack overlap with clean-repeat overlap before attributing changes to the attack. Missing metrics are not zero.
