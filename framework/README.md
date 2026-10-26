# aml_starting_point_framwork

Saved starting framework, 29 September 2026. Copied from `C:\habib dissertation\replication_v3_scratch`.

## What is included

- Elliptic and IBM AMLSim: all six original CSVs under `data/raw`.
- Elliptic models: GCN, GAT, GraphSAGE, ChebNet and GATv2. AMLSim models: GCN, GraphSAGE and GATv2.
- Completed baseline results for all eight combinations, five seeds each (42–46): logs, per-seed metrics, summaries and comparisons.
- Fifteen saved AMLSim baseline checkpoints and one separately trained Elliptic GraphSAGE seed-42 checkpoint.
- GNNExplainer, PGExplainer and DGL SubgraphX code, plus the integrated two-dataset GraphSAGE case runner.
- Two completed faithfulness reports, their structured evidence, five PGExplainer fits per dataset, and SubgraphX selections.
- Approved report formatter: rankings, Top-1/Top-2 comparisons, probability changes, necessity, sufficiency and stability.
- Two UTF-8 dependency lists regenerated from the working environments. Environments themselves are not duplicated.

## Layout

| Folder/file | Purpose |
| --- | --- |
| `data/raw` | Original datasets |
| `data/external_repos/aml-elliptic-gnn` | Required upstream loader/model code and attribution |
| `src` | Dataset loaders and model definitions |
| `scripts` | Training, explainers, report formatter and run coordinators |
| `outputs` | Completed runs, checkpoints, logs, reports and evidence |
| `requirements-main.txt` | Main training/PyG environment |
| `requirements-subgraphx.txt` | Separate DGL/SubgraphX environment |
| `SOURCE_MANIFEST.json` | File hashes, original code provenance and snapshot verification |

## Model results

All 40 runs completed. Splits matched: Elliptic 30,266 / 6,985 / 9,313; AMLSim 6,500 / 1,500 / 2,000 (train / validation / test). F1 is for the illicit/fraud class; standard deviation is the sample standard deviation across five seeds.

| Dataset | Model | Historical F1 mean ± std | Framework run F1 mean ± std | Mean difference |
| --- | --- | --- | --- | ---: |
| IBM AMLSim | GATv2 | 0.7545 ± 0.0647 | 0.8177 ± 0.0568 | +0.0632 |
| IBM AMLSim | GCN | 0.3688 ± 0.0201 | 0.3583 ± 0.0175 | -0.0105 |
| IBM AMLSim | GraphSAGE | 0.9051 ± 0.0139 | 0.9035 ± 0.0101 | -0.0016 |
| Elliptic | chebnet | 0.8974 ± 0.0053 | 0.8975 ± 0.0075 | +0.0001 |
| Elliptic | gat | 0.7690 ± 0.0115 | 0.7664 ± 0.0126 | -0.0026 |
| Elliptic | gatv2 | 0.8688 ± 0.0048 | 0.8685 ± 0.0104 | -0.0003 |
| Elliptic | gcn | 0.6080 ± 0.0119 | 0.6097 ± 0.0119 | +0.0017 |
| Elliptic | graphsage | 0.8762 ± 0.0075 | 0.8788 ± 0.0073 | +0.0026 |

No combination exactly matched both historical statistics at four decimals. These are numerical comparisons, not statistical equivalence tests.

Detailed comparison: [report](outputs/baseline_check_20260929_105205/COMPARISON.md) and [CSV](outputs/baseline_check_20260929_105205/comparison.csv). Per-seed Elliptic metrics are under `outputs/results`; AMLSim metrics/checkpoints are under `outputs/baseline_check_20260929_105205/ibm_amlsim`.

## Explainer results

GraphSAGE model seed 42; explainer seeds 2026–2030. Targets are correctly detected illicit validation nodes, selected as the first model-index-ordered case with 4–100 incoming two-hop context nodes and 2–2,000 context edges. These are two demonstrations, not dataset-wide estimates. Node IDs in reports are model indices.

| Dataset | Target | Original illicit probability | Full report |
| --- | ---: | ---: | --- |
| elliptic | 10780 | 94.18% | [readable_results.txt](outputs/graphsage_explanations_seed42_v2/elliptic/readable_results.txt) |
| amlsim | 236 | 98.67% | [readable_results.txt](outputs/graphsage_explanations_seed42_v2/amlsim/readable_results.txt) |

First explainer seed (2026); full reports include connection endpoints, importance scores, probability changes and every seed:

| Dataset | Explainer | Selection | Edge IDs | Necessity ↑ | Sufficiency ↓ |
| --- | --- | --- | --- | ---: | ---: |
| elliptic | GNNExplainer | Top 1 | E30904 | 0 | 0 |
| elliptic | GNNExplainer | Top 2 | E30904, E31527 | 0 | 0 |
| elliptic | PGExplainer | Top 1 | E30904 | 0 | 0 |
| elliptic | PGExplainer | Top 2 | E30904, E31640 | 0 | 0 |
| elliptic | SubgraphX | Node group (2 induced edges) | See full report | 0 | 0 |
| amlsim | GNNExplainer | Top 1 | E420935 | 0 | 0 |
| amlsim | GNNExplainer | Top 2 | E420935, E1131141 | 0 | 0 |
| amlsim | PGExplainer | Top 1 | E729920 | 0 | 0 |
| amlsim | PGExplainer | Top 2 | E729920, E418267 | 0 | 0 |
| amlsim | SubgraphX | Node group (22 induced edges) | See full report | 0 | 0 |

Necessity = 1 when removing selected edges changes the original class (higher is better). Sufficiency = 1 when retaining only selected edges changes the class (lower is better). Tests physically remove/keep edges on the full graph, hold features fixed, and preserve separate parallel transaction rows.

| Dataset | Explainer | Budget | Five-run edge-set Jaccard |
| --- | --- | --- | ---: |
| elliptic | GNNExplainer | 1 | 0.200 |
| elliptic | GNNExplainer | 2 | 0.467 |
| elliptic | PGExplainer | 1 | 0.300 |
| elliptic | PGExplainer | 2 | 0.733 |
| elliptic | SubgraphX | Variable induced edges | 0.733 |
| amlsim | GNNExplainer | 1 | 0.100 |
| amlsim | GNNExplainer | 2 | 0.033 |
| amlsim | PGExplainer | 1 | 0.100 |
| amlsim | PGExplainer | 2 | 0.100 |
| amlsim | SubgraphX | Variable induced edges | 0.142 |

Jaccard 1 means identical edge selections; repeatability does not prove faithfulness. PG stability includes five independently fitted explainers. SubgraphX selects node groups, not ranked edges; AMLSim induced-edge counts were 22, 0, 27, 46 and 27. The empty selection is retained.

## Important implementation boundaries

- The original Elliptic five-seed training runner did not save weights. Its explanation model is a separately trained seed-42 GraphSAGE checkpoint (test F1 0.8841099164), not the exact checkpoint from the five-seed table.
- That checkpoint is retained at `outputs/graphsage_explanations_seed42_v1/elliptic/graphsage_seed42_new_checkpoint.pt`. The successful v2 run references it; keep it.
- v1 failed on undefined PG edge entropy for empty incoming contexts. v2 excludes such training nodes while retaining the copied confidence criteria, learning rate and epoch count. Failure logs remain for provenance.
- GNNExplainer runs on a verified incoming two-hop context; PGExplainer fits use full-graph training nodes; SubgraphX uses fixed-context feature coalitions. Local/full baseline logits and unchanged classifier weights were checked.
- The integrated runner currently supports the two GraphSAGE cases. Other model backbones require explicit integration and validation.
- The standalone report utility formats supplied evaluated metrics; it does not itself calculate faithfulness.

## Using this starting framework

Keep this copy as your starting snapshot. Copy it to a new project directory before changing research settings. Run commands from the project root and choose fresh output names.

Use Python 3.11 with separate main and SubgraphX environments. The tested main environment used PyTorch 2.11.0+cu128 / PyG 2.8.0.post1; SubgraphX used PyTorch 2.1.2+cu121 / DGL 2.2.1. The requirements files record installed versions, not a fully automated installer; CUDA/DGL package sources may be required when rebuilding them. No environment installation was performed for this snapshot.

Baseline comparison:

```powershell
python scripts/run_baseline_comparison.py
```

Two GraphSAGE case reports (main environment; supply your actual DGL Python path):

```powershell
python scripts/run_explainer_reports.py --output outputs/graphsage_explanations_new_run --dgl-python "PATH_TO_DGL_ENV/Scripts/python.exe"
```

The integrated runner reuses the bundled baseline AMLSim checkpoint and retained Elliptic checkpoint. Do not rerun into an existing output directory. It does not automatically select checkpoints from a future baseline run; update the explicit checkpoint selection when starting a new study.

Format already evaluated evidence:

```powershell
python scripts/faithfulness_report.py outputs/graphsage_explanations_seed42_v2/elliptic/report_input.json --output outputs/elliptic_report_new.txt
```

Keep only needed datasets, code, dependencies, checkpoints and evidence. Consolidate notes here. Avoid duplicate environments, cache folders and copied historical project trees.

## Snapshot verification and provenance

All source files were SHA-256 verified during copying. Dataset, model and explainer code, weights and numerical results were preserved. README was rewritten, dependency lists refreshed, and active report references relocated to D:. Original log paths and code-source paths remain historical provenance. SOURCE_MANIFEST.json records both inherited source entries and hashes of this snapshot (excluding itself).

Original code project: `C:\habib dissertation\Projects\AML-GNN-Replication-v2`. Expected Marasi upstream commit: `b02c6e6be51becf2147ce372002fef8998f17b21`.
