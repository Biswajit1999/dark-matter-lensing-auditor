"""Generate synthetic weak-lensing validation evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from lensaudit.weak_lensing_validation import (
    ks_resolution_convergence,
    mass_sheet_degeneracy_sweep,
    shape_noise_profile_experiment,
)


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    research = root / "research"
    convergence = ks_resolution_convergence()
    shape_noise = shape_noise_profile_experiment()
    degeneracy = mass_sheet_degeneracy_sweep()
    _write_csv(research / "ks_resolution_convergence.csv", convergence)
    _write_csv(research / "shape_noise_profile.csv", shape_noise)
    _write_csv(research / "mass_sheet_degeneracy.csv", degeneracy)
    payload = {
        "schema": "lensaudit-weak-lensing-validation/1",
        "data_class": "synthetic known-truth numerical validation",
        "supports_observational_mass_claim": False,
        "kaiser_squires_resolution": convergence,
        "shape_noise_profile": shape_noise,
        "mass_sheet_degeneracy": degeneracy,
    }
    (research / "weak_lensing_validation.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)
    axes[0].loglog(
        [row["grid_size"] for row in convergence],
        [row["relative_error"] for row in convergence],
        marker="o",
    )
    axes[0].set(
        xlabel="Grid size (pixels per side)",
        ylabel="Aperture-mass relative error",
        title="Kaiser–Squires convergence",
    )
    axes[1].loglog(
        [row["source_density_arcmin2"] for row in shape_noise],
        [row["profile_rmse"] for row in shape_noise],
        marker="o",
        color="#7c3aed",
    )
    axes[1].set(
        xlabel="Source density (arcmin⁻²)",
        ylabel="Tangential-shear profile RMSE",
        title="Shape-noise sensitivity",
    )
    axes[2].semilogy(
        [row["lambda"] for row in degeneracy],
        [max(row["maximum_reduced_shear_difference"], 1e-18) for row in degeneracy],
        marker="o",
        color="#c2410c",
    )
    axes[2].set(
        xlabel="Mass-sheet transform λ",
        ylabel="Maximum |Δ reduced shear|",
        title="Degeneracy invariance",
    )
    figure.suptitle("Synthetic weak-lensing validation — not an observational mass measurement")
    figure.savefig(root / "docs/assets/weak-lensing-validation.png", dpi=180)
    plt.close(figure)
    print(
        json.dumps(
            {
                "finest_grid": convergence[-1],
                "highest_density": shape_noise[-1],
                "maximum_degeneracy_difference": max(
                    row["maximum_reduced_shear_difference"] for row in degeneracy
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
