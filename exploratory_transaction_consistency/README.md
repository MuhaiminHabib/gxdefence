# Transaction-consistency pilot (separate exploratory study)

Question: do prediction-preserving explanation attacks survive when suppressed transaction records update both topology and every transaction-derived account feature? Frozen features represent graph-store corruption; refreshed features represent suppression upstream of feature extraction. Neither condition establishes economically executable laundering, temporal feasibility, explanation accuracy, or a defense. Labels describe the underlying accounts and remain fixed. Account metadata, classifier parameters, and the original clean-fitted preprocessing remain fixed. No model training or original study file is changed.

## Registered design

The primary explainer is the existing native DGL SubgraphX (2 hops, 6 children, 5 rollouts, 5 Shapley samples, terminal size 3). Preserve native induced edge sets, including empty explanations; do not truncate these sets. Use the original directed transaction row IDs, parallel rows, and incoming two-hop domain. Exactly six distinct non-self-loop rows are deleted. No additions, invented amounts, timestamps, or label-derived features are introduced.

Select 20 of the 30 previously registered deletion-access targets per dataset (AMLSim and HI-Small) using seed 173205, independent of attack outcomes. Save the selection and all input/source hashes before evaluating new outcomes. These targets have been studied previously and are not untouched confirmation data. Use the original validation target per dataset for technical checks, outside the 40-target pilot.

Two stages are evaluated on each target:

1. Replay saved deletion-only Adaptive search and Random search graphs, selected in the earlier frozen-feature SubgraphX experiment. Evaluate each graph with frozen and refreshed features. This is transfer of previously selected attacks, not a fair comparison of optimal attackers in the two scenarios.
2. Freshly generate 40 independent six-deletion proposals with the same candidate pool for both scenarios. Run SubgraphX for every proposal under both assumptions using selection seed 93001. Select separately by (label preserved, probability change <= 0.02, largest native-set disruption), with deterministic first-candidate tie resolution. Report feasibility failures, label changes, and all candidate scores. The first candidate is a one-draw random baseline. This is matched best-of-40 random search, not GXAttack or a new adaptive algorithm. Proposal count and unique evaluations are recorded separately. The matched pool controls search effort but cannot establish global robustness.

Evaluate each selected graph under BOTH feature assumptions on five fresh seeds 94001--94005. Clean and attacked explanations share each seed. Clean-to-clean repeats use independent seeds 95001--95005 and are a variability reference, not a matched causal null. No fresh-seed result is used for selection.

## Outcomes

Primary matched-search outcomes are (a) feasibility/label preservation, (b) native-set similarity, and (c) the joint preserved-label, <=2pp probability-change disruption score (zero credit for infeasible attacks). Report all targets; conditional both-feasible subsets are supplementary. Cross-evaluation distinguishes change in selected attack from change in processing assumptions. Retain continuous probability changes, native-set sizes, empty flags, and directly deleted explanatory rows. Primary paired difference: refreshed-search/refreshed-evaluation minus frozen-search/frozen-evaluation, after averaging fresh seeds within target. Also report same-edit refreshed-minus-frozen effects for each selection origin.

On clean and refreshed attacked graphs, compute hard and soft necessity and sufficiency failure using two explicitly different interventions: remove/retain graph edges with the evaluated feature matrix fixed, or remove/retain transaction records and recompute features. Frozen attacked graphs receive edge fidelity only: otherwise refreshing their stale features would be conflated with the explanatory-record intervention itself. Fidelity always concerns the evaluated graph's predicted class; prediction-changing cases remain flagged. Retention means keeping only selected transaction records globally. It is a severe intervention and does not resolve out-of-distribution concerns. Each explanation has 20 random sets of identical size from the same available local edge-row pool, shared between intervention modes. Recompute random controls for each selected size; sample variability is not additional independent targets. Do not interpret record-level fidelity as the uniquely correct replacement for conditional edge fidelity.

Use 5,000 target bootstrap samples, fixed seed, after averaging repeated seeds and search trials within targets. Intervals are descriptive conditional on these graphs/classifiers; graph-node dependence, training variation, and post-hoc target reuse remain limitations. The weak HI-Small classifier and legacy AMLSim preprocessing are inherited, not silently corrected. All results stay separate for review.

## Conditional larger pilot, frozen before new outcomes

Following the user's standing instruction to expand promising experiments, the manifest also freezes 50 different targets per dataset from the original correctly detected illicit test cohort, requiring at least six removable rows and excluding this pilot and its validation targets. Selection uses feasibility only. Expand a dataset only after all 20 screening targets finish and the primary paired fresh-seed joint-disruption effect (refreshed search/evaluation minus frozen search/evaluation) has absolute mean at least 0.10 and its 95% target-bootstrap interval excludes zero. Either direction can justify studying a processing-assumption effect; this is a screening rule, not a multiplicity-adjusted significance claim. Do not tune thresholds after outcomes.

Expansion evaluates matched searches and the first-random baseline on 50 new targets with two independent proposal pools and selection seeds 93002/93003, then five unseen evaluation seeds per trial (96001--96005 and 96101--96105). Old replay attacks are not available on this cohort and are not invented. Evaluate each selected graph under both feature assumptions. Average trials and fresh seeds within targets. Keep screening and expansion reports separate. Failure to pass the gate stops the experiment without trying alternate metrics for promotion.

## Implementation and verification

Use exact raw-row mappings. HI-Small recomputes incoming/outgoing count, sum, mean, population standard deviation and original log1p/training scaling. AMLSim reproduces its original 26 numeric features, sample standard deviations, extrema, distinct counterparties/types, timestamp extrema, log transformations and legacy ratios, with the original clean-fitted scaler. Static account fields remain unchanged. Candidate evaluation updates only affected accounts using their complete incident record histories, not just ego-graph records.

Before the pilot: reconstruct clean features and all edge rows; verify affected-account updates against an independent full raw-record rebuild; compare local and full-graph predictions for both scenarios and record-removal/retention interventions; verify native SubgraphX against saved same-seed results; verify unchanged weights. Fail on technical errors. The existing DGL worker is reused read-only with isolated request files and logs. The controller uses CUDA for local model/fidelity evaluations, one CPU thread, a 25% CUDA allocator limit and below-normal Windows priority. The DGL worker remains on two CPU threads. Original HI-Small files/processes are untouched.

Run `run.py validate` for the technical validation, then `run.py pipeline`. Source changes invalidate validation and resume manifests. Results are saved atomically per target with raw masks, candidates, random sets, update evidence, hashes and timing. Reports are provisional until all 40 target cases complete.

## Literature motivation (targeted review, not a first-ever claim)

- GXAttack optimizes adjacency with features retained in its formulation: https://arxiv.org/html/2406.06417v2#S4.SS1
- Graph Neural Network Explanations are Fragile studies constrained structural explanation attacks: https://proceedings.mlr.press/v235/li24bd.html
- The Feature-Space Illusion (SaTML 2026) motivates transaction-to-feature consistency for financial classification evasion: https://doi.org/10.1109/SaTML68715.2026.00023
- GInX-Eval motivates caution about removal-based fidelity: https://arxiv.org/abs/2309.16223

The proposed contribution is an audit of the dependence of prediction-preserving explanation attacks on transaction-to-feature coupling, not the invention of constrained financial attacks or a guarantee of realistic transactions.
