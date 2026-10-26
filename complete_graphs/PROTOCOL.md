# Complete-graph experiment — protocol v3

User authorization: complete Elliptic, AMLSim and HI-Small graphs and ALL eligible correctly detected illicit test targets. Separate from the completed v2 sampled study. Five attack/explainer trials per target. No literature review or defence work.

## Graphs and models

- Elliptic: every feature-file transaction, including unknown-labelled nodes, and every edge in the supplied CSV. Explicit transaction-ID mapping aligns features, classes and endpoints. Unknown nodes participate in message passing but never supervised loss, validation or test labels. Stratified 65/15/20 split of known labels with seed42; 165 supplied non-time features standardized using training-labelled nodes only. New two-layer GraphSAGE, hidden110, frozen after validation selection.
- AMLSim: existing complete graph of 10,000 accounts and 1,323,234 transaction rows. Reuse the full-graph seed42 classifier and five training-only PG fits, since these inputs have not changed.
- HI-Small: ALL 5,078,345 transaction rows, including parallel edges and existing self-loops; bank/account composite nodes. Positive labels indicate incident laundering transactions in the complete file. Same eight aggregate features as the earlier study; no laundering label features. New stratified65/15/20 split seed42, training-only standardization, new GraphSAGE hidden64. This remains an account-label proxy and may remain a weak detector; performance is reported without silently excluding it.

New models: seed42, Adam lr0.005, weight decay0.0005, inverse-frequency weighted cross entropy, at most300 epochs, validation AP selection and patience30. Test metrics evaluated once after selecting the checkpoint. Five PG fits seeds2026–2030, 20 epochs/lr1e-6, first30 correctly detected illicit training nodes with confidence0.55–0.95 and nonempty incoming contexts. Fail explicitly if no such nodes exist.

## Coverage and pilot gate

Pilot: three eligible validation targets per dataset and two trials, all raw outputs saved. Full: every eligible correctly detected illicit TEST target, five trials. No target sample cap. Eligibility remains incoming two-hop4–100 nodes,5–2,000 edge rows,at least3 removable non-self-loop rows and3 absent ordered pairs. Complete graphs are never truncated for classifier predictions. These eligibility bounds mean the study covers all eligible targets, not every node irrespective of graph size or label. Save candidate census, included/excluded counts and IDs.

All pilot checks from v2 remain mandatory: graph relaxation equals physical edits, gradients finite, native PG agreement, frozen classifier and PG weights, valid identifiers and six realized directed edits. Attack effectiveness is an outcome, not a promotion criterion. New full runs start only after all three dataset pilots pass.

## Attack and transfer

Same directed-multigraph adaptation as v2: fixed6 edits, additions at absent ordered pairs, independent deletion candidates for parallel rows, no self-loop edits, fixed clean incoming two-hop candidate nodes and frozen node features. Graph-store corruption threat model; financial and temporal plausibility is not claimed. Full boundary messages are retained by exact sparse delta updates.

GXAttack repository-based soft objective,100 projected-ascent steps/lr0.01,beta0.1,entropy0.0005,two starts,20 exact-budget discretizations per start. Prefer prediction-preserving candidates, then explanation distance. The original paper v2 uses different sampling, budget and learning-rate settings; this remains an adaptation. Random flipping and random rewiring are one-draw controls with matched6-edit budget, not matched search effort. No claim of an exact paper reproduction.

Save each attacked graph as its edge edit list. Transfer that same graph to GNNExplainer100epochs and DGL SubgraphX(two hops,six children,five rollouts,five Shapley samples,terminal coalition3nodes). Contexts of at most3nodes use the whole terminal coalition; empty GNN contexts return an empty explanation. Keep all prediction-changing random controls and all algorithm failures.

## Paper-aligned tables and metrics

Source layout: supplied 2406.06417v2 (1).pdf, Table II page8, Table III page9. Dataset columns; attack/metric row blocks; explainer rows for transfer. GEA remains unavailable, never replaced by illicit labels or labelled as measured.

The supplied v2 paper explicitly computes reported similarity with binary top25% edge masks. Add a separately named binary_top25_cosine for PGExplainer/GNNExplainer: independently choose ceil(0.25*available explanation edge rows) on each graph, stable edge-ID tie-break, align the union, zero absent edges. Keep continuous cosine and fixed top5/10/20 metrics as supplementary. For multigraphs this row-preserving convention is still an adaptation of simple adjacency. SubgraphX uses its entire native binary induced edge set, not an invented ranking. Cosine both-empty=1,one-empty=0; record emptiness and selected cardinalities.

DeltaLabel: mean attacked-target class change. DeltaProb: mean absolute change of original target class probability. Target-LP=1-DeltaLabel. No GEA or human-deception claim. Physical-edge necessity, sufficiency-failure and probability gaps follow v2; equal-weight harmonic summary is not presented as exact GraphFramEx replication. PG clean controls use independent trained fits; GNN/SubgraphX controls vary seed.

Average all target outcomes within each trial, then mean/sampleSD across5trials. Save unconditional and prediction-preserving summaries. Only clean/attacked measured fidelity contributes to harmonic summaries; no clean-repeat placeholder scores.

## Persistence

prepared/: full graphs,mappings,training histories,metrics and frozen weights. results/pilot and results/full: independent cases,logs,census,CSV tables and status. Resume only identical source/parameter runs; stop on technical errors. Each completed case is saved atomically. Running all eligible targets may require many hours; elapsed time never authorizes reducing coverage.

