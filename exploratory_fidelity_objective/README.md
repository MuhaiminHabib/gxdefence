# Exploratory objective comparison - separate from the main study

This branch is experimental. Results are not incorporated into the main study or contribution claims without user review. Existing code, checkpoints and running experiments are read-only inputs.

## Question and controlled design

Does choosing a graph perturbation to reduce explanation soft necessity yield a larger necessity reduction on fresh explanation seeds than choosing a perturbation for cosine disruption?

Use the same 40 independently generated six-edit candidates for all three selectors: (1) minimum continuous edge-mask cosine relative to the clean explanation, (2) minimum signed soft necessity of the attacked explanation, and (3) the first feasible random candidate. This is a controlled comparison of candidate-selection objectives, not a new gradient-based GXAttack algorithm. Training-seed improvement of the optimized objective is expected by construction; only fresh-seed results can support promotion.

All selectors have identical topology permissions, models, features and candidate pools. Candidates must preserve the target class, change its original-class probability by at most 0.02 (two percentage points), and retain at least ten explanation-edge rows. Exactly ten edges are selected for fidelity. Candidate failures are recorded; targets with no feasible candidate remain in coverage/failure denominators and are not replaced. Cached duplicate candidates count as proposals but not new evaluations. No model retraining or automatic hyperparameter search.

Features and labels remain fixed; this is graph-store corruption. Edits use the original clean incoming two-hop node set, individually removable non-self-loop rows, and absent ordered pairs for additions. No parallel additions or self-loop edits. Native PyG GNNExplainer fits 100 epochs. The native fitter, physical graph reconstruction and fidelity evaluator are reused read-only from the validated followup_audit implementation.

## Screening and conditional expansion, frozen before outcomes

Screening: 20 randomly preselected eligible test targets per dataset, AMLSim and HI-Small, requiring at least ten clean explanation rows. One search trial; explanation selection seed 61001, evaluation seeds 71001--71005. Sample seed 1618033. Original test targets have been evaluated before; this remains exploratory.

The manifest also freezes 50 DIFFERENT targets per dataset for a potential expanded pilot before screening. If a dataset passes the rule below, evaluate those 50 additional targets with two independent candidate-pool/search trials, selection seeds 61002/61003 and evaluation seeds 81001--81005. Do not pool screening and expansion into a confirmation claim. Expansion is not automatically extended to a dataset that fails its gate.

Primary outcome is the fresh-seed mean reduction in signed soft necessity, clean minus attacked. The paired advantage is necessity-selector reduction minus comparator reduction. Average fresh seeds and search trials within each target before target bootstrap (5,000 resamples, fixed seed). Compare separately against cosine selection and first-feasible random selection. Report sufficiency, hard fidelity, overlap, prediction changes, and 20 size-matched random-explanation controls as secondary outcomes. Random-control subsets are independent of selector optimization. These are target-conditional descriptive intervals, not uncertainty over classifier training or graph-node dependence.

Automatic promotion for each dataset requires: all 20 screening targets attempted and all technical checks passed; feasible-candidate coverage at least 80%; fresh-seed necessity-reduction advantage at least 0.005 (0.5 percentage points) over BOTH comparators, with each paired 95% bootstrap lower bound greater than zero; and positive mean advantage over BOTH comparators after subtracting random-explanation necessity on each graph. A failed gate ends that dataset's experiment without tuning or replacing targets. A positive gate is a reason to test a larger pilot, not a publication-quality novelty or correctness claim. All outcomes, including negative or null results, remain saved.

## Execution and validation

Use the recorded main Python environment with `exploratory_fidelity_objective/run.py pilot`, followed by `... run.py pipeline`. The technical pilot uses the first preselected screening target in each dataset and is reused only with identical provenance. Full screening runs only after both technical pilots pass. Validate clean masks against original saved masks, local masks/fidelity against the original full-graph native path, candidate-local predictions against an independent full-graph forward on CPU, exact budgets/permissions, finite outputs and unchanged weights. Effectiveness is not a technical pass condition.

The GPU handles compact local graphs, with one CPU thread and a 25% GPU allocator limit. Full graph storage stays on CPU. One isolated background controller runs screening and, if qualified, expansion. Source/checkpoint/case hashes and resume manifests are saved. Per-target evidence is atomic, and reports explicitly distinguish incomplete, screening and expanded results. Any required implementation change must preserve previous evidence and rerun numerical parity checks before continuing under a new provenance manifest.
