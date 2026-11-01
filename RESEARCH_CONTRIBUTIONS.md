# Research objective, questions, and defensible contributions

**Evidence reviewed: 1 November 2026, late-evening update (Australia/Perth).** The [latest results snapshot](publication_snapshots/2026-11-01-231311/README.md) was rebuilt from verified saved cases. The 200-case pattern-constraint expansion is now complete, alongside the additional 100-target resolution audit, 20-target pattern screening, and 40-target transaction-consistency pilot. Only HI-Small SubgraphX remains incomplete among these studies. This is a claim register, not a declaration that every finding is novel; cohorts, explainers, and trials must not be pooled indiscriminately.

## Research objective

Determine when prediction-preserving structural perturbations meaningfully change explanations of graph neural network anti-money-laundering classifiers, and how the conclusion depends on attacker capabilities, explainer randomness, transaction representation, search effort, and the definition of explanation fidelity.

The intended contribution is a controlled empirical evaluation on directed financial transaction multigraphs, supported by threat-model comparisons and diagnostic controls. GXAttack and explanation attacks already exist. The GNNExplainer-targeted adaptation and discrete SubgraphX search are distinct implementations; neither should be presented as an exact reproduction of the original PGExplainer attack or as an established new state-of-the-art method.

**Working research title:** *When Do Structural Attacks Meaningfully Disrupt GNN Explanations in Financial Transaction Multigraphs?*

## Research questions

| ID | Research question | Evidence and present status |
|---|---|---|
| RQ1 | How much can small structural edits change financial-graph explanations while preserving the classifier's prediction? | Completed PG-targeted complete-graph study, GNN-targeted three-trial study, and AMLSim SubgraphX study. HI-Small SubgraphX remains incomplete. |
| RQ2 | How does restricting the attacker from mixed addition/deletion to deletion-only access change explanation disruption? | Completed paired SubgraphX experiment: 30 targets per dataset. |
| RQ3 | Does disruption selected under one explainer seed persist under unseen explanation randomness? | Completed original audit: 50 targets per dataset, five fresh seeds. The additional 50-target-per-dataset resolution audit with new seeds is also complete. |
| RQ4 | Does lower explanation overlap correspond to lower fidelity, including fidelity relative to size-matched random explanations? | Completed full-cohort hard/soft fidelity analysis and fresh-seed random-mask controls. |
| RQ5 | How much do random search and proposal budget explain the observed attack effectiveness? | Completed three-trial baselines and retrospective AMLSim SubgraphX trajectory analysis. |
| RQ6 | Does matching model-indistinguishable parallel transaction rows change the interpretation of attack and clean-repeat overlap? | Completed retrospective audit, mechanical checks, and additional 100-target fresh-randomness/native-permutation validation. |
| RQ7 | Do conclusions survive recomputation of transaction-derived account features after record changes? | Completed 40-target pilot: no clear primary matched-search difference; substantial secondary differences between edge-only and record-consistent fidelity interventions. No expansion was triggered. |
| RQ8 | Can explanation disruption survive exact degree and short-cycle-count constraints while retaining the prediction? | Completed screening and 200-case expansion on 50 additional targets per dataset, with two search trials each. The positive disruption contrast persists on both datasets; feasible-case coverage is lower on HI-Small. |

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

## Completed representation audit

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

**Additional validation is now complete:** 50 further targets per dataset, disjoint from the original fresh-seed cohort, with five new explainer seeds. The predeclared primary endpoint is the change in clean-repeat-minus-attack contrast after within-pair matching, for GNN-targeted top-quarter explanations:

| Dataset | Raw contrast | Matched contrast | Change in contrast, 95% target interval |
|---|---:|---:|---|
| AMLSim | 0.0542 | 0.1666 | 0.1123 [0.0905, 0.1337] |
| HI-Small | 0.0860 | 0.2114 | 0.1254 [0.0898, 0.1671] |

The finding therefore persists under new explanation draws on additional targets. These targets were part of the earlier retrospective aggregate analysis; this is not wholly unseen-data or independently trained-model replication.

**Native edge-order control:** without changing graph connections, permuting clean edge columns and rerunning GNNExplainer gives mean top-quarter row overlap 0.2890 on AMLSim and 0.3623 on HI-Small; within-pair matching raises these to 0.8181 and 0.6935. All 500 target-logit comparisons under permutation passed, with maximum difference 1.43e-6. These are actual explainer reruns, unlike the earlier constructed equivalent-mask check. Column order changes the assignment of random initial mask values, so this is implementation-level ordering sensitivity, not proof that top-k tie-breaking alone causes the effect. Unchanged predictions do not imply that the resulting explanation masks have identical fidelity.

**Contribution status:** strengthened completed empirical evidence under the stated architecture, feature matrix and cohorts. **Boundary:** matching increases overlap by construction and is an upper-bound diagnostic, not a corrected attack-success rate or semantic-accuracy metric. Independent clean repeats remain a variability reference rather than a perfectly matched null. The general symmetry problem is established literature; recomputing transaction-derived features can break the stated equivalence.

Evidence: [initial resolution audit](exploratory_multigraph_resolution/results/REPORT.md), [initial paired analysis](exploratory_multigraph_resolution/results/PAIRED_BASELINE.md), [completed additional validation](publication_snapshots/2026-11-01-231311/exploratory_resolution_validation/REPORT.md), [native permutation and attack summaries](publication_snapshots/2026-11-01-231311/exploratory_resolution_validation/summary.csv), [verification summary](publication_snapshots/2026-11-01-231311/exploratory_resolution_validation/validation_summary.json).

## Completed constrained-attack study

### C7. Explanation disruption can survive degree and short-cycle-count preservation

**Claim supported by the completed expansion:** On preselected financial-graph targets, best-of-up-to-40 random search produces GNNExplainer disruption while exactly preserving each node's in/out degree and global multiplicity-weighted directed two- and three-cycle totals. The finding persists in the separate expansion cohort of 50 targets per dataset, two search trials per target, and five fresh explainer seeds per trial: **200/200 planned target-search cases are complete**.

The attack rewires three transaction receivers, equivalent to three removed and three inserted connections. Features and classifier weights remain fixed. A selected attack must preserve the class and change its original-class probability by at most 0.02. Five fresh paired explanation seeds evaluate each selected graph. The search objective is endpoint-multiplicity overlap, reducing reliance on individual transaction-ID swaps.

| Degree-and-cycle-constrained search, expansion | Feasible target-search cases | Mean joint disruption | Excess disruption over clean-repeat reference, 95% target interval |
|---|---:|---:|---|
| AMLSim | 100/100 | 0.3662 | 0.1812 [0.1538, 0.2096] |
| HI-Small | 75/100 | 0.3784 | 0.1555 [0.0893, 0.2238] |

Joint disruption is feasibility multiplied by (1 - endpoint overlap); excess disruption is feasibility multiplied by (clean-repeat overlap - attacked overlap). Infeasible cases receive zero and remain in the denominator. Seeds are averaged within search trials, then both trials are averaged within each target before target-level bootstrap resampling. The independent clean-repeat reference is not a perfectly matched null. Feasible-case percentages refer to 100 target-search cases per dataset, not 100 unique targets.

The paired excess-disruption advantage over the first structurally admissible random candidate is **0.2506 [0.2166, 0.2875]** on AMLSim and **0.1538 [0.1013, 0.2078]** on HI-Small. This compares search with a single random candidate; it does not establish superiority over another best-of-40 algorithm.

The initial screening used ten targets per dataset and yielded excess disruption 0.1907 on AMLSim and 0.1228 on HI-Small. Both passed the prespecified expansion gate. Expansion targets were frozen before execution and are disjoint from screening targets; screening and expansion are reported separately. This strengthens evidence on the same datasets and fixed classifiers, not on independent datasets or newly trained models.

**Feasibility and budget limits:** on HI-Small, 18/100 searches produced no structurally admissible candidate within the 20,000-draw cap; another seven had candidates but no feasible attack under the label/probability constraint. Failure to find a candidate does not prove that none exists. The constrained search produced fewer than 40 candidates in 24/100 HI-Small cases and 2/100 AMLSim cases. Report these shortfalls alongside the positive mean effect rather than interpreting the result as universal attack success.

**Boundary:** this is a completed experimental extension, not a new learned attack method. Exact total cycle counts do not preserve every individual motif or establish financial plausibility. Constraint conditions use different proposal distributions and realized budgets, so a better mean under a stricter constraint is not evidence that adding constraints inherently improves an attack. No feature consistency, fidelity degradation, human deception, fully black-box capability, or generalization across trained models is established.

Evidence: [completed expansion report](publication_snapshots/2026-11-01-231311/exploratory_pattern_constraints/expanded/REPORT.md), [expanded paired comparisons](publication_snapshots/2026-11-01-231311/exploratory_pattern_constraints/expanded/paired_effects.csv), [actual search coverage](publication_snapshots/2026-11-01-231311/exploratory_pattern_constraints/expanded/search_coverage.csv), [validated feasibility and coverage](publication_snapshots/2026-11-01-231311/exploratory_pattern_constraints/expanded/validation_summary.json), [separate screening report](publication_snapshots/2026-11-01-231311/exploratory_pattern_constraints/screening/REPORT.md), [protocol](exploratory_pattern_constraints/README.md).

## Completed secondary finding from the transaction-consistency pilot

### C8. Fidelity changes when transaction-derived features are recomputed

**Claim supported by the completed pilot:** For the evaluated clean SubgraphX explanations, deleting or retaining transaction records and recomputing account features gives materially different fidelity values from changing graph edges while holding those features fixed.

The pilot uses 20 targets per dataset and five fresh explanation seeds. The table gives paired **record-intervention minus edge-only-intervention** changes on the clean graphs. Values and descriptive target-bootstrap intervals are in probability percentage points.

| Dataset | Soft necessity change | Random-adjusted soft necessity change | Soft retention-gap change |
|---|---|---|---|
| AMLSim | +11.35 [2.64, 21.99] | +10.95 [2.41, 21.19] | +92.51 [87.66, 96.78] |
| HI-Small | +11.76 [6.54, 17.48] | +6.40 [1.58, 11.65] | +19.69 [9.51, 30.47] |

The necessity increase remains after subtracting size-matched random-mask necessity. However, the random-adjusted retention-gap difference is negative: -6.90 pp [-11.99, -2.75] on AMLSim and -26.44 pp [-37.44, -15.20] on HI-Small. Thus the large raw retention effect is not an explanation-specific deterioration. Record retention removes all other transaction records globally and recomputes aggregates, causing a much broader input change than edge-only masking.

**Boundary:** these are preplanned secondary intervention comparisons, not ground-truth explanation accuracy or proof that one fidelity definition is universally correct. The intervals are descriptive and unadjusted for multiple comparisons. They concern the composed preprocessing/classifier intervention and remain conditional on the fixed trained models; substantial input-distribution change is possible. This result does not override the pilot's failed primary expansion gate.

**Primary attack-comparison result:** reselecting attacks separately under frozen and refreshed features did not produce a clear paired change in fresh-seed joint disruption:

| Dataset | Frozen-search joint disruption | Refreshed-search joint disruption | Refreshed minus frozen, 95% target interval |
|---|---:|---:|---|
| AMLSim | 0.4230 | 0.4554 | +0.0324 [-0.0140, 0.0823] |
| HI-Small | 0.3934 | 0.3883 | -0.0052 [-0.1040, 0.0840] |

Neither dataset met the prespecified criterion for expansion. This is absence of a clear effect in this pilot, not an equivalence test. Replaying previously selected adaptive edits on HI-Small reduced observed label/2pp feasibility from 16/20 to 13/20 after feature refresh; the paired feasibility-change interval touches zero. Report this as a descriptive transfer limitation, not a robust average causal claim.

Evidence: [complete transaction-consistency report](publication_snapshots/2026-11-01-231311/exploratory_transaction_consistency/pilot/REPORT.md), [primary paired comparisons](publication_snapshots/2026-11-01-231311/exploratory_transaction_consistency/pilot/paired_effects.csv), [secondary fidelity comparisons](publication_snapshots/2026-11-01-231311/exploratory_transaction_consistency/pilot/fidelity_paired_effects.csv), [no-expansion decision](publication_snapshots/2026-11-01-231311/exploratory_transaction_consistency/promotion_decision.json).

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
| A large systematic change in optimized attack success after feature refresh | [Transaction-consistency study](exploratory_transaction_consistency/README.md) is complete at pilot scale | The current primary intervals include zero and the expansion criterion failed. A larger effect cannot be claimed from this pilot. |
| Generalization of graph-pattern-constrained vulnerability beyond the evaluated setting | [Pattern-constraint study](exploratory_pattern_constraints/README.md): screening and 200-case expansion are complete | New classifiers, other datasets, feature-consistent rewirings, or stronger attacker-access restrictions. The current C7 evidence is conditional on the fixed model and graph-store threat model. |
| Generalization of the resolution finding to new datasets or architectures | Current additional resolution cohort is complete | Independent datasets/trained models or edge-attribute-aware architectures; those experiments have not been conducted. |
| Full-cohort HI-Small SubgraphX finding | [SubgraphX HI-Small protocol](subgraphx_hi_small/README.md) | Completion of all 795 planned targets; partial snapshots must not be treated as completed-cohort estimates. |

Current completion counts and publication boundaries are in the [latest snapshot](publication_snapshots/2026-11-01-231311/README.md); earlier snapshots remain as history. HI-Small SubgraphX is still provisional and is not promoted to a completed-cohort claim.

## Literature positioning

| Prior work | What it already establishes | Defensible positioning of this study |
|---|---|---|
| [Li et al., Explainable Graph Neural Networks Under Fire / GXAttack (2024)](https://arxiv.org/abs/2406.06417v2) | Optimization-based explanation attacks preserving predictions | Financial-multigraph adaptation and controlled empirical assessment; no claim to invent prediction-preserving explanation attacks. |
| [Li et al., Graph Neural Network Explanations are Fragile, ICML 2024](https://proceedings.mlr.press/v235/li24bd.html) | Explanation attacks under limited knowledge and perturbation restrictions | Our deletion-only comparison and specific financial evaluation; no first restricted-threat-model claim. |
| [Crabbe and van der Schaar, NeurIPS 2023](https://arxiv.org/abs/2304.06715) | Explanation invariance/equivariance and symmetry-based evaluation | Measured impact of parallel transaction identity on adversarial evaluation, rather than a new symmetry principle. |
| [Xu et al., Automorphism-Induced Non-Canonicity in Top-k Explanations (2026 preprint)](https://arxiv.org/abs/2607.26344) | Ambiguity in top-k graph explanations and symmetry-aware reporting | Financial parallel-record and attack-evaluation consequences; not invention of symmetry-aware reporting. |
| [Heijmans et al., Towards Adversarially Robust Multigraph Neural Networks for Financial Crime Analysis (LoG 2026)](https://arxiv.org/abs/2610.31718) | Financial multigraph prediction-evasion attacks and short-cycle regularization | Our completed constrained-attack study addresses a prediction-preserving explanation objective; not the first financial multigraph attack or cycle constraint. |

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

> We evaluate prediction-preserving explanation attacks on directed financial transaction multigraphs and show that their measured effects depend on attacker access, explainer randomness, and evaluation granularity. Paired deletion-only experiments quantify the role of insertion access; fresh-seed and random-explanation controls distinguish overlap changes from uniform fidelity degradation; and saved search trajectories expose strong random-search baselines and early proposal-budget saturation. A multigraph audit, strengthened by additional fresh-randomness and native edge-order controls, shows that transaction-ID instability can obscure attack-associated changes when the classifier cannot distinguish parallel records. A transaction-consistency pilot further shows that refreshing derived account features changes the fidelity intervention being measured, while its primary matched-search effect remains inconclusive. A completed expansion on 100 additional targets with two search trials each supports explanation disruption under exact degree and short-cycle-count preservation, with lower feasible-case coverage on HI-Small.

Keep screening and expansion results separate and retain infeasible cases in the denominator. Distinguish the transaction-consistency pilot's negative primary result from its secondary fidelity findings. All claims remain conditional on the fixed models, target eligibility, feature/intervention settings and stated metrics.
