# GXAttack financial graph study — protocol v2

22 October 2026. Authorized scope: revise the plan, save a pilot, then run the full experiment. No literature review or defence experiment.

## Design and sources

Adapted financial evaluation of GXAttack, not an exact reproduction of its synthetic-graph experiments. Reference: https://arxiv.org/html/2406.06417v1 . Local official source commit a5f1fd3a1e27941791c58d76728d6477b06788b9; audited copies in vendor/. The core objective is log probability of the original class minus 0.0005 times perturbation entropy plus 0.1 times explanation cosine distance, with projected gradient ascent. Architecture, directed multigraph support and candidate domain are explicit adaptations.

Frozen seed-42 GraphSAGE checkpoints for Elliptic and AMLSim; five existing independently fitted PGExplainer networks (2026–2030). HI-Small uses a newly trained GraphSAGE, validation-selected checkpoint and five training-only PG fits. This evaluates variation across attack/explainer trials conditional on one classifier per dataset.

HI-Small: user approved random 50% of transaction rows. Select exactly floor(N/2) without replacement with NumPy seed 42, retaining source row IDs. Accounts are (bank, account) pairs; directed transaction rows remain separate edges. An account is positive if incident to a labelled laundering transaction in the selected data. This is an incident-laundering account proxy, not a native account label. Numeric transaction aggregates exclude laundering labels. Stratified account split 65/15/20; scaler fitted on training accounts only. Transductive static experiment, not future-event forecasting.

## Sampling and stages

Pilot: three eligible validation targets per dataset, two trials. Full: 50 randomly selected eligible test targets per dataset, five trials. If fewer than 50 qualify, use all and prominently report the count. Seed 4242 selects targets independently of attack outcomes. Eligibility: correctly classified illicit node, incoming two-hop context with 4–100 nodes, 5–2,000 edge rows, at least three removable non-self-loop rows and three candidate nonedges. Record the full candidate census and reasons. Pilot and full targets are disjoint by split.

Each target is attacked independently from the clean graph. No accumulated perturbations. The same saved GXAttack graph is evaluated with PGExplainer, GNNExplainer and SubgraphX. Same-seed clean/attacked comparisons and independent clean-repeat controls are recorded. PG networks are frozen during attacks. GNNExplainer uses 100 epochs. DGL SubgraphX uses fixed-context feature coalitions with two hops, six children, five rollouts, five Shapley samples, minimum three nodes; save native selected nodes and induced edges. SubgraphX is not a ranked-edge explainer.

Pilot technical gates: finite outputs and gradients; frozen weights unchanged; clean and binary weighted GraphSAGE predictions match physical edge edits; PG scores match the native implementation; realized budgets respected; target mappings and selected identifiers valid; all three explainers produce saved results. Attack effectiveness is an outcome, never a pass condition. Failures are saved and halt promotion until fixed. Freeze configuration before full-run test evaluation.

## Threat model and budget

White-box, topology-only, directed graph editing within the clean incoming two-hop node set. Existing parallel rows are independent deletion candidates. Additions are one synthetic edge per absent ordered pair; no new self-loops or parallel additions. Existing self-loops stay fixed. Features, including aggregate features, remain frozen: this represents graph-store corruption, not a claim of economically valid transaction fabrication. No temporal or balance feasibility claim.

Six directed edge changes per method. GXAttack uses 100 projected-ascent steps, learning rate 0.01, two starts (zero and small seeded random); exact-budget weighted sampling produces 20 discretizations per start, selecting the best preservation/disruption result. This fixed-budget discretization differs from the repository's symmetric Bernoulli draw. Random flipping uniformly selects six candidates; random rewiring deletes three transaction rows and adds three nonedges, without degree preservation or optimization. All share the candidate domain and maximum edit count. Record additions and deletions separately. No retries that silently discard prediction-changing outcomes.

## Metrics

The audited repository run.py computes DeltaLabel across attacked targets and DeltaProb for each target's original predicted class. Preserve these definitions: DeltaLabel = mean target label change; Target-LP = 1 - DeltaLabel; DeltaProb = mean absolute target probability change. The earlier v1 all-node definition was incorrect for reproducing this code. Report fractions in CSV, clearly labelled percentages in prose.

Cosine compares masks aligned by persistent edge-row IDs on their union; absent edges get zero. Both empty masks: 1; one empty: 0, with empty counts reported. Repository dense adjacency cosine sums parallel rows; include this endpoint-aggregated cosine separately, retaining row-level cosine for transaction interpretation. Added edges have stable synthetic endpoint IDs. Never compare raw scores across different explainers as calibrated quantities.

Jaccard at k=5,10,20 uses top min(k,available edges) with actual sizes reported. Binary cosine is the common selected-set representation. SubgraphX uses its native induced set and reports cardinality rather than pretending to have a ranking. RBO/Recall/NDCG are deferred: no independent explanatory relevance annotation is established. No GEA claim.

Necessity/Fidelity+ = indicator that physically deleting the selected edges changes the graph's own original target prediction. Sufficiency-failure/Fidelity- = indicator that retaining only selected edges changes that prediction. Features and root transformations remain fixed. Save probability changes too. Compute these on clean and attacked graphs separately and report prediction-preserving comparisons. The equal-weight harmonic summary is computed from aggregate necessity and 1 minus aggregate sufficiency-failure; undefined denominator yields zero. Call it an equal-weight fidelity summary, avoiding an unverified exact GraphFramEx replication claim.

Aggregate targets within each trial, then mean and sample SD across trials. Save per-target evidence, unconditional and prediction-preserved subsets, failures, target counts and runtime. A clean-repeat control measures ordinary stochastic explanation change. Similarity changes alone do not establish poorer correctness or human deception.

## Outputs

Pilot implementation clarification: if an attacked context has at most three nodes, it is already at SubgraphX's terminal coalition size; retain the whole context and record its size, rather than invoking DGL's search which rejects this boundary case.

results/pilot and results/full: per-target JSON evidence, CSV metrics, trial means, aggregate summaries, technical validation and status. prepared/: graph caches, HI-Small row IDs and classifier/PG checkpoints. REPORT.md summarizes actual measured results and limitations after execution.
