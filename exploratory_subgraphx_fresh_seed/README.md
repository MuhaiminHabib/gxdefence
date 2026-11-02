# HI-Small SubgraphX: fresh-seed audit

Separate audit of the completed HI-Small SubgraphX attack study. No attack is optimized again, and no source experiment is modified.

## Frozen protocol

- Sample 100 targets uniformly without replacement from all 795 targets in `subgraphx_hi_small/results/full/manifest.json`, using Python sampling seed 20261102. Sampling uses target IDs only, independently of attack success or explanation scores. Preserve the selected targets even if a check fails.
- Replay the saved seed-2026 adaptive SubgraphX-targeted attack and best-of-40 random-search attack for every target. Each has six original edge edits. Use the same classifier, features, physical edge order, and SubgraphX parameters as the source study.
- Fresh evaluation seeds: 131001, 131002, 131003, 131004, 131005. Pair clean and attacked graphs with the same fresh seed. Independent clean-repeat seeds: 132001, 132002, 132003, 132004, 132005. None is used for source attack selection. Each target receives 20 new explanation calls (clean, two attacked graphs, and clean repeat for each of five seeds), plus three source-seed reproduction checks.
- Use native SubgraphX edge sets without top-k truncation. Report binary set cosine, Jaccard, sizes/empty sets, label and probability preservation, and physical hard/soft removal and retention fidelity. Native fidelity uses every selected edge, not GNNExplainer's top-10 helper.
- Primary endpoint: adaptive-search fresh-minus-selection native similarity, after averaging the five fresh seeds within each target. A positive value means weaker overlap disruption under unseen randomness; it does not alone mean attack failure.
- Secondary endpoints: the same change for random search; fresh random-minus-adaptive similarity; change in that method contrast from selection to fresh seeds; similarity relative to independent clean repeats; and fidelity changes. Clean repeats are a variability reference, not a perfectly matched null.
- Use paired target-level bootstrap intervals (5,000 draws, seed 133001). Seeds are averaged within targets first. Do not treat 500 target/seed pairs as 500 independent targets. Intervals omit dependence between graph nodes, common evaluation-seed effects, and model-training variation; secondary intervals are descriptive and are not multiplicity-adjusted.
- All selected targets remain in the denominator; label preservation is reported separately. No probability cap is introduced retrospectively. This is a fixed-feature graph-store threat model and tests fresh explainer randomness conditional on one source attack run and one classifier, not generalization across models or datasets.

## Validation and execution

The first three preselected targets form a technical validation stage and are included in the 100-target audit. This stage is not an outcome-based promotion gate. It checks exact reproduction of source-seed native edge/node sets, source prediction/fidelity parity, full/local prediction parity on all three graphs, physical full/local fidelity parity on the first fresh seed, and same-seed clean reproducibility. Every later target still checks saved edits, original-seed explanations, prediction/fidelity parity and unchanged model weights.

`run.py pilot` freezes target IDs, configuration, source hashes and input hashes, then evaluates the three validation targets. `run.py pipeline` performs the validation stage if necessary and continues all 100 targets. Resuming requires exact manifest agreement. An exclusive controller lock prevents two writers; completed target records are immutable and each finished fresh-seed pair is checkpointed. Reports use completed targets only and remain provisional until 100/100 are present.

Use the existing main Python environment. The GPU evaluates predictions and fidelity with a 25% allocator cap; the unchanged DGL SubgraphX worker runs on CPU in its existing separate environment, preserving source-study behavior. Main CPU threads are limited to one and the DGL worker retains its original two-thread setting. Background processes use hidden windows and below-normal priority.

Outputs are confined to this folder: `results/manifest.json`, `results/status.json`, `results/validation.json`, `results/coverage.json`, `results/REPORT.md`, aggregate CSVs, immutable `results/cases/`, resumable `results/progress/`, and logs. Raw cases and worker contexts stay local.
