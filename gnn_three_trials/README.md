# GNNExplainer: all eligible targets, three trials

Requested continuation: AMLSim 166 targets × 3 = 498 evaluations; HI-Small 795 × 3 = 2,385; total 2,883. Elliptic is excluded. Seeds: 2026–2028. Complete graphs, frozen classifiers/features and eligibility limits are unchanged.

The per-target computation is copied unchanged from the validated optimized GNNExplainer-primary runner: six edits, 100 outer steps, 100 inner steps and 40 candidates. The prior pilot remains the gate. Native-mask parity and hypergradient checks passed for this copy.

307 compatible saved evaluations are reused: 277 AMLSim and 30 HI-Small. Their original metadata and files are preserved. `results/reuse_registry.json` records exact source/result hashes; the numerical equivalence evidence covers the earlier index-caching optimization. Trial count and target cap describe run coverage, not per-target computations. All prior results remain in their original folders.

Run with the recorded Python environment:

```
python gnn_three_trials/run.py full --trials 3 --targets 0
```

Only one controller should run. Each completed case is saved atomically and reused on restart. `results/full/status.json` records runtime state. `results/full/TABLES_PAPER_LAYOUT.md` is updated after each case, with final tables withheld until all required cases are available. `REPORT.md` and CSVs contain provisional summaries while incomplete.

The final report provides cohort counts; Table II attack similarity, edits, label/probability changes; Table III cross-explainer harmonic fidelity; Table IV GNNExplainer Jaccard and hard/soft fidelity; and clean-repeat controls. Means and sample standard deviations are computed over three trial means. Harmonic fidelity is our summary of Fidelity+ and (1 − Fidelity−), not ground-truth explanation accuracy. No defence evaluation is included.
