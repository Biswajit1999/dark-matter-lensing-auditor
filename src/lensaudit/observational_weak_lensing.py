"""Validation of official MAST HFF strong+weak-lensing map products."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from astropy.io import fits
from skimage.metrics import structural_similarity

from lensaudit.core import kaiser_squires


MERTEN_BASE_URL = (
    "https://archive.stsci.edu/pub/hlsp/frontier/abell2744/models/merten/v1"
)
MERTEN_FILES = {
    role: f"hlsp_frontier_model_abell2744_merten_v1_{suffix}.fits"
    for role, suffix in {
        "gamma": "gamma",
        "gamma1": "gamma1",
        "gamma2": "gamma2",
        "kappa": "kappa",
        "magnification_z9": "z09-magnif",
    }.items()
}
EXPECTED_BYTES = 135_360


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_merten_maps(output: str | Path) -> Path:
    """Fetch the reviewed Merten v1 map set and write a SHA-256 receipt."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "provenance.json"
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text(encoding="utf-8"))
        retrieved_at_utc = previous.get("retrieved_at_utc")
    else:
        retrieved_at_utc = None
    assets = []
    for role, filename in MERTEN_FILES.items():
        target = output / filename
        url = f"{MERTEN_BASE_URL}/{filename}"
        if not target.exists():
            partial = target.with_suffix(".fits.part")
            request = Request(
                url, headers={"User-Agent": "lensaudit/0.5 observational-validation"}
            )
            try:
                with urlopen(request, timeout=60) as response, partial.open(
                    "wb"
                ) as stream:
                    while chunk := response.read(1024 * 1024):
                        stream.write(chunk)
                if partial.stat().st_size != EXPECTED_BYTES:
                    raise ValueError(f"unexpected byte count for {filename}")
                with fits.open(partial):
                    pass
                partial.replace(target)
            except Exception:
                partial.unlink(missing_ok=True)
                raise
        if target.stat().st_size != EXPECTED_BYTES:
            raise ValueError(f"existing map has unexpected byte count: {target}")
        assets.append(
            {
                "role": role,
                "filename": filename,
                "url": url,
                "bytes": target.stat().st_size,
                "sha256": _sha256(target),
            }
        )
    receipt = {
        "schema": "lensaudit.merten-receipt/1",
        "retrieved_at_utc": retrieved_at_utc or datetime.now(timezone.utc).isoformat(),
        "archive": "MAST Hubble Frontier Fields",
        "dataset": "Abell 2744 Merten v1 SaWLens strong+weak-lensing reconstruction",
        "assets": assets,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt_path


def _load_maps(root: Path) -> tuple[dict[str, np.ndarray], dict[str, fits.Header]]:
    maps: dict[str, np.ndarray] = {}
    headers: dict[str, fits.Header] = {}
    for role, filename in MERTEN_FILES.items():
        path = root / filename
        if not path.is_file():
            raise ValueError(f"missing reviewed map: {path}")
        with fits.open(path, memmap=False) as hdul:
            maps[role] = np.asarray(np.squeeze(hdul[0].data), dtype=float)
            headers[role] = hdul[0].header.copy()
    return maps, headers


def _best_affine(
    reference: np.ndarray, estimate: np.ndarray
) -> tuple[float, float, float, float, float]:
    design = np.column_stack([estimate.ravel(), np.ones(estimate.size)])
    slope, intercept = np.linalg.lstsq(design, reference.ravel(), rcond=None)[0]
    fitted = slope * estimate + intercept
    residual = reference - fitted
    correlation = float(np.corrcoef(reference.ravel(), estimate.ravel())[0, 1])
    normalized_rmse = float(np.sqrt(np.mean(residual**2)) / np.std(reference))
    ssim = float(
        structural_similarity(reference, fitted, data_range=float(np.ptp(reference)))
    )
    return float(slope), float(intercept), correlation, normalized_rmse, ssim


@dataclass(frozen=True)
class ProductValidation:
    gamma_identity_max_abs: float
    gamma_identity_rms: float
    magnification_median_relative_error: float
    magnification_p95_relative_error: float
    ks_boundary_sweep: tuple[dict[str, float | int], ...]
    b_mode_rms: float
    shape: tuple[int, int]
    lens_redshift: float
    source_redshift: float

    def to_dict(self) -> dict:
        result = asdict(self)
        result["data_kind"] = (
            "official observationally constrained strong+weak-lensing model products"
        )
        result["claim_boundary"] = (
            "This tests internal consistency of published Merten SaWLens maps; it neither "
            "reprocesses the source-galaxy shear catalogues nor constitutes a new mass measurement."
        )
        return result


def validate_merten_products(root: str | Path) -> ProductValidation:
    """Check map identity, magnification closure, WCS, and KS boundary sensitivity."""
    maps, headers = _load_maps(Path(root))
    shapes = {array.shape for array in maps.values()}
    if len(shapes) != 1 or len(next(iter(shapes))) != 2:
        raise ValueError(f"map shapes disagree: {sorted(shapes)}")
    shape = next(iter(shapes))
    wcs_keys = (
        "CTYPE1",
        "CTYPE2",
        "CRPIX1",
        "CRPIX2",
        "CRVAL1",
        "CRVAL2",
        "CDELT1",
        "CDELT2",
    )
    reference_wcs = tuple(headers["kappa"].get(key) for key in wcs_keys)
    if any(
        tuple(header.get(key) for key in wcs_keys) != reference_wcs
        for header in headers.values()
    ):
        raise ValueError("published products do not share one pixel/WCS grid")

    gamma_from_components = np.hypot(maps["gamma1"], maps["gamma2"])
    gamma_residual = maps["gamma"] - gamma_from_components

    determinant = (1 - maps["kappa"]) ** 2 - maps["gamma"] ** 2
    predicted_magnification = 1 / np.abs(determinant)
    published_magnification = np.abs(maps["magnification_z9"])
    stable = (
        np.isfinite(predicted_magnification)
        & np.isfinite(published_magnification)
        & (published_magnification > 0)
        & (published_magnification < 100)
    )
    relative_magnification_error = (
        np.abs(predicted_magnification[stable] - published_magnification[stable])
        / published_magnification[stable]
    )

    recovered, b_mode = kaiser_squires(maps["gamma1"], maps["gamma2"])
    sweep: list[dict[str, float | int]] = []
    for margin in (value for value in (0, 8, 16, 24, 32) if 2 * value < min(shape)):
        selection = (
            np.s_[margin : shape[0] - margin, margin : shape[1] - margin]
            if margin
            else np.s_[:, :]
        )
        slope, intercept, correlation, normalized_rmse, ssim = _best_affine(
            maps["kappa"][selection], recovered[selection]
        )
        sweep.append(
            {
                "edge_margin_pixels": margin,
                "pixels": int(maps["kappa"][selection].size),
                "affine_slope": slope,
                "mass_sheet_intercept": intercept,
                "pearson_correlation": correlation,
                "normalized_rmse": normalized_rmse,
                "structural_similarity": ssim,
            }
        )

    return ProductValidation(
        gamma_identity_max_abs=float(np.max(np.abs(gamma_residual))),
        gamma_identity_rms=float(np.sqrt(np.mean(gamma_residual**2))),
        magnification_median_relative_error=float(
            np.median(relative_magnification_error)
        ),
        magnification_p95_relative_error=float(
            np.percentile(relative_magnification_error, 95)
        ),
        ks_boundary_sweep=tuple(sweep),
        b_mode_rms=float(np.sqrt(np.mean(b_mode**2))),
        shape=(int(shape[0]), int(shape[1])),
        lens_redshift=float(headers["kappa"].get("Z_L", np.nan)),
        source_redshift=float(headers["kappa"].get("Z_S", np.nan)),
    )
