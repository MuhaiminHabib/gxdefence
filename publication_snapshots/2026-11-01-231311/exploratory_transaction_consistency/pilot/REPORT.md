# Transaction-consistency pilot

**COMPLETE: 40/40 target-trial cases.**

SubgraphX; six deleted transaction rows; matched pools of 40 proposals; five fresh evaluation seeds. Frozen features model graph-store corruption; refreshed features model upstream record suppression. Classifiers, labels, static account fields and original preprocessing remain fixed. Expansion follows the frozen screening rule; screening and expansion are reported separately.

| Dataset | Selection origin | Processing | N | Similarity | Label preserved | Within label/2pp constraint | Joint disruption |
|---|---|---|---:|---:|---:|---:|---:|
| amlsim | First random | frozen | 20 | 0.7080 | 1.0000 | 1.0000 | 0.2920 |
| amlsim | First random | refreshed | 20 | 0.7020 | 1.0000 | 1.0000 | 0.2980 |
| amlsim | Replay adaptive | frozen | 20 | 0.5964 | 1.0000 | 1.0000 | 0.4036 |
| amlsim | Replay adaptive | refreshed | 20 | 0.5872 | 1.0000 | 1.0000 | 0.4128 |
| amlsim | Replay random search | frozen | 20 | 0.5981 | 1.0000 | 1.0000 | 0.4019 |
| amlsim | Replay random search | refreshed | 20 | 0.5910 | 1.0000 | 1.0000 | 0.4090 |
| amlsim | Search frozen | frozen | 20 | 0.5770 | 1.0000 | 1.0000 | 0.4230 |
| amlsim | Search frozen | refreshed | 20 | 0.5535 | 0.9500 | 0.9500 | 0.3965 |
| amlsim | Search refreshed | frozen | 20 | 0.5486 | 1.0000 | 1.0000 | 0.4514 |
| amlsim | Search refreshed | refreshed | 20 | 0.5446 | 1.0000 | 1.0000 | 0.4554 |
| hi_small | First random | frozen | 20 | 0.6442 | 1.0000 | 0.8000 | 0.2270 |
| hi_small | First random | refreshed | 20 | 0.6290 | 0.8500 | 0.8000 | 0.2423 |
| hi_small | Replay adaptive | frozen | 20 | 0.5142 | 1.0000 | 0.8000 | 0.3393 |
| hi_small | Replay adaptive | refreshed | 20 | 0.4936 | 0.9000 | 0.6500 | 0.2577 |
| hi_small | Replay random search | frozen | 20 | 0.4235 | 1.0000 | 0.8000 | 0.4315 |
| hi_small | Replay random search | refreshed | 20 | 0.4202 | 0.9000 | 0.7000 | 0.3533 |
| hi_small | Search frozen | frozen | 20 | 0.5748 | 1.0000 | 0.9500 | 0.3934 |
| hi_small | Search frozen | refreshed | 20 | 0.5468 | 1.0000 | 0.8500 | 0.3400 |
| hi_small | Search refreshed | frozen | 20 | 0.6335 | 1.0000 | 0.9500 | 0.3563 |
| hi_small | Search refreshed | refreshed | 20 | 0.6117 | 1.0000 | 1.0000 | 0.3883 |

Lower similarity means greater explanation disruption. Joint disruption is (1-similarity) with zero credit unless the label and 2pp probability constraint are both preserved. All targets remain in denominators, including cases with no feasible candidate. Saved replay attacks were selected under frozen features; interpret them as transfer evidence.

| Dataset | Matched search: refreshed minus frozen | Mean | 95% target interval |
|---|---|---:|---:|
| amlsim | similarity | -0.0324 | (-0.0842, 0.0125) |
| amlsim | preserved | 0.0000 | (0.0000, 0.0000) |
| amlsim | feasible | 0.0000 | (0.0000, 0.0000) |
| amlsim | delta_prob | 0.0001 | (0.0000, 0.0002) |
| amlsim | joint_disruption | 0.0324 | (-0.0140, 0.0823) |
| hi_small | similarity | 0.0369 | (-0.0588, 0.1384) |
| hi_small | preserved | 0.0000 | (0.0000, 0.0000) |
| hi_small | feasible | 0.0500 | (0.0000, 0.1500) |
| hi_small | delta_prob | -0.0013 | (-0.0072, 0.0031) |
| hi_small | joint_disruption | -0.0052 | (-0.1040, 0.0840) |

Paired intervals average seeds within targets before resampling. They are conditional descriptive intervals and do not include graph-node dependence or model-training uncertainty. The cohort has been evaluated previously. Empty/native-set cardinalities and clean-repeat variability are saved.

On clean and refreshed graphs, fidelity compares edge-only removal/retention with input features fixed versus raw-record removal/retention with feature refresh. Frozen attacked graphs have edge fidelity only: adding a refresh there would confound the intervention with a baseline feature correction. Fidelity concerns the current graph's predicted class; prediction-changing cases are flagged. Twenty size-matched random sets control cardinality, not connectivity or other distribution shift. Retention removes all other transaction records globally. These are distinct intervention questions, not evidence of ground-truth explanation correctness or a universal preferred metric.

Mean completed target runtime: 115.5 seconds.

Original studies and the ongoing HI-Small run are read-only. The HI-Small detector is weak and the legacy AMLSim scaling is reproduced as trained; neither limitation is silently repaired.