# Supplemental explanation audit

This folder is isolated from the running HI-Small SubgraphX experiment. Existing experiment code, checkpoints, attacks, worker files and outputs are read-only inputs.

## Frozen scope

- Retrospective SubgraphX search-budget analysis: all 166 AMLSim targets, three completed source trials, proposal prefixes 1/5/10/20/40. Rank preserved labels first, then native-set cosine distance. Record unique proposals separately. First zero-similarity success must preserve the label; failures are censored at 40 proposals. Zero similarity is not explanation incorrectness. Only adaptive trajectories are available; no claim of superiority to random search from this curve.
- Fresh-seed GNNExplainer audit: 50 eligible test targets per dataset (AMLSim and HI-Small), sampled with NumPy seed 314159 from sorted registered eligible IDs without inspecting outcomes. Source attack trial is fixed at 2026. Methods: GNN-targeted GX adaptation, best-of-40 random search and random flipping. Saved edits are replayed without reoptimization.
- Fresh explanation seeds: 41001--41005; separate independent clean-repeat seeds: 51001--51005. Clean and attacked explanations use the same fresh seed; clean-repeat pairs use different seeds. Original selection-seed measurements are retained separately. The primary overlap outcome is binary top-25% cosine; Jaccard@10 and continuous cosine are supplementary.
- Random-explanation control: 20 uniform edge-row subsets per physical graph, cardinality min(10, number of explanation edges), sampled from that graph's complete two-hop explanation-edge pool. Identical random subsets are reused for comparisons with all five fresh seeds on a graph. This controls cardinality, not connectivity or degree. Record hard/soft necessity and sufficiency-failure, and explanation-minus-random gaps separately. A positive soft-necessity gap means a larger removal-induced probability drop; it is not ground-truth accuracy.
- Primary fidelity result: attacked-minus-clean change in excess soft necessity (explainer soft necessity minus random-set mean). Report absolute changes too, both unconditional and on label-preserved cases. Each graph uses its own original predicted class, matching the original study.
- No new classifier training, attack search, feature modification, defense claim or global novelty claim. One source attack seed and one frozen classifier per dataset limit generalization. Selection is retrospective on previously evaluated test targets; this is not an untouched confirmation set.

## Validation and execution

CUDA is used only for compact two-hop evaluation graphs. Full stored graph tensors remain on CPU; CPU threads are limited to one. On the first target in each dataset, compare the new local extraction and fitter against the existing native GNNExplainer and fidelity functions on the physical full graph, and check saved-mask and predicted-probability agreement. Audit output saves exact source/model hashes. Resume requires matching configuration, source and per-case input hashes. A failed technical gate halts the audit; low attack effectiveness never does.

Run `python followup_audit/search_budget.py`, then `python followup_audit/run.py --limit 1` for the timing/technical pilot (first preselected target per dataset), then `python followup_audit/run.py` for all 100 targets. Pilot cases are reused only with identical provenance. Reports remain explicitly provisional until all 100 cases are saved. Per-target files are atomic.

For uncertainty, average repeated explanation seeds within target before paired target resampling. For the search-budget analysis keep the three source trials together within each target. Percentile intervals describe target heterogeneity conditional on the saved graphs/models; they do not model dependence between connected nodes or training randomness. No seed row is treated as a new independent target.
