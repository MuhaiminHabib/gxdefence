# HI-Small: SubgraphX-primary single trial

Queued after the running AMLSim SubgraphX experiment completes all 498 evaluations. This separate folder preserves the AMLSim code and results.

Full cohort: all 795 eligible HI-Small illicit test targets, one trial with seed 2026. A three-target validation pilot with the same seed runs first, saves results and must pass before full execution. Pilot targets are distinct validation targets, not test targets.

Copied SubgraphX-targeted discrete search: six directed edits, 40 adaptive proposals, original classifier/features, original SubgraphX parameters. Random flipping, rewiring and best-of-40 random search remain included. PGExplainer and GNNExplainer are transfer comparisons. This is not gradient-based GXAttack. Native SubgraphX sets are not truncated to top-k. Report single-trial means without between-trial standard deviations.

Start the sequential controller once with the recorded main Python environment:

```
python subgraphx_hi_small/after_amlsim.py
```

Queue status: results/queue_status.json. After startup, progress is in results/pilot/status.json then results/full/status.json. Per-case evidence, CSV summaries and reports are saved under their phase folders. Resume uses exact source and parameter hashes. See ../subgraphx_primary/README.md for search details and ../REPRODUCIBILITY.md for runtime and input dependencies.
