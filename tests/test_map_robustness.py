"""Synthetic identity and sensitivity checks for model-product diagnostics."""
import numpy as np
import pytest
from lensaudit.map_robustness import (
    lensing_jacobian_diagnostics, mass_sheet_invariance_audit, resolution_sensitivity,
)


def maps(size=64):
    y, x = np.mgrid[-1:1:complex(size), -1:1:complex(size)]
    k = 0.55 * np.exp(-(x*x + y*y) / 0.2)
    return k, 0.15 * np.sin(3*x), 0.15 * np.cos(3*y)


def test_uniform_subcritical_map_has_positive_parity():
    k = np.full((8, 8), 0.2)
    zero = np.zeros_like(k)
    r = lensing_jacobian_diagnostics(k, zero, zero)
    assert r["negative_parity_fraction"] == 0
    assert r["near_critical_fraction"] == 0
    assert r["median_abs_magnification_stable"] == pytest.approx(1 / 0.8**2)


def test_supercritical_shear_has_negative_parity():
    k = np.zeros((8, 8))
    g = np.full_like(k, 1.5)
    r = lensing_jacobian_diagnostics(k, g, np.zeros_like(g))
    assert r["negative_parity_fraction"] == 1


def test_near_critical_mask_is_exclusive():
    k = np.ones((8, 8))
    zero = np.zeros_like(k)
    r = lensing_jacobian_diagnostics(k, zero, zero)
    assert r["near_critical_fraction"] == 1
    assert r["median_abs_magnification_stable"] is None


def test_mass_sheet_invariance_to_roundoff():
    rows = mass_sheet_invariance_audit(*maps())
    assert len(rows) == 5
    assert all(r["max_reduced_shear_difference"] < 1e-12 for r in rows)
    assert all(r["max_relative_magnification_scaling_error"] < 1e-12 for r in rows)
    assert all(r["parity_changed_pixels"] == 0 for r in rows)


def test_mass_sheet_invalid_lambda():
    with pytest.raises(ValueError, match="positive"):
        mass_sheet_invariance_audit(*maps(), lambdas=[-0.5])


def test_resolution_uniform_map_is_invariant():
    k = np.full((64, 64), 0.2)
    zero = np.zeros_like(k)
    rows = resolution_sensitivity(k, zero, zero)
    assert [r["pixels"] for r in rows] == [4096, 1024, 256, 64]
    assert all(r["median_abs_magnification_stable"] == pytest.approx(1 / 0.8**2) for r in rows)


def test_resolution_central_structure_is_sensitive():
    k, g1, g2 = maps()
    rows = resolution_sensitivity(k, g1, g2, factors=[1, 4, 8])
    assert len(rows) == 3
    assert rows[0]["pixels"] > rows[-1]["pixels"]
    assert all(0 <= r["negative_parity_fraction"] <= 1 for r in rows)


def test_resolution_rejects_oversized_factor():
    with pytest.raises(ValueError, match="fewer than 4"):
        resolution_sensitivity(*maps(), factors=[32])


def test_bad_shapes_rejected():
    with pytest.raises(ValueError, match="matching 2-D"):
        lensing_jacobian_diagnostics(np.zeros((8, 8)), np.zeros((7, 8)), np.zeros((8, 8)))


def test_nonfinite_maps_rejected():
    k, g1, g2 = maps()
    k[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        lensing_jacobian_diagnostics(k, g1, g2)
