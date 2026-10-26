# Reproducing and reviewing this research snapshot

This repository contains experiment source, protocols, aggregated results, and diagnostic reports. Raw datasets, prepared graphs, checkpoints, per-target case records, temporary files and machine logs remain in the original local workspace and are excluded from Git. This is a research snapshot, not a self-contained runnable distribution.

## Results to read first

- [Complete-graph report](complete_graphs/REPORT.md): five-trial results for all eligible targets, with the earlier pilot also shown.
- [Full-cohort soft fidelity](complete_graphs/results/soft_fidelity_full/REPORT.md): 166 AMLSim and 795 HI-Small targets; soft versus hard fidelity and all-edge-removal ablation.
- [Independent diagnostic pilot](complete_graphs/results/fidelity_diagnostic/REPORT.md): physical full-graph versus local edge-removal checks for 20 targets.
- [Complete-graph protocol](complete_graphs/PROTOCOL.md): graph construction, target eligibility, attack parameters and limitations.

The root-level reports describe the earlier study (including 50% HI-Small). The complete_graphs directory describes the later full-input-graph study. Do not combine their results.

## Environment and inputs

Recorded main environment: torch 2.2.2+cu121, torch-geometric 2.5.3, numpy 1.26.4, pandas 3.0.6, scikit-learn 1.9.1; see results/environment.json. SubgraphX ran in a separate torch 2.1.2+cu121 / DGL 2.2.1 environment. Framework requirements files are historical snapshots and differ from the environment that ran these experiments; they are not validated lockfiles for this study.

Acquire the Elliptic, AMLSim and HI-Small inputs separately under their applicable terms. The graph caches and original AMLSim classifier/PG checkpoints must also be restored to reproduce the exact saved runs: complete_graphs/prepare.py reuses those earlier AMLSim artifacts. They are not included in this repository.

Source scripts preserve original machine-specific dataset and Python paths. Before running elsewhere, review prepare.py, complete_graphs/prepare.py, run_study.py, complete_graphs/run_study.py and controller/launcher scripts, and adapt paths in a separate experiment copy. Source-hash checks intentionally prevent mixing old saved cases with modified runtime code.

With the inputs, checkpoints, dependencies and paths restored, the original workflow is: prepare.py; validate_core.py; continue_study.py. Run these from complete_graphs for the expanded study. Do not start concurrent controllers. paper_report.py formats its saved outputs. diagnose_fidelity.py and summarize_soft_fidelity.py require the excluded prepared graphs and original case/per-target files; their aggregate reports are included for review.

## Interpretation

The complete evaluation includes 8 Elliptic, 166 AMLSim and 795 HI-Small unique targets, each in five trials. All supplied graph records were used, but target eligibility restricts coverage. GXAttack used six directed edge edits and a larger search effort than random controls. GEA is unavailable. Hard and soft fidelity can move in different directions; the results do not demonstrate human-investigator deception. The all-edge ablation preserves features, including transaction-derived features. No robustness-method/defence evaluation has yet been completed.

## Attribution

The pinned GXAttack source in vendor is from https://github.com/ZhongLIFR/GXAttack at commit a5f1fd3a1e27941791c58d76728d6477b06788b9. Its MIT license is preserved in vendor/LICENSE. The framework was supplied as the project's existing research starting point. No blanket license is applied to all original project materials or datasets.
