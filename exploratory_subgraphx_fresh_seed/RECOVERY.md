# File-lock recovery, 2 November 2026

The initial background audit stopped at 06:53 Perth time after completing 18 targets. Target 73040 had four of its five fresh seeds checkpointed. A `PermissionError: [WinError 5]` occurred while replacing `results/status.tmp` with `results/status.json`. The workspace is under OneDrive, but the specific process holding the file was not identified.

`resume_resilient.py pipeline` loads the original frozen `run.py` and wraps only its JSON-save function and deterministic report generation with bounded retries for `PermissionError`. It retries at most 40 times, waiting at most two seconds between attempts. Non-permission failures are not suppressed. No model, graph, sampling, seed, explainer, metric or statistical code is changed. The frozen protocol, manifest and existing cases are not rewritten to bypass their hash checks.

Each launch saves a record under `results/recoveries/` with the wrapper/document hashes, original manifest hash, previous status and hashes of existing completed cases and progress checkpoints. The original startup still verifies input/source hashes, the exclusive controller lock, technical validation, and saved case identities. The interrupted target resumes from its last completed seed; finished targets are reused.

Use the same main Python environment as the original protocol. Background launches must be hidden. Process verification requires the host-side process inventory; the sandbox's `Get-Process` view may not show the host worker.
