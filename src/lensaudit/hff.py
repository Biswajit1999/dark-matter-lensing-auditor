"""Curated, provenance-preserving access to official Hubble Frontier Fields products."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS


@dataclass(frozen=True)
class HFFAsset:
    role: str
    filename: str
    url: str
    expected_bytes: int
    description: str


@dataclass(frozen=True)
class HFFDataset:
    key: str
    cluster: str
    cluster_redshift: float
    lens_team: str
    lens_method: str
    release: str
    source_redshift: float | None
    archive_page: str
    model_readme: str
    warning: str
    assets: tuple[HFFAsset, ...]


ABELL2744_SHARON_V4COR = HFFDataset(
    key="abell2744-sharon-v4cor",
    cluster="Abell 2744",
    cluster_redshift=0.308,
    lens_team="Sharon / Johnson",
    lens_method="LENSTOOL parametric strong-lensing model",
    release="v4cor (corrected 2018-08-24)",
    source_redshift=None,
    archive_page="https://archive.stsci.edu/prepds/frontier/lensmodels/",
    model_readme="https://archive.stsci.edu/prepds/frontier/lensmodels/hlsp_frontier_model_abell2744_sharon_v4_readme.pdf",
    warning=(
        "Use v4cor, not v4orig: STScI marks the original Sharon v4 scaling as incorrect. "
        "The convergence normalization and constrained region must be read from the map-maker documentation."
    ),
    assets=(
        HFFAsset(
            role="light",
            filename="hlsp_frontier_hst_acs-60mas_abell2744_f814w_v1.0_drz.fits",
            url="https://archive.stsci.edu/pub/hlsp/frontier/abell2744/images/hst/v1.0-epoch1/hlsp_frontier_hst_acs-60mas_abell2744_f814w_v1.0_drz.fits",
            expected_bytes=131_800_320,
            description="HST ACS/WFC F814W drizzled science mosaic at 60 mas/pixel",
        ),
        HFFAsset(
            role="kappa",
            filename="hlsp_frontier_model_abell2744_sharon_v4cor_kappa.fits",
            url="https://archive.stsci.edu/pub/hlsp/frontier/abell2744/models/sharon/v4cor/hlsp_frontier_model_abell2744_sharon_v4cor_kappa.fits",
            expected_bytes=64_008_000,
            description="Corrected Sharon v4 convergence map",
        ),
    ),
)

HFF_DATASETS = {ABELL2744_SHARON_V4COR.key: ABELL2744_SHARON_V4COR}


def get_hff_dataset(key: str) -> HFFDataset:
    """Return a curated dataset contract, rejecting unreviewed identifiers."""

    try:
        return HFF_DATASETS[key]
    except KeyError as error:
        choices = ", ".join(sorted(HFF_DATASETS))
        raise ValueError(f"Unknown HFF dataset {key!r}. Available: {choices}") from error


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_hff_dataset(key: str, output: str | Path, *, overwrite: bool = False) -> Path:
    """Download official products and write a machine-readable receipt.

    Files are streamed to a partial path, checked for size and FITS signature, then
    atomically promoted. Existing files are preserved unless ``overwrite`` is true.
    """

    dataset = get_hff_dataset(key)
    destination = Path(output).expanduser().resolve() / key
    destination.mkdir(parents=True, exist_ok=True)
    receipts: list[dict[str, object]] = []

    for asset in dataset.assets:
        target = destination / asset.filename
        if target.exists() and not overwrite:
            if target.stat().st_size != asset.expected_bytes:
                raise ValueError(f"Existing file has unexpected size: {target}")
        else:
            partial = target.with_suffix(target.suffix + ".part")
            request = Request(asset.url, headers={"User-Agent": "lensaudit/0.2 (+research reproducibility)"})
            try:
                with urlopen(request, timeout=120) as response, partial.open("wb") as stream:
                    while chunk := response.read(1024 * 1024):
                        stream.write(chunk)
                if partial.stat().st_size != asset.expected_bytes:
                    raise ValueError(
                        f"Size mismatch for {asset.filename}: {partial.stat().st_size} != {asset.expected_bytes}"
                    )
                with partial.open("rb") as verification_stream:
                    signature = verification_stream.read(6)
                if signature != b"SIMPLE":
                    raise ValueError(f"Downloaded payload is not a primary-HDU FITS file: {asset.filename}")
                partial.replace(target)
            except Exception:
                if partial.exists():
                    partial.unlink()
                raise

        receipts.append({**asdict(asset), "actual_bytes": target.stat().st_size, "sha256": _sha256(target)})

    manifest = {
        "schema": "lensaudit.hff-receipt/1",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {**asdict(dataset), "assets": receipts},
    }
    receipt_path = destination / "provenance.json"
    receipt_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return receipt_path


def prepare_hff_pair(dataset_dir: str | Path, output: str | Path) -> tuple[Path, Path]:
    """Reproject the official F814W mosaic onto the κ grid and retain its footprint.

    This operation requires the optional ``reproject`` dependency. No interpolation
    of the lens map occurs: the image is mapped to the lens product's celestial WCS.
    """

    try:
        from reproject import reproject_interp
    except ImportError as error:  # pragma: no cover - depends on optional environment
        raise RuntimeError('Install the real-data extra with: pip install -e ".[hff]"') from error

    root = Path(dataset_dir).expanduser().resolve()
    science_path = root / ABELL2744_SHARON_V4COR.assets[0].filename
    kappa_path = root / ABELL2744_SHARON_V4COR.assets[1].filename
    output_root = Path(output).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    with fits.open(science_path, memmap=True) as science_hdul, fits.open(kappa_path, memmap=True) as kappa_hdul:
        science_hdu = science_hdul[0]
        kappa_hdu = kappa_hdul[0]
        target_wcs = WCS(kappa_hdu.header).celestial
        shape_out = np.squeeze(kappa_hdu.data).shape
        aligned, footprint = reproject_interp(science_hdu, target_wcs, shape_out=shape_out, return_footprint=True)
        image_header = kappa_hdu.header.copy()
        image_header["BUNIT"] = science_hdu.header.get("BUNIT", "HST F814W")
        image_header["HISTORY"] = "F814W reprojected onto Sharon v4cor kappa WCS by lensaudit"

    aligned_path = output_root / "abell2744-f814w-on-sharon-v4cor-grid.fits"
    footprint_path = output_root / "abell2744-f814w-reprojection-footprint.fits"
    fits.writeto(aligned_path, aligned.astype("f4"), image_header, overwrite=True)
    fits.writeto(footprint_path, footprint.astype("f4"), image_header, overwrite=True)
    return aligned_path, footprint_path
