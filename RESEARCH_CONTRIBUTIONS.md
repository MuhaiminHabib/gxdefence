# Research objective, questions, and defensible contributions

**Evidence reviewed: 1 November 2026 (Australia/Perth).** This is a claim register for the current study, not a declaration that every finding is novel. Completed evidence, exploratory findings, and unfinished hypotheses are distinguished below. Numeric values are tied to the linked experiment; cohorts, explainers, and trials must not be pooled indiscriminately.

## Research objective

Determine when prediction-preserving structural perturbations meaningfully change explanations of graph neural network anti-money-laundering classifiers, and how the conclusion depends on attacker capabilities, explainer randomness, transaction representation, search effort, and the definition of explanation fidelity.

The intended contribution is a controlled empirical evaluation on directed financial transaction multigraphs, supported by threat-model comparisons and diagnostic controls. GXAttack and explanation attacks already exist. The GNNExplainer-targeted adaptation and discrete SubgraphX search are distinct implementations; neither should be presented as an exact reproduction of the original PGExplainer attack or as an established new state-of-the-art method.

**Working research title:** *When Do Structural Attacks Meaningfully Disrupt GNN Explanations in Financial Transaction Multigraphs?*

## Research questions

| ID | Research question | Evidence and present status |
|---|---|---|
| RQ1 | How much can small structural edits change financial-graph explanations while preserving the classifier's prediction? | Completed PG-targeted complete-graph study, GNN-targeted three-trial study, and AMLSim SubgraphX study. HI-Small SubgraphX remains incomplete. |
| RQ2 | How does restricting the attacker from mixed addition/deletion to deletion-only access change explanation disruption? | Completed paired SubgraphX experiment: 30 targets per dataset. |
| RQ3 | Does disruption selected under one explainer seed persist under unseen explanation randomness? | Completed original audit: 50 targets per dataset, five fresh seeds. Additional fresh-randomness validation remains incomplete. |
| RQ4 | Does lower explanation overlap correspond to lower fidelity, including fidelity relative to size-matched random explanations? | Completed full-cohort hard/soft fidelity analysis and fresh-seed random-mask controls. |
| RQ5 | How much do random search and proposal budget explain the observed attack effectiveness? | Completed three-trial baselines and retrospective AMLSim SubgraphX trajectory analysis. |
| RQ6 | Does matching model-indistinguishable parallel transaction rows change the interpretation of attack and clean-repeat overlap? | Completed exploratory multigraph-resolution audit and mechanical equivalence checks; additional native explainer/permutation validation is incomplete. |
| RQ7 | Do conclusions survive recomputation of transaction-derived account features after record changes? | Transaction-consistency experiment implemented and partially evaluated; no completed-cohort conclusion yet. |
| RQ8 | Can explanation disruption survive exact degree and short-cycle-count constraints while retaining the prediction? | New GNNExplainer constrained-rewiring pilot implemented and partially evaluated; no completed-cohort conclusion yet. |

## Strongest completed empirical contributions

### C1. Explanation vulnerability depends materially on attacker access

**Claim we can use:** Under the fixed-feature graph-store threat model, restricting SubgraphX attacks to deletion-only access reduces disruption relative to mixed addition/deletion on the paired evaluated cohorts.

Six edits and 40 proposals were used in each search/access condition, on the same 30 targets per dataset. For adaptive search:

| Dataset | Mixed-access similarity | Deletion-only similarity | Paired increase, 95% target interval |
|---|---:|---:|---|
| AMLSim | 0.0000 | 0.2468 | 0.2468 [0.1128, 0.3916] |
| HI-Small | 0.2064 | 0.3783 | 0.1719 [0.0664, 0.2820] |

Higher similarity means less explanation disruption. All selected predictions were preserved in this experiment. This does not imply probabilities were unchanged: preservation of the discrete label was the selection condition, not a universal 0.02 probability cap. Empty explanations and direct removal of explanatory edges require the accompanying sensitivity checks.

**Contribution type:** empirical threat-model comparison. **Boundary:** one attack trial, fixed trained models and features; record suppression is not demonstrated to be economically feasible. Deletion-only attacks and constrained graph attacks are not new concepts.

Evidence: [paired access report](deletion_access/results/full/REPORT.md), [paired effects](deletion_access/results/full/paired_effects.csv), [protocol](deletion_access/README.md).

### C2. Overlap disruption does not imply uniform fidelity degradation

**Claim we can use:** In the evaluated financial graphs, hard and soft fidelity can move in opposite directions after an explanation attack; lower edge overlap alone is insufficient evidence that explanations become uniformly less faithful.

In the five-trial PG-targeted complete-graph study, HI-Small hard necessity decreases while mean soft necessity increases for PGExplainer, GNNExplainer, and SubgraphX. For GNNExplainer, soft necessity changes from 2.6839 to 3.2753 probability percentage points. This belongs to the PG-targeted experiment and must not be confused with the separate GNN-targeted study.

The fresh-seed GNN-targeted audit adds a size-matched random-explanation reference: HI-Small explanation-minus-random soft necessity increases from 0.6799 to 3.1886 percentage points. The paired change is **+2.5088 pp**, with a target-bootstrap interval **[1.1037, 4.2418] pp**. Thus the increase is not explained solely by the average response of the sampled random edge sets.

**Contribution type:** domain-specific evaluation finding and controlled interpretation. **Boundary:** this is not proof of improved explanation accuracy. Random masks control cardinality, not connectivity or degree. Removing graph edges can introduce distribution shift; the study has no ground-truth transaction-level explanation labels or investigator study. The general distinction between overlap and accuracy is prior knowledge.

Evidence: [full-cohort fidelity](complete_graphs/results/soft_fidelity_full/REPORT.md), [random-mask audit](followup_audit/results/gnn_audit/REPORT.md), [audit intervals](followup_audit/results/gnn_audit/summary.csv).

### C3. Fresh explanation randomness produces dataset-dependent attenuation

**Claim we can use:** In the fixed saved-attack audit, moving from the selection seed to unseen GNNExplainer seeds leaves mean AMLSim overlap approximately unchanged, while reducing measured disruption on HI-Small.

| GNN-targeted attack | Selection-seed similarity | Fresh-seed similarity | Fresh minus selection, 95% target interval |
|---|---:|---:|---|
| AMLSim | 0.2451 | 0.2471 | 0.0020 [-0.0054, 0.0100] |
| HI-Small | 0.2591 | 0.3064 | 0.0473 [0.0242, 0.0741] |

The audit used 50 targets per dataset and five unseen paired clean/attacked seeds. A similar HI-Small attenuation occurs for random search. Independent clean-repeat controls quantify ordinary variability, but are not a perfectly matched null for same-seed clean/attacked comparisons.

**Contribution type:** operational assumption audit. **Boundary:** the attack retains knowledge of the model and selection-time explainer; the final explainer randomness is unseen. This is not a fully black-box attack, and the evidence does not establish robustness across retrained models or unseen datasets.

Evidence: [fresh-seed report](followup_audit/results/gnn_audit/REPORT.md), [paired seed changes](followup_audit/results/gnn_audit/seed_generalization.csv).

## Additional completed findings: baselines and parameters

### C4. Strong random-search baselines limit claims of attack-method superiority

**Claim we can use:** Best-of-40 random search is competitive with the targeted methods in these financial-graph evaluations and is necessary when interpreting their effectiveness.

In the completed GNN-targeted three-trial study, mean top-quarter similarity is 0.2374 for the adaptation versus 0.2415 for random search on AMLSim, and 0.2482 versus 0.2292 on HI-Small. For native AMLSim SubgraphX sets, adaptive search gives 0.0039 versus 0.0013 for random search. These means support competitiveness, not a universal statistical ordering of algorithms.

**Boundary:** matching candidate-evaluation counts does not equalize gradient work, wall time, or total computational cost. The result does not support claiming that the new adaptation is consistently superior to random search.

Evidence: [GNN three-trial tables](gnn_three_trials/results/full/TABLES_PAPER_LAYOUT.md), [AMLSim SubgraphX results](subgraphx_primary/results/full/REPORT.md).

### C5. AMLSim SubgraphX disruption saturates rapidly with proposal budget

**Claim we can use:** Retrospective prefixes of the completed AMLSim adaptive-search trajectories show most observed gains by ten proposals, with smaller further gains toward forty.

| Available proposals | Mean native-set similarity | Label-preserved zero-similarity cases |
|---:|---:|---:|
| 1 | 0.3340 | 58.63% |
| 5 | 0.1015 | 85.34% |
| 10 | 0.0423 | 93.98% |
| 20 | 0.0108 | 97.99% |
| 40 | 0.0039 | 99.40% |

The analysis covers 166 targets and three source trials, or 498 saved trajectories. All selected prefix candidates preserved labels in this cohort.

**Contribution type:** parameter-efficiency finding. **Boundary:** this is retrospective trajectory analysis under selection-time randomness. Proposal counts differ from unique explainer calls because of caching. Zero overlap can involve an empty explanation; it is not an accuracy score. Missing random-search intermediate scores prevent a corresponding efficiency-superiority claim.

Evidence: [budget report and intervals](followup_audit/results/search_budget/REPORT.md), [budget summary](followup_audit/results/search_budget/summary.csv).

## Promising completed exploratory contribution

### C6. Transaction identity and model resolution change attack evaluation

**Narrow claim supported by the completed audit:** For this fixed-feature GraphSAGE, treating parallel transaction rows as distinguishable explanation units can obscure the difference between ordinary explainer variability and attack-associated change.

The classifier consumes node features and directed endpoints, without individual edge amount/time attributes. Swapping selected row identities within an ordered sender-receiver pair, while preserving selected multiplicity, leaves the retained/removed endpoint multisets unchanged. This is a model-conditional equivalence, not economic equivalence between transactions.

The audit verified 500 constructed explanation-pair comparisons on 100 targets and five fresh seeds. Removal and retention logits agreed within numerical tolerance; maximum observed differences were 1.43e-6 on AMLSim and 2.38e-7 on HI-Small. These were constructed equivalent masks, not independently generated explainer outputs.

For fresh-seed GNN-targeted attacks, matching original rows available in both input pools gives:

| Dataset | Raw attack overlap | Within-pair matched overlap | Clean-repeat minus attack: raw | Clean-repeat minus attack: matched |
|---|---:|---:|---:|---:|
| AMLSim | 0.2471 | 0.7004 | 0.0469 | 0.1250 |
| HI-Small | 0.3064 | 0.4673 | 0.0510 | 0.2307 |

The completed AMLSim native SubgraphX control has zero matching discrepancy, consistent with selection of whole induced edge groups. The retrospective larger GNN cohort has 166 AMLSim and 795 HI-Small targets over three trials; it overlaps the initial audit and is not an independent replication.

**Contribution status:** completed exploratory evidence; a plausible empirical contribution, pending the additional fresh-randomness/edge-order validation. **Boundary:** matching increases overlap by construction and is an upper-bound diagnostic, not a corrected attack-success rate or semantic-accuracy metric. The general symmetry problem is established literature. Recomputing transaction-derived features can break the stated equivalence.

Evidence: [resolution audit](exploratory_multigraph_resolution/results/REPORT.md), [paired clean-repeat analysis](exploratory_multigraph_resolution/results/PAIRED_BASELINE.md), [additional validation protocol](exploratory_resolution_validation/README.md).

## Supporting contributions and extras

- **Controlled financial-multigraph evaluation:** completed GNN-targeted results cover 961 eligible targets across two datasets and three trials; native AMLSim SubgraphX covers 166 targets and three trials. This is an application/evaluation contribution, not evidence that all test accounts or all financial networks are vulnerable.
- **Physical-edge implementation validation:** native/local explanation parity, full/local prediction checks, frozen-weight checks, and physical removal/retention tests support the correctness of the implementation. These are methodological safeguards rather than a new attack.
- **Why hard necessity is low:** removing all edges while retaining features preserves 165/166 AMLSim and 739/795 HI-Small target labels. This is a frozen-model ablation, not a separately trained feature-only model or proof that the classifier ignores structure.
- **Explanation-size sensitivity:** in the complete-graph PG analysis, increasing k from 5 to 20 raises HI-Small clean hard necessity from 4.4277% to 7.6981%. This is useful parameter sensitivity, not evidence that one post-hoc choice of k is universally correct.
- **Negative exploratory result:** the fidelity-objective selector pilot completed 40 cases but did not meet its promotion criterion. On HI-Small its extra soft-necessity reduction versus the first feasible candidate is +0.5347 pp with interval [-1.1250, 2.3732]; versus the cosine selector it is -0.0472 pp with interval [-1.3578, 1.4673]. Retain it as a negative result, not a successful new attack. See [pilot report](exploratory_fidelity_objective/results/screening/REPORT.md).
- **Historical studies:** the sampled-graph study, earlier HI-Small preview, and stopped AMLSim run provide development history. The later complete cohorts supersede them; they are not independent replications.

## Candidate contributions that cannot yet be claimed

| Candidate | Experiment | Claim requires |
|---|---|---|
| Feature-consistent threat-model assessment | [Transaction-consistency study](exploratory_transaction_consistency/README.md): frozen versus refreshed transaction-derived features, replay and matched searches | Completed paired cohort, valid prediction checks, uncertainty intervals, and scrutiny of feasibility/empty explanations. |
| Explanation vulnerability under graph-pattern constraints | [Pattern-constraint pilot](exploratory_pattern_constraints/README.md): source-fixed, degree-preserving, and degree-plus-cycle-preserving rewiring | Completed fixed pilot; feasible coverage and fresh-seed outcomes; independent verification of global cycle counts; expansion only if its prespecified gate passes. |
| Replication of the resolution finding under new explainer draws | [Additional resolution validation](exploratory_resolution_validation/README.md): 50 additional targets per dataset, new seeds and native edge-order reruns | Completed cohort and primary endpoint. Targets were included in earlier retrospective aggregates, so this is not wholly unseen-data confirmation. |
| Full-cohort HI-Small SubgraphX finding | [SubgraphX HI-Small protocol](subgraphx_hi_small/README.md) | Completion of all 795 planned targets; partial snapshots must not be treated as completed-cohort estimates. |

Current completion counts and publication boundaries are in the [dated snapshot](publication_snapshots/2026-11-01/README.md). Technical-pilot success establishes implementation readiness, not success of a scientific hypothesis.

## Literature positioning

| Prior work | What it already establishes | Defensible positioning of this study |
|---|---|---|
| [Li et al., Explainable Graph Neural Networks Under Fire / GXAttack (2024)](https://arxiv.org/abs/2406.06417v2) | Optimization-based explanation attacks preserving predictions | Financial-multigraph adaptation and controlled empirical assessment; no claim to invent prediction-preserving explanation attacks. |
| [Li et al., Graph Neural Network Explanations are Fragile, ICML 2024](https://proceedings.mlr.press/v235/li24bd.html) | Explanation attacks under limited knowledge and perturbation restrictions | Our deletion-only comparison and specific financial evaluation; no first restricted-threat-model claim. |
| [Crabbe and van der Schaar, NeurIPS 2023](https://arxiv.org/abs/2304.06715) | Explanation invariance/equivariance and symmetry-based evaluation | Measured impact of parallel transaction identity on adversarial evaluation, rather than a new symmetry principle. |
| [Xu et al., Automorphism-Induced Non-Canonicity in Top-k Explanations (2026 preprint)](https://arxiv.org/abs/2607.26344) | Ambiguity in top-k graph explanations and symmetry-aware reporting | Financial parallel-record and attack-evaluation consequences; not invention of symmetry-aware reporting. |
| [Heijmans et al., Towards Adversarially Robust Multigraph Neural Networks for Financial Crime Analysis (LoG 2026)](https://arxiv.org/abs/2610.31718) | Financial multigraph prediction-evasion attacks and short-cycle regularization | Our pending prediction-preserving explanation objective under explicit constraints; not the first financial multigraph attack or cycle constraint. |

These references motivate narrow candidate gaps. They are not an exhaustive novelty proof. Any final paper should refresh the literature review and compare exact threat models, model inputs, and metrics.

## Common claim limits

1. Most completed attacks change graph structure while freezing transaction-derived features. The current main threat model is graph-store corruption, not fully consistent financial transaction manipulation.
2. Class preservation is not identical to probability preservation. Report both, including failures; a 0.02 probability cap belongs only to experiments explicitly configured for it.
3. Binary top-quarter overlap, top-10 overlap, native SubgraphX overlap, soft-mask cosine, hard fidelity, and soft fidelity are different quantities. Their numerical values are not interchangeable.
4. Target-bootstrap intervals average repeated seeds/trials within targets. They omit dependence between connected nodes and uncertainty from retraining the classifier. Trial SD is not a confidence interval.
5. Eligibility selects correctly classified illicit test targets with restricted neighborhoods. Results are conditional on this cohort and on one frozen classifier per dataset.
6. No current evidence establishes human-investigator deception, ground-truth explanation error, universal robustness, or an effective new defense.
7. Do not claim universal degradation, universal superiority over random search, a fully black-box attack, first-ever symmetry-aware evaluation, or first-ever financial multigraph attacks.

## Suggested concise contribution statement

> We evaluate prediction-preserving explanation attacks on directed financial transaction multigraphs and show that their measured effects depend on attacker access, explainer randomness, and evaluation granularity. Paired deletion-only experiments quantify the role of insertion access; fresh-seed and random-explanation controls distinguish overlap changes from uniform fidelity degradation; and saved search trajectories expose strong random-search baselines and early proposal-budget saturation. An exploratory multigraph audit further shows that transaction-ID instability can obscure attack-associated explanation changes when the classifier cannot distinguish parallel records.

Use the final sentence as an exploratory contribution until the additional resolution-validation cohort is complete. Add feature-consistency or pattern-preservation claims only after their respective experiments finish and support them.
