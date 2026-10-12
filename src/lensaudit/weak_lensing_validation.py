"""Synthetic numerical validation for gridded weak-lensing diagnostics.

The functions in this module use known simulated fields. They validate
numerical behaviour and cannot establish an observational cluster mass.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import erf, pi, sqrt

import numpy as np

from lensaudit.core import kaiser_squires


def shear_from_kappa(kappa: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply the discrete Kaiser--Squires forward operator to an E-mode map."""
    field = np.asarray(kappa, dtype=float)
    if field.ndim != 2 or not np.all(np.isfinite(field)):
        raise ValueError("kappa must be a finite two-dimensional array")
    ny, nx = field.shape
    ky = np.fft.fftfreq(ny)[:, None]
    kx = np.fft.fftfreq(nx)[None, :]
    radius2 = kx**2 + ky**2
    d1 = np.divide(kx**2 - ky**2, radius2, out=np.zeros_like(radius2), where=radius2 > 0)
    d2 = np.divide(2 * kx * ky, radius2, out=np.zeros_like(radius2), where=radius2 > 0)
    kappa_hat = np.fft.fft2(field)
    return np.fft.ifft2(d1 * kappa_hat).real, np.fft.ifft2(d2 * kappa_hat).real


def _analytic_demeaned_gaussian_aperture(
    amplitude: float,
    sigma: float,
    aperture_radius: float,
) -> float:
    gaussian_aperture = 2 * pi * amplitude * sigma**2 * (
        1 - np.exp(-(aperture_radius**2) / (2 * sigma**2))
    )
    square_integral = amplitude * (
        sigma * sqrt(2 * pi) * erf(0.5 / (sqrt(2) * sigma))
    ) ** 2
    return float(gaussian_aperture - square_integral * pi * aperture_radius**2)


def ks_resolution_convergence(
    sizes: Iterable[int] = (32, 48, 64, 96, 128, 192, 256),
    *,
    amplitude: float = 0.4,
    sigma: float = 0.12,
    aperture_radius: float = 0.25,
) -> list[dict[str, float]]:
    """Converge an aperture integral recovered from analytic Gaussian kappa.

    The zero Fourier mode is unrecoverable, so both the analytic and discrete
    aperture masses use the mean-subtracted convergence field.
    """
    analytic = _analytic_demeaned_gaussian_aperture(amplitude, sigma, aperture_radius)
    rows = []
    for size in sizes:
        if size < 16:
            raise ValueError("grid sizes must be at least 16")
        coordinate = (np.arange(size) + 0.5) / size - 0.5
        y, x = np.meshgrid(coordinate, coordinate, indexing="ij")
        radius = np.hypot(x, y)
        kappa = amplitude * np.exp(-(radius**2) / (2 * sigma**2))
        gamma1, gamma2 = shear_from_kappa(kappa)
        recovered, b_mode = kaiser_squires(gamma1, gamma2)
        aperture = radius <= aperture_radius
        recovered_mass = float(np.sum(recovered[aperture]) / size**2)
        rows.append(
            {
                "grid_size": int(size),
                "pixel_scale_domain_units": 1 / size,
                "recovered_demeaned_aperture_mass": recovered_mass,
                "analytic_demeaned_aperture_mass": analytic,
                "relative_error": abs(recovered_mass - analytic) / abs(analytic),
                "b_mode_rms": float(np.sqrt(np.mean(b_mode**2))),
            }
        )
    return rows


def shape_noise_profile_experiment(
    source_densities_arcmin2: Iterable[float] = (10, 20, 40, 80),
    *,
    area_arcmin2: float = 100.0,
    intrinsic_shape_sigma: float = 0.28,
    replicates: int = 160,
    seed: int = 20261012,
) -> list[dict[str, float]]:
    """Recover a synthetic tangential-shear profile under shape noise.

    Sources are uniform in area over 0.2--2.0 arcmin. The injected model is
    ``gamma_t = 0.08 / (1 + (r/0.7 arcmin)^2)``. Reported coverage is for
    normal mean intervals in fixed radial bins, not a cluster-mass posterior.
    """
    if area_arcmin2 <= 0 or intrinsic_shape_sigma <= 0 or replicates < 2:
        raise ValueError("area/noise must be positive and at least two replicates are required")
    edges = np.geomspace(0.2, 2.0, 7)
    rng = np.random.default_rng(seed)
    rows = []
    for density in source_densities_arcmin2:
        count = int(round(float(density) * area_arcmin2))
        if count < 60:
            raise ValueError("each density must provide at least 60 sources")
        squared_radius = rng.uniform(edges[0] ** 2, edges[-1] ** 2, (replicates, count))
        radius = np.sqrt(squared_radius)
        truth = 0.08 / (1 + (radius / 0.7) ** 2)
        measured = truth + rng.normal(0, intrinsic_shape_sigma, truth.shape)
        residuals = []
        covered = []
        usable_bins = 0
        for replicate in range(replicates):
            for low, high in zip(edges[:-1], edges[1:], strict=True):
                selected = (radius[replicate] >= low) & (radius[replicate] < high)
                n_bin = int(selected.sum())
                if n_bin < 8:
                    continue
                values = measured[replicate, selected]
                injected = float(np.mean(truth[replicate, selected]))
                estimate = float(np.mean(values))
                standard_error = float(np.std(values, ddof=1) / np.sqrt(n_bin))
                residuals.append(estimate - injected)
                covered.append(abs(estimate - injected) <= 1.96 * standard_error)
                usable_bins += 1
        rows.append(
            {
                "source_density_arcmin2": float(density),
                "sources": count,
                "replicates": replicates,
                "usable_radial_bins": usable_bins,
                "profile_rmse": float(np.sqrt(np.mean(np.square(residuals)))),
                "nominal_95pct_coverage": float(np.mean(covered)),
            }
        )
    return rows


def mass_sheet_degeneracy_sweep(
    lambdas: Iterable[float] = (0.6, 0.8, 1.0, 1.2, 1.4),
    *,
    size: int = 96,
) -> list[dict[str, float]]:
    """Demonstrate reduced-shear invariance under a mass-sheet transform.

    ``kappa' = lambda*kappa + (1-lambda)`` and ``gamma' = lambda*gamma``
    leave ``g = gamma/(1-kappa)`` invariant wherever the denominator is finite.
    """
    coordinate = (np.arange(size) + 0.5) / size - 0.5
    y, x = np.meshgrid(coordinate, coordinate, indexing="ij")
    kappa = 0.35 * np.exp(-(x**2 + y**2) / (2 * 0.14**2))
    gamma1, gamma2 = shear_from_kappa(kappa)
    reduced1 = gamma1 / (1 - kappa)
    reduced2 = gamma2 / (1 - kappa)
    rows = []
    for value in lambdas:
        if value <= 0:
            raise ValueError("mass-sheet lambda must be positive")
        transformed_kappa = value * kappa + (1 - value)
        transformed1 = value * gamma1 / (1 - transformed_kappa)
        transformed2 = value * gamma2 / (1 - transformed_kappa)
        difference = np.hypot(transformed1 - reduced1, transformed2 - reduced2)
        rows.append(
            {
                "lambda": float(value),
                "mean_kappa_before": float(np.mean(kappa)),
                "mean_kappa_after": float(np.mean(transformed_kappa)),
                "maximum_reduced_shear_difference": float(np.max(difference)),
                "rms_reduced_shear_difference": float(np.sqrt(np.mean(difference**2))),
            }
        )
    return rows
