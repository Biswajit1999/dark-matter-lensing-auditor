"""Fetch and validate official Abell 2744 Merten v1 lensing products."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from lensaudit.observational_weak_lensing import fetch_merten_maps, validate_merten_products

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "hff" / "abell2744-merten-v1"
RESEARCH = ROOT / "research"
FIGURE = ROOT / "docs" / "assets" / "merten-product-validation.png"


def main() -> None:
    fetch_merten_maps(RAW)
    result = validate_merten_products(RAW)
    payload = result.to_dict()
    receipt = json.loads((RAW / "provenance.json").read_text(encoding="utf-8"))
    payload["provenance"] = receipt
    (RESEARCH / "merten-product-validation.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    with (RESEARCH / "merten-ks-boundary-sweep.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result.ks_boundary_sweep[0]))
        writer.writeheader()
        writer.writerows(result.ks_boundary_sweep)

    margins = [row["edge_margin_pixels"] for row in result.ks_boundary_sweep]
    correlations = [row["pearson_correlation"] for row in result.ks_boundary_sweep]
    errors = [row["normalized_rmse"] for row in result.ks_boundary_sweep]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    axes[0].plot(margins, correlations, marker="o", color="#174a8b")
    axes[0].set(xlabel="Excluded edge margin (pixels)", ylabel="Pearson correlation", title="Kaiser–Squires morphology agreement")
    axes[1].plot(margins, errors, marker="o", color="#b85d00")
    axes[1].set(xlabel="Excluded edge margin (pixels)", ylabel="Normalized RMSE after affine fit", title="Finite-field boundary sensitivity")
    figure.suptitle("Abell 2744 Merten v1 observational product validation", fontweight="bold")
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)
    print(
        f"Validated {result.shape[0]}x{result.shape[1]} maps; "
        f"gamma identity RMS={result.gamma_identity_rms:.3e}; "
        f"median magnification closure={result.magnification_median_relative_error:.3e}"
    )


if __name__ == "__main__":
    main()

