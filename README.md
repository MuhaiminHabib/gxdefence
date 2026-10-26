# Financial GXAttack study

Start with [Reproducibility and results guide](REPRODUCIBILITY.md), the [complete-graph results](complete_graphs/REPORT.md), and the [full-cohort fidelity investigation](complete_graphs/results/soft_fidelity_full/REPORT.md). The sections below describe the earlier sampled study. Raw data and model checkpoints are excluded from Git.

Read PROTOCOL.md for the revised experiment and REPORT.md for measured results.

- framework/: isolated copy of the supplied starting framework and historical results.
- vendor/: pinned GXAttack source used to audit objective and metrics; commit a5f1fd3a1e27941791c58d76728d6477b06788b9.
- prepared/: graphs, frozen model weights, five PG fits per dataset, HI-Small selected source-row IDs, provenance and training history.
- results/pilot/: validation pilot cases, metrics, summaries and technical checks.
- results/full/: held-out test cases and summaries, written incrementally.
- results/pipeline_status.json: overall execution state.
- results/environment.json: main package versions. DGL worker uses the existing separate PyTorch 2.1.2 / DGL 2.2.1 environment.

The pipeline saves each case atomically and can resume completed cases. Do not run two controllers concurrently. A failed pilot stops promotion. Full-run failures preserve prior results and a traceback. Failed attacks that change the prediction are valid measured outcomes and remain in the tables.

Main interpreter used:

`C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe`

Commands from this directory:

```powershell
& 'C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe' validate_core.py
& 'C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe' prepare.py
& 'C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe' continue_study.py
```

The controller finishes remaining pilot cases, checks completion, runs all full cases and writes REPORT.md. No packages were installed into the existing environments. No literature review or defence work is included.

Scope decisions: 50 eligible test targets per dataset (all if fewer), five trials, fixed six directed edits. Only GXAttack is transferred to the other explainers; random controls have PGExplainer measurements. Additional metrics are set overlap and physical-edge necessity/sufficiency. RBO and relevance-label metrics remain deferred as recorded in the protocol. XGNN-loss/deduction attacks are outside this GXAttack-focused study; tables are explicitly adapted comparisons.
