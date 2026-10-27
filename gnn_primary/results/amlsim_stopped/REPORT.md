# AMLSim saved results - stopped by user

277 completed evaluations retained: all 166 targets in trial 2026 and 111 targets in trial 2027. The unsaved in-progress case is excluded. Full case evidence remains in ../full/cases/.

The table below uses only the completed trial 2026, covering all 166 targets equally. It is a single-trial summary, not a five-trial estimate. Partial trial 2027 remains in the other CSVs for later use.

| Method | Explainer | Similarity | Label changes | Probability change | Clean hard+ | Attacked hard+ | Clean soft+ | Attacked soft+ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Clean repeat | GNNExplainer | 0.27743 | 0.00000 | 0.00000 | unavailable | unavailable | unavailable | unavailable |
| GNN-targeted GX adaptation | GNNExplainer | 0.23497 | 0.00000 | 0.00130 | 0.00602 | 0.00602 | 0.00149 | 0.00118 |
| GNN-targeted GX adaptation | PGExplainer | 0.71835 | 0.00000 | 0.00130 | 0.00602 | 0.00000 | 0.00006 | 0.00010 |
| GNN-targeted GX adaptation | SubgraphX | 0.30624 | 0.00000 | 0.00130 | 0.01205 | 0.00602 | 0.01056 | 0.00106 |
| Random flipping | GNNExplainer | 0.54189 | 0.00000 | 0.00016 | 0.00602 | 0.00602 | 0.00149 | 0.00131 |
| Random rewiring | GNNExplainer | 0.43229 | 0.00000 | 0.00009 | 0.00602 | 0.00602 | 0.00149 | 0.00124 |
| Random search | GNNExplainer | 0.24047 | 0.00000 | 0.00090 | 0.00602 | 0.01205 | 0.00149 | 0.00136 |

All values are fractions/probability differences, not percentages. PG/GNN fidelity uses top10; SubgraphX uses its native set. Similarity uses binary top25% for PG/GNN and native sets for SubgraphX. Clean repeat has no fidelity measurements.