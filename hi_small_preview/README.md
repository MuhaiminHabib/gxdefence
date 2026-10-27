# HI-Small 30-target preview

User-requested replacement for the unfinished all-target run, 27 October 2026. Exactly 30 unique eligible illicit test targets are selected uniformly without replacement using seed 42 from the existing 795-target eligible cohort. Each is evaluated once, using trial seed 2026. Selection is saved before outcomes are computed. This gives 30 target-trial cases, not 30 targets times five trials.

This separate directory preserves the stopped gnn_primary experiment. Source is copied from its validated fixed-index implementation; only dataset selection, target sampling, trial count and report labels change. GNNExplainer is the direct target; PGExplainer/SubgraphX are comparison explainers. Attack budget remains six edits, 100 outer steps, 100 inner fitting steps, 40 native-scored candidates, and the same random controls. No Elliptic or AMLSim work is launched here.

Run validate.py and then run.py preview with the main experiment interpreter. Results are saved under results/preview, including selected_targets.json, case evidence, per-target metrics and aggregate tables. Every case is saved atomically; failed/in-progress cases are not counted. Means describe these 30 selected targets only. Across-trial SD is unavailable because there is only one trial.

AMLSim results are preserved at ../gnn_primary/results/amlsim_stopped/REPORT.md. Its primary table uses the completed 166-target trial; a further 111 second-trial cases are retained separately as incomplete evidence. Do not combine those cases with this preview as though the original five-trial experiment completed.
