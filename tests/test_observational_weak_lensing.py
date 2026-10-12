from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from lensaudit.observational_weak_lensing import MERTEN_FILES, validate_merten_products
from lensaudit.weak_lensing_validation import shear_from_kappa


def _write_fixture(root: Path, *, mismatched: bool = False) -> None:
    size = 64
    coordinate = np.arange(size) - size / 2
    y, x = np.meshgrid(coordinate, coordinate, indexing="ij")
    kappa = 0.2 * np.exp(-(x**2 + y**2) / (2 * 8**2))
    gamma1, gamma2 = shear_from_kappa(kappa)
    gamma = np.hypot(gamma1, gamma2)
    magnification = 1 / np.abs((1 - kappa) ** 2 - gamma**2)
    arrays = {
        "gamma": gamma,
        "gamma1": gamma1,
        "gamma2": gamma2,
        "kappa": kappa,
        "magnification_z9": magnification,
    }
    header = fits.Header(
        {
            "CTYPE1": "RA---TAN",
            "CTYPE2": "DEC--TAN",
            "CRPIX1": 32.0,
            "CRPIX2": 32.0,
            "CRVAL1": 3.58,
            "CRVAL2": -30.4,
            "CDELT1": -0.001,
            "CDELT2": 0.001,
            "Z_L": 0.308,
            "Z_S": 9.0,
        }
    )
    for role, filename in MERTEN_FILES.items():
        product_header = header.copy()
        if mismatched and role == "gamma2":
            product_header["CRPIX1"] = 31.0
        fits.writeto(root / filename, arrays[role].astype("f4"), product_header)


def test_product_validation_closes_identities(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    result = validate_merten_products(tmp_path)
    assert result.gamma_identity_rms < 1e-8
    assert result.magnification_median_relative_error < 1e-7
    assert result.ks_boundary_sweep[0]["pearson_correlation"] > 0.99
    assert result.ks_boundary_sweep[0]["structural_similarity"] > 0.99


def test_product_validation_rejects_wcs_mismatch(tmp_path: Path) -> None:
    _write_fixture(tmp_path, mismatched=True)
    with pytest.raises(ValueError, match="one pixel/WCS grid"):
        validate_merten_products(tmp_path)
