import numpy as np
import pytest

from lensaudit.core import audit_mass_light, kaiser_squires, make_synthetic_cluster, robust_normalize


def test_robust_normalize_is_bounded():
    image = np.arange(100, dtype=float).reshape(10, 10)
    normalized = robust_normalize(image)
    assert np.nanmin(normalized) >= 0
    assert np.nanmax(normalized) <= 1


def test_synthetic_audit_is_deterministic_and_finite():
    image, ensemble = make_synthetic_cluster(size=96, models=12, seed=11)
    first = audit_mass_light(image, ensemble)
    second = audit_mass_light(image, ensemble)
    assert first.summary() == second.summary()
    assert np.isfinite(first.discrepancy_score[first.valid_mask]).all()
    assert first.centroid_offset_pixels > 0


def test_single_model_emits_systematics_warning():
    image, ensemble = make_synthetic_cluster(size=64, models=2)
    result = audit_mass_light(image, ensemble[0])
    assert any("Only one lens model" in warning for warning in result.warnings)


def test_shape_mismatch_stops_audit():
    image = np.ones((32, 32))
    kappa = np.ones((30, 32))
    with pytest.raises(ValueError, match="grids differ"):
        audit_mass_light(image, kappa)


def test_kaiser_squires_zero_shear_is_zero_mass():
    zeros = np.zeros((64, 64))
    e_mode, b_mode = kaiser_squires(zeros, zeros)
    assert np.allclose(e_mode, 0)
    assert np.allclose(b_mode, 0)


def test_kaiser_squires_rejects_mismatched_grids():
    with pytest.raises(ValueError, match="same grid"):
        kaiser_squires(np.zeros((16, 16)), np.zeros((15, 16)))
