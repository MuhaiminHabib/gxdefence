# Fixed-index runtime optimization (27 October 2026)

The live GNNExplainer-primary experiment repeatedly converted a fixed boolean mask to indices during each of 100 inner fitting steps, inside each of 100 attack steps. Profiling identified repeated `aten::nonzero` and associated synchronization overhead. The optimized implementation computes the nonzero indices once per mask fit, then uses index selection. Epochs, losses, seeds, targets, trials, graph construction, model precision, candidate count and final native-explainer scoring are unchanged.

The original code is preserved as before_core.py and before_run.py. benchmark_indices.py reconstructs the old and optimized fitters and compares scores, hypergradients and the full 100-step attack with 40 sampled candidates. The benchmark ran alongside the existing experiment, so timings are indicative rather than dedicated-machine measurements.

| Dataset / validation target | Original optimization | Optimized | Time reduction | Candidate equality |
|---|---:|---:|---:|---|
| AMLSim / 7598 | 101.34 s | 80.64 s | 20.4% | All 40 identical |
| HI-Small / 277872 | 94.00 s | 75.46 s | 19.7% | All 40 identical |

AMLSim mask error was zero and maximum gradient difference was 2.98e-8, also seen between original-code repeats. HI-Small mask difference was 5.96e-8 and gradient difference 7.63e-6; original repeats differed by 1.19e-7 and 1.14e-5 respectively. Gradient checks use absolute and relative tolerances (1e-7 and 1e-6); all actual sampled edit lists matched exactly. The HI-Small optimization trace maximum absolute difference was 1.79e-7. GPU floating-point nondeterminism means bitwise identity for every future outcome is not claimed.

Native PyG mask parity and independent finite-difference hypergradient validation were rerun successfully after applying the change. Only two representative real targets were used for the end-to-end benchmark, so this is not an exhaustive equivalence proof over every target.

The process was restarted with 275 completed cases preserved. The interrupted, unsaved case is recomputed. Existing cases retain their original source hashes; new cases record the updated hashes. gnn_primary/results/runtime_compatibility.json allows only this exact source transition and pins the validation evidence by SHA256; arbitrary changes still fail resume checks. The original manifest is retained here.

Overall case speedup will be smaller than the optimization-stage speedup because native candidate scoring, transfer evaluations and metrics are unchanged. Check new complete-case timings before revising the final ETA. No targets or trials were removed, and no mixed precision, approximate gradient truncation, early stopping or reduced attack budgets were introduced.
