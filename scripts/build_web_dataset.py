"""Build a compact, traceable browser derivative from verified HFF FITS files.

This script never downloads data and never substitutes for the full-resolution
analysis. It area-aggregates an already reprojected F814W image, the unchanged
Sharon v4cor kappa map, and the reprojection footprint onto a small regular grid.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from astropy.io import fits
import numpy as np


def area_aggregate(array: np.ndarray, size: int) -> np.ndarray:
    """Return finite-pixel means in ``size × size`` non-overlapping area bins."""

    values = np.asarray(array, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError(f"Expected a 2D input, received {values.shape}.")
    if size < 16 or size > min(values.shape):
        raise ValueError("Output size must be between 16 and the shortest input axis.")
    y_edges = np.linspace(0, values.shape[0], size + 1, dtype=int)
    x_edges = np.linspace(0, values.shape[1], size + 1, dtype=int)
    output = np.empty((size, size), dtype=np.float64)
    for y in range(size):
        for x in range(size):
            block = values[y_edges[y] : y_edges[y + 1], x_edges[x] : x_edges[x + 1]]
            finite = block[np.isfinite(block)]
            output[y, x] = float(finite.mean()) if finite.size else np.nan
    return output


def prepare_light_derivative(image: np.ndarray) -> np.ndarray:
    """Background-subtract and asinh-compress an area-aggregated light image."""

    finite = image[np.isfinite(image)]
    if not finite.size:
        raise ValueError("The light derivative has no finite samples.")
    background = float(np.percentile(finite, 20))
    positive = np.clip(image - background, 0, None)
    scale = max(float(np.percentile(positive, 90)), 1e-12)
    return np.arcsinh(positive / scale)


def rounded_list(array: np.ndarray, digits: int = 7) -> list[float]:
    """Flatten a finite array into compact JSON-safe values."""

    fill = float(np.nanmedian(array[np.isfinite(array)]))
    finite = np.nan_to_num(array, nan=fill, posinf=fill, neginf=fill)
    return np.round(finite, digits).ravel().tolist()


def build_dataset(
    image_path: Path,
    kappa_path: Path,
    footprint_path: Path,
    receipt_path: Path,
    output_path: Path,
    *,
    size: int = 128,
) -> Path:
    """Build and write the versioned web-dataset JSON product."""

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    with fits.open(image_path, memmap=True) as image_hdul, fits.open(kappa_path, memmap=True) as kappa_hdul, fits.open(footprint_path, memmap=True) as footprint_hdul:
        image = np.squeeze(image_hdul[0].data)
        kappa = np.squeeze(kappa_hdul[0].data)
        footprint = np.squeeze(footprint_hdul[0].data)
        if image.shape != kappa.shape or image.shape != footprint.shape:
            raise ValueError(f"Aligned products must share one grid: {image.shape}, {kappa.shape}, {footprint.shape}.")
        image_small = prepare_light_derivative(area_aggregate(image, size))
        kappa_small = area_aggregate(kappa, size)
        footprint_small = area_aggregate(footprint, size)

    dataset = receipt["dataset"]
    payload = {
        "schema": "lensaudit.web-dataset/1",
        "id": dataset["key"],
        "title": f'{dataset["cluster"]} · F814W / convergence audit derivative',
        "width": size,
        "height": size,
        "light": rounded_list(image_small),
        "kappa": rounded_list(kappa_small),
        "footprint": rounded_list(footprint_small, 4),
        "display": {
            "lightTransform": "area mean → 20th-percentile subtraction → asinh(x / positive-p90)",
            "kappaUnit": "dimensionless convergence from source product; area-mean aggregated",
        },
        "provenance": {
            "clusterRedshift": dataset["cluster_redshift"],
            "lensTeam": dataset["lens_team"],
            "release": dataset["release"],
            "sourceArchive": dataset["archive_page"],
            "modelReadme": dataset["model_readme"],
            "generatedUtc": datetime.now(timezone.utc).isoformat(),
            "derivativeMethod": (
                f"Each {size}×{size} output cell is the finite-pixel area mean of one non-overlapping bin "
                "on the 4000×4000 Sharon WCS. No lens-map interpolation is performed in this step."
            ),
            "sourceAssets": [
                {"role": asset["role"], "filename": asset["filename"], "sha256": asset["sha256"]}
                for asset in dataset["assets"]
            ],
        },
        "limitations": [
            "The web derivative is for inspection and teaching, not publication-grade measurement.",
            "Area aggregation removes angular-resolution information; use the full FITS products for inference.",
            "Only the Sharon/Johnson v4cor reconstruction is bundled, so between-team systematics are absent.",
            "F814W surface brightness is a morphology proxy, not a stellar-mass map.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return output_path


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--image", type=Path, required=True, help="F814W FITS already reprojected onto the kappa WCS")
    argument_parser.add_argument("--kappa", type=Path, required=True, help="Sharon v4cor kappa FITS")
    argument_parser.add_argument("--footprint", type=Path, required=True, help="Reprojection footprint FITS")
    argument_parser.add_argument("--receipt", type=Path, required=True, help="Verified lensaudit provenance.json")
    argument_parser.add_argument("--output", type=Path, required=True, help="Destination JSON")
    argument_parser.add_argument("--size", type=int, default=128)
    return argument_parser


def main() -> None:
    args = parser().parse_args()
    path = build_dataset(args.image, args.kappa, args.footprint, args.receipt, args.output, size=args.size)
    print(path)


if __name__ == "__main__":
    main()
