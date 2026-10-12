import numpy as np

from lensaudit.weak_lensing_validation import (
    ks_resolution_convergence,
    mass_sheet_degeneracy_sweep,
    shape_noise_profile_experiment,
    shear_from_kappa,
)


def test_forward_inverse_recovers_demeaned_e_mode():
    coordinate = np.linspace(-1, 1, 64, endpoint=False)
    y, x = np.meshgrid(coordinate, coordinate, indexing="ij")
    kappa = np.exp(-5 * (x**2 + y**2))
    gamma1, gamma2 = shear_from_kappa(kappa)
    from lensaudit.core import kaiser_squires

    recovered, b_mode = kaiser_squires(gamma1, gamma2)
    # Even-sized FFT grids contain Nyquist modes whose discrete spin-2
    # convention leaves a sub-ppm residual; this bound records that limit.
    assert np.max(np.abs(recovered - (kappa - np.mean(kappa)))) < 1e-6
    assert np.sqrt(np.mean(b_mode**2)) < 1e-12


def test_aperture_mass_converges_with_resolution():
    rows = ks_resolution_convergence((32, 64, 128, 256))
    assert rows[-1]["relative_error"] < rows[0]["relative_error"]
    assert rows[-1]["relative_error"] < 0.01
    assert max(row["b_mode_rms"] for row in rows) < 1e-12


def test_shape_noise_decreases_with_source_density():
    rows = shape_noise_profile_experiment((10, 80), replicates=60)
    assert rows[1]["profile_rmse"] < rows[0]["profile_rmse"]
    assert 0.85 < rows[1]["nominal_95pct_coverage"] < 1.0


def test_mass_sheet_transform_preserves_reduced_shear():
    rows = mass_sheet_degeneracy_sweep((0.6, 1.0, 1.4), size=48)
    assert max(row["maximum_reduced_shear_difference"] for row in rows) < 1e-14
    assert rows[0]["mean_kappa_after"] != rows[-1]["mean_kappa_after"]
