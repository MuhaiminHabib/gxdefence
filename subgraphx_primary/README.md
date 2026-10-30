# SubgraphX-primary AMLSim experiment

AMLSim only: all 166 previously eligible illicit test nodes, three trials (2026–2028), 498 full evaluations. Validation pilot: three separate validation nodes over two trials, saved before full execution. No Elliptic or HI-Small. Previous experiments remain untouched.

SubgraphX is a discrete MCTS/Shapley explainer, so this is a **direct derivative-free SubgraphX-targeted search**, not original GXAttack or a gradient-based reproduction. It optimizes disruption of the native explanation edge set, preferring candidates that preserve the original class. Do not label these results GXAttack in a paper or table.

Each candidate changes exactly six directed edge rows. Search uses 40 proposals: an initial random candidate, one-edit substitutions of the best incumbent, and independent restarts every tenth proposal. The objective ranks label preservation first, then native binary cosine distance. Random flipping uses one independent draw, random rewiring uses three removals plus three additions, and random search selects the best of 40 independent proposals by the same rule. Duplicate candidates reuse a deterministic same-seed explanation; actual unique evaluation counts and all adaptive proposals are recorded.

The original frozen full-graph classifier, features, target eligibility and SubgraphX settings remain unchanged: incoming two hops, six children, five rollouts, five Shapley steps and terminal size three. Native SubgraphX selected sets are evaluated without top-k truncation. GNNExplainer and PGExplainer provide transfer comparisons on the chosen attacked graph, with top-10 fidelity in the summary. All hard/soft fidelity is saved. Each case checks full versus cached prediction parity, same-seed SubgraphX repeatability and frozen model parameters.

Run with the recorded main Python environment:

```
python subgraphx_primary/run.py pipeline
```

The separate DGL environment and original datasets/checkpoints are required (see ../REPRODUCIBILITY.md). Only one controller should run for this folder. The full phase starts only after the six-case pilot passes. Cases are atomically saved and resume requires exact source and parameter hashes. Results are in results/pilot and results/full. Reports update per case; final tables require complete coverage. Runtime is measured during the pilot rather than borrowed from the gradient attack.

Lower overlap does not prove worse explanation quality or investigator deception. This is not a defence experiment. Native SubgraphX set scores should not be directly ranked against top-25% PG/GNN selections without acknowledging the different definitions.
