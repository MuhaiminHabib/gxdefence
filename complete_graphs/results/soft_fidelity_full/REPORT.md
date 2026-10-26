# Full-cohort hard and soft fidelity: AMLSim and HI-Small

All existing eligible test targets, five saved trials. No attack rerun or model retraining. Full saved-metric aggregation; the earlier independent physical-edge audit remains a 20-target pilot. Every eligible target is included in the new all-edge-removal ablation.

Soft+ is the signed baseline probability minus the probability after removing explanation edges. Soft- is the signed baseline probability minus the probability after retaining explanation edges. Each graph uses its own predicted class as reference. Negative values indicate increased probability, not an error. Mean absolute changes and signed distributions are saved to expose cancellation.

## Coverage

| Dataset | Targets | Trials | Evaluations | GXAttack label changes |
|---|---:|---:|---:|---:|
| amlsim | 166 | 5 | 830 | 0 |
| hi_small | 795 | 5 | 3975 | 14 |

## GXAttack: clean versus attacked

Means +/- sample SD across the five trial means. PG/GNN use top-10 capped by available edges; SubgraphX uses its native set. Soft values below are percentage points. Hard values below are percentages of class changes.

| Dataset | Explainer | Metric | Clean | Attacked |
|---|---|---|---:|---:|
| amlsim | PGExplainer | hard_plus | 0.2410 +/- 0.3300 | 0.0000 +/- 0.0000 |
| amlsim | PGExplainer | hard_minus | 1.6867 +/- 2.1041 | 1.4458 +/- 1.2492 |
| amlsim | PGExplainer | soft_plus | -0.0143 +/- 0.0309 | -0.0021 +/- 0.0064 |
| amlsim | PGExplainer | soft_minus | 0.0850 +/- 1.9421 | 0.0091 +/- 1.4437 |
| amlsim | GNNExplainer | hard_plus | 0.6024 +/- 0.0000 | 0.4819 +/- 0.2694 |
| amlsim | GNNExplainer | hard_minus | 1.8072 +/- 0.9525 | 1.2048 +/- 0.7378 |
| amlsim | GNNExplainer | soft_plus | 0.1228 +/- 0.0196 | 0.1167 +/- 0.0137 |
| amlsim | GNNExplainer | soft_minus | 0.0410 +/- 0.6966 | -0.4767 +/- 0.4312 |
| amlsim | SubgraphX | hard_plus | 1.3253 +/- 0.5040 | 0.3614 +/- 0.3300 |
| amlsim | SubgraphX | hard_minus | 3.7349 +/- 1.0776 | 2.8916 +/- 0.6599 |
| amlsim | SubgraphX | soft_plus | 0.8861 +/- 0.2519 | 0.4548 +/- 0.1456 |
| amlsim | SubgraphX | soft_minus | 2.4277 +/- 0.7232 | 1.9366 +/- 0.5517 |
| hi_small | PGExplainer | hard_plus | 5.7358 +/- 1.9418 | 4.1509 +/- 0.6162 |
| hi_small | PGExplainer | hard_minus | 6.2893 +/- 3.4252 | 5.2327 +/- 2.3509 |
| hi_small | PGExplainer | soft_plus | 2.9821 +/- 1.9527 | 3.7450 +/- 2.0518 |
| hi_small | PGExplainer | soft_minus | -0.1000 +/- 2.9225 | 0.3300 +/- 2.7133 |
| hi_small | GNNExplainer | hard_plus | 5.6101 +/- 1.8500 | 3.8742 +/- 0.8220 |
| hi_small | GNNExplainer | hard_minus | 6.0881 +/- 1.0696 | 4.6038 +/- 0.6327 |
| hi_small | GNNExplainer | soft_plus | 2.6839 +/- 0.8207 | 3.2753 +/- 0.5832 |
| hi_small | GNNExplainer | soft_minus | -0.2258 +/- 0.9607 | 0.0458 +/- 0.6036 |
| hi_small | SubgraphX | hard_plus | 9.5346 +/- 0.5993 | 5.8365 +/- 0.6750 |
| hi_small | SubgraphX | hard_minus | 6.7673 +/- 0.1866 | 4.8805 +/- 0.5140 |
| hi_small | SubgraphX | soft_plus | 5.6970 +/- 0.1721 | 5.8162 +/- 0.2513 |
| hi_small | SubgraphX | soft_minus | -4.7024 +/- 0.0973 | -4.5848 +/- 0.2643 |

## All-edge-removal ablation

One deterministic evaluation per unique target with the frozen model; node features are retained.

| Dataset | Labels preserved | Mean clean illicit probability | Mean no-edge illicit probability | Mean probability drop (pp) |
|---|---:|---:|---:|---:|
| amlsim | 165/166 | 97.482% | 98.612% | -1.130 |
| hi_small | 739/795 | 67.561% | 66.617% | 0.945 |

## Explanation-size sensitivity

GXAttack/PGExplainer means; soft metrics in percentage points, hard necessity in percent.

| Dataset | k | Clean hard+ | Attacked hard+ | Clean soft+ | Attacked soft+ |
|---|---:|---:|---:|---:|
| amlsim | 5 | 0.1205 | 0.0000 | -0.0118 | -0.0016 |
| amlsim | 10 | 0.2410 | 0.0000 | -0.0143 | -0.0021 |
| amlsim | 20 | 0.3614 | 0.1205 | 0.0093 | 0.0248 |
| hi_small | 5 | 4.4277 | 2.9182 | 2.1494 | 2.9225 |
| hi_small | 10 | 5.7358 | 4.1509 | 2.9821 | 3.7450 |
| hi_small | 20 | 7.6981 | 5.7862 | 3.4589 | 4.3133 |

## Interpretation limits

The saved full experiment contains fidelity for fixed k=5/10/20 and native SubgraphX sets. Top-25% fidelity remains pilot-only; binary top-25% similarity is a different metric. Summary CSV includes random baselines, signed distributions, mean absolute values and prediction-preserved-only results.

No-edge ablation retains transaction-derived features (including HI-Small aggregate features) and learned root transformations. It is not a separately trained feature-only model and does not establish independence from transaction information. Low soft means can hide opposing effects; inspect distributions. The eligible cohort is not the whole test population. Neither fidelity nor similarity establishes human-investigator deception.

## Findings

The full cohort revises the pilot interpretation. HI-Small soft necessity increases after GXAttack for PGExplainer (2.9821 to 3.7450 percentage points), GNNExplainer (2.6839 to 3.2753), and SubgraphX (5.6970 to 5.8162), although hard necessity decreases. Therefore uniform explanation-fidelity degradation is not supported. Average probability drops and the frequency of crossing a class boundary can move in opposite directions. This direction also persists in the label-preserved PG/GNN summaries saved in summary.csv.

AMLSim clean PG soft necessity is near zero (-0.0143 percentage points); its mean absolute removal-induced probability change is also small (about 0.0407 percentage points). Thus this result is not merely cancellation of large positive and negative effects. Clean GNN soft necessity is 0.1228 percentage points and SubgraphX is 0.8861, so do not generalize the PG finding to identical effects across every explainer.

The all-edge ablation preserves 165/166 AMLSim labels (99.40%) and 739/795 HI-Small labels (92.96%). Unlike the 20-target pilot, preservation is not universal. This supports an explanation for low hard necessity in this eligible cohort: most decisions survive without graph connections when features and parameters remain fixed. It does not establish that the trained models never use graph structure.

Increasing PG selection from top-5 to top-20 raises clean hard necessity on HI-Small from 4.4277% to 7.6981%, but it remains low. Larger selections should be reported as size sensitivity rather than selected post hoc for more favorable conclusions. No new defence experiment has been run.
