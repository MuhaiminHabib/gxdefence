# GNNExplainer-primary experiment

Separate implementation for AMLSim and HI-Small only. Elliptic is deliberately excluded. Existing complete_graphs code and results remain unchanged and supply read-only datasets, frozen checkpoints and reusable utilities.

## Scientific scope

This is a **GXAttack-objective adaptation targeting GNNExplainer**, not an exact reproduction of the original PGExplainer-targeted algorithm. GNNExplainer fits a fresh mask by optimization rather than applying a pretrained explanation network. The attack therefore differentiates through 100 functional Adam mask-fitting steps to obtain structural hypergradients. It uses no PGExplainer surrogate. PGExplainer and SubgraphX are downstream transfer comparisons on the selected attacked graph.

At binary graph presence and identical initialization, the functional mask fitter must match native PyG GNNExplainer. Candidate graph predictions must match full-graph physical edits. An independent central finite-difference test checks the unrolled gradient. Final candidate ranking and reported results use native PyG GNNExplainer, not the differentiable surrogate mask.

The relaxed union graph contains absent candidate edges and any external boundary nodes reachable within two hops. Edge presence affects aggregation degrees; explanation masks affect messages but not degrees. Mask-size and entropy regularization are presence-weighted in the relaxation. The first-iteration nonzero-gradient support is treated as a fixed gate for differentiation, as a piecewise-smooth approximation. Shared union-graph initialization differs from fresh native initialization on each compact physical graph; native rescoring is mandatory.

## Runs

Use the experiment's recorded main Python environment. The DGL worker remains in its separate original environment. Read ../REPRODUCIBILITY.md for missing inputs and machine-specific paths. Do not run concurrent controllers.

```
python gnn_primary/validate.py
python gnn_primary/run.py smoke --outer 3 --draws 4 --targets 1 --trials 1
python gnn_primary/run.py pilot
python gnn_primary/run.py full --trials 5 --targets 0
```

The smoke run only checks two validation targets. The pilot uses the three previously selected validation targets per dataset and two seeds (12 target-trial cases). The full run uses every previously eligible test target (166 AMLSim, 795 HI-Small) and five seeds. A complete pilot with matching source hashes and outer/draw settings is required before full execution. Resume accepts only identical source hashes and parameters.

`continue_after_pilot.ps1` waits for an already-running pilot and starts the full run only after completion. Start at most one such controller. Its pipeline status and full log are saved under results. In the full command, targets=0 records that no target cap is requested; the full phase always enumerates every eligible test target.

## Registered initial settings

- Original frozen classifiers and feature definitions; six directed edge edits; original eligibility limits.
- GNNExplainer: edge-only masks, 100 Adam steps, lr 0.01, native PyG size/entropy coefficients.
- Attacker: 100 projected outer steps, lr 0.01, explanation cosine-distance weight 0.1, entropy weight 0.0005, one seeded interior initialization, 40 discretized candidates. Selection prefers preserved labels, then native GNN explanation cosine distance. Label-changing outcomes are retained.
- Random flipping and random rewiring: one draw each. Additional random search: 40 candidates selected using the same native-GNN criterion. This matches candidate evaluation count, not total computational effort.
- Report binary top-25% similarity, Jaccard and hard/soft fidelity at top-5/10/20 and top-25%, plus native SubgraphX sets. Soft metrics retain signed probability differences. GNN clean-repeat controls use a second seed.
- No human deception claim; no ground-truth explanation accuracy; no defence method implemented here yet.

## Sources

- GXAttack paper and implementation: https://arxiv.org/abs/2406.06417 and ../vendor (pinned source).
- GNNExplainer: https://proceedings.neurips.cc/paper/2019/hash/d80b7040b773199015de6d3b4293c8ff-Abstract.html
- Native parity target: installed torch-geometric 2.5.3 GNNExplainer. The validated source implements Adam lr 0.01, edge_size 0.005, edge_ent 1.0 and first-step gradient support gating.

This new run must not be combined with earlier PG-targeted attack results. Full-result interpretation follows the pilot and full-run completion gates, not merely successful code execution.
