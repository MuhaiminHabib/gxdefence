from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = PROJECT_ROOT / "data" / "external_repos" / "aml-elliptic-gnn"
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "elliptic"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "results"

EXPECTED_UPSTREAM_COMMIT = "b02c6e6be51becf2147ce372002fef8998f17b21"
DEFAULT_SEEDS = [42, 43, 44, 45, 46]
DEFAULT_MODELS = ["gcn", "gat", "graphsage", "chebnet", "gatv2"]

HIDDEN_UNITS = 110
EPOCHS = 13_000
LEARNING_RATE = 9e-3
WEIGHT_DECAY = 5e-4
EARLY_STOPPING_PATIENCE = 1_000
SCHEDULER_PATIENCE = 100
SCHEDULER_FACTOR = 0.9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the official Marasi tx+agg models over multiple seeds."
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument(
        "--models", nargs="+", choices=DEFAULT_MODELS, default=DEFAULT_MODELS
    )
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument(
        "--output-prefix", default="marasi_new_5seed_txagg",
        help="Prefix below outputs/results; historical reference files are not overwritten.",
    )
    return parser.parse_args()


def validate_inputs() -> None:
    required_upstream = [
        UPSTREAM_ROOT / "loader.py",
        UPSTREAM_ROOT / "models" / "models.py",
    ]
    required_data = [
        DATA_DIR / "elliptic_txs_features.csv",
        DATA_DIR / "elliptic_txs_classes.csv",
        DATA_DIR / "elliptic_txs_edgelist.csv",
    ]
    missing = [path for path in required_upstream + required_data if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(map(str, missing)))


def load_upstream_components():
    sys.path.insert(0, str(UPSTREAM_ROOT))
    from loader import data_to_pyg, load_data
    from models import models as upstream_models

    return load_data, data_to_pyg, upstream_models


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def choose_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ModelArgs(dict):
    def __getattr__(self, key):
        return self[key]


def build_model(model_name: str, upstream_models, num_features: int):
    args = ModelArgs(num_classes=2)
    builders = {
        "gcn": lambda: upstream_models.GCNConvolution(args, num_features, HIDDEN_UNITS),
        "gat": lambda: upstream_models.GATConvolution(args, num_features, HIDDEN_UNITS),
        "graphsage": lambda: upstream_models.SAGEConvolution(args, num_features, HIDDEN_UNITS),
        "chebnet": lambda: upstream_models.ChebyshevConvolution(
            args, [1, 2], num_features, HIDDEN_UNITS
        ),
        "gatv2": lambda: upstream_models.GATv2Convolution(args, num_features, HIDDEN_UNITS),
    }
    return builders[model_name]()


def train_model(model, data, epochs: int) -> tuple[int, float]:
    optimizer = Adam(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        patience=SCHEDULER_PATIENCE,
        factor=SCHEDULER_FACTOR,
    )

    best_val_loss = float("inf")
    epochs_since_best = 0
    last_epoch = 0

    for epoch in range(epochs + 1):
        last_epoch = epoch
        model.train()
        optimizer.zero_grad()
        out, _ = model((data.x, data.edge_index))
        loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
        loss.backward()
        optimizer.step()

        with torch.no_grad():
            val_loss = F.cross_entropy(out[data.val_mask], data.y[data.val_mask])
        scheduler.step(val_loss)

        current_val_loss = float(val_loss.item())
        if current_val_loss < best_val_loss:
            best_val_loss = current_val_loss
            epochs_since_best = 0
        else:
            epochs_since_best += 1

        if epoch % 100 == 0:
            print(
                f"epoch={epoch:5d} train_loss={loss.item():.6f} "
                f"val_loss={current_val_loss:.6f}"
            )

        if epochs_since_best >= EARLY_STOPPING_PATIENCE:
            print(f"Early stopping at epoch {epoch}")
            break

    return last_epoch, best_val_loss


@torch.no_grad()
def evaluate(model, data) -> dict[str, float]:
    model.eval()
    logits, _ = model((data.x, data.edge_index))
    predictions = logits[data.test_mask].argmax(dim=1).cpu().numpy()
    labels = data.y[data.test_mask].cpu().numpy()

    return {
        "precision": precision_score(labels, predictions, pos_label=0, zero_division=0),
        "recall": recall_score(labels, predictions, pos_label=0, zero_division=0),
        "f1": f1_score(labels, predictions, pos_label=0, zero_division=0),
        "f1_micro_avg": f1_score(labels, predictions, average="micro"),
    }


def create_summary(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby(["dataset", "feature_setting", "model"], as_index=False)
        .agg(
            runs=("seed", "count"),
            train_samples=("train_samples", "first"),
            val_samples=("val_samples", "first"),
            test_samples=("test_samples", "first"),
            f1_mean=("f1", "mean"),
            f1_std=("f1", "std"),
            precision_mean=("precision", "mean"),
            recall_mean=("recall", "mean"),
            f1_micro_mean=("f1_micro_avg", "mean"),
        )
        .sort_values("model")
    )


def main() -> None:
    cli = parse_args()
    validate_inputs()
    load_data, data_to_pyg, upstream_models = load_upstream_components()
    device = choose_device(cli.device)

    print(f"Official upstream commit expected: {EXPECTED_UPSTREAM_COMMIT}")
    print(f"Device: {device}")
    print(f"Seeds: {cli.seeds}")
    print(f"Models: {cli.models}")
    print(f"Maximum epochs: {cli.epochs}")

    features, edges = load_data(str(DATA_DIR), noAgg=False)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    partial_path = OUTPUT_DIR / f"{cli.output_prefix}_partial_results.csv"
    results_path = OUTPUT_DIR / f"{cli.output_prefix}_results.csv"
    summary_path = OUTPUT_DIR / f"{cli.output_prefix}_summary.csv"

    if partial_path.exists():
        existing = pd.read_csv(partial_path)
        all_results: list[dict] = existing.to_dict("records")
        completed = {
            (int(row["seed"]), str(row["model"])) for row in all_results
        }
        print(f"Resuming from {partial_path} ({len(completed)} completed runs)")
    else:
        all_results = []
        completed = set()

    for seed in cli.seeds:
        for model_name in cli.models:
            if (seed, model_name) in completed:
                print(f"Skipping completed run: seed={seed} model={model_name}")
                continue

            print("=" * 100)
            print(f"Marasi Elliptic tx+agg | seed={seed} | model={model_name}")
            print("=" * 100)

            seed_everything(seed)
            data = data_to_pyg(features.copy(), edges.copy())
            model = build_model(model_name, upstream_models, data.num_features).to(device)
            data = data.to(device)

            last_epoch, best_val_loss = train_model(model, data, cli.epochs)
            metrics = evaluate(model, data)
            row = {
                "dataset": "Elliptic",
                "feature_setting": "tx+agg",
                "seed": seed,
                "model": model_name,
                "num_nodes": int(data.num_nodes),
                "num_edges": int(data.num_edges),
                "num_features": int(data.num_features),
                "train_samples": int(data.train_mask.sum().item()),
                "val_samples": int(data.val_mask.sum().item()),
                "test_samples": int(data.test_mask.sum().item()),
                "last_epoch": last_epoch,
                "best_val_loss": best_val_loss,
                **metrics,
            }
            all_results.append(row)
            pd.DataFrame(all_results).to_csv(partial_path, index=False)
            print(pd.DataFrame([row]).to_string(index=False))
            print(f"Partial results saved to: {partial_path}")

            del model, data
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    results = pd.DataFrame(all_results)
    summary = create_summary(results)
    results.to_csv(results_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("\nMarasi Elliptic five-seed summary")
    print(summary.to_string(index=False))
    print(f"\nSaved results to: {results_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
