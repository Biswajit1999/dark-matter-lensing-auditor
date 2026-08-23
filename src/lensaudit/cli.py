"""Command-line interface for reproducible FITS audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from astropy.io import fits

from .core import audit_mass_light, make_synthetic_cluster
from .io import read_fits
from .hff import HFF_DATASETS, download_hff_dataset, prepare_hff_pair
from .plotting import make_audit_figure


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit lensing mass contours against a luminous-matter proxy.")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze a science image and kappa FITS product.")
    analyze.add_argument("image", type=Path, help="2D FITS science image")
    analyze.add_argument("kappa", type=Path, help="2D kappa map or 3D model ensemble FITS")
    analyze.add_argument("--output", type=Path, default=Path("lensing-audit"))
    analyze.add_argument("--sigma", type=float, default=2.0, help="light-proxy Gaussian smoothing in pixels")
    demo = sub.add_parser("demo", help="Generate and analyze a synthetic cluster.")
    demo.add_argument("--output", type=Path, default=Path("lensing-demo"))
    demo.add_argument("--seed", type=int, default=7)
    fetch = sub.add_parser("hff-fetch", help="Download a curated official Hubble Frontier Fields dataset.")
    fetch.add_argument("dataset", choices=sorted(HFF_DATASETS), nargs="?", default="abell2744-sharon-v4cor")
    fetch.add_argument("--output", type=Path, default=Path("data/hff"))
    fetch.add_argument("--overwrite", action="store_true")
    prepare = sub.add_parser("hff-prepare", help="Reproject the HFF light image onto the lens-map WCS.")
    prepare.add_argument("dataset_dir", type=Path, help="directory produced by hff-fetch")
    prepare.add_argument("--output", type=Path, default=Path("data/hff/prepared"))
    return parser


def _write(output: Path, image: np.ndarray, kappa: np.ndarray, result) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fits.writeto(output / "science-image.fits", image, overwrite=True)
    fits.writeto(output / "kappa-ensemble.fits", kappa, overwrite=True)
    fits.writeto(output / "discrepancy-score.fits", result.discrepancy_score, overwrite=True)
    (output / "summary.json").write_text(json.dumps(result.summary(), indent=2), encoding="utf-8")
    make_audit_figure(result, output / "audit.png")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "hff-fetch":
        receipt = download_hff_dataset(args.dataset, args.output, overwrite=args.overwrite)
        print(receipt)
        return 0
    if args.command == "hff-prepare":
        aligned, footprint = prepare_hff_pair(args.dataset_dir, args.output)
        print(json.dumps({"aligned_image": str(aligned), "footprint": str(footprint)}, indent=2))
        return 0
    if args.command == "demo":
        image, kappa = make_synthetic_cluster(seed=args.seed)
    else:
        image, _, _ = read_fits(args.image)
        kappa, _, _ = read_fits(args.kappa)
    result = audit_mass_light(image, kappa, smoothing_sigma=getattr(args, "sigma", 2.0))
    _write(args.output, image, kappa, result)
    print(json.dumps(result.summary(), indent=2))
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
