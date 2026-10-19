"""Numerical robustness diagnostics for gridded convergence and shear maps.

These operations test properties of *model products*, not source-galaxy
inference, independent cluster masses, or observational likelihoods.
"""
from __future__ import annotations

from collections.abc import Iterable
import numpy as np


def _validate(kappa: np.ndarray, gamma1: np.ndarray, gamma2: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    maps = tuple(np.asarray(x, dtype=float) for x in (kappa, gamma1, gamma2))
    if any(x.ndim != 2 for x in maps) or len({x.shape for x in maps}) != 1:
        raise ValueError("kappa, gamma1 and gamma2 must be matching 2-D arrays")
    if min(maps[0].shape) < 4 or any(not np.all(np.isfinite(x)) for x in maps):
        raise ValueError("maps must be finite and at least 4 by 4 pixels")
    return maps


def lensing_jacobian_diagnostics(
    kappa: np.ndarray, gamma1: np.ndarray, gamma2: np.ndarray, *,
    critical_tolerance: float = 0.05,
) -> dict[str, float | int | None]:
    """Audit determinant, parity, and near-critical fraction of lens Jacobian.

    Eigenvalues `1-kappa±|gamma|` are principal stretches, not necessarily
    physical radial/tangential eigenvalues without orientation information.
    The tolerance is dimensionless in determinant space.
    """
    k, g1, g2 = _validate(kappa, gamma1, gamma2)
    if not np.isfinite(critical_tolerance) or critical_tolerance <= 0:
        raise ValueError("critical_tolerance must be finite and positive")
    shear = np.hypot(g1, g2)
    eigen_min = 1 - k - shear
    eigen_max = 1 - k + shear
    det = eigen_min * eigen_max
    stable = np.abs(det) >= critical_tolerance
    return {
        "pixels": int(k.size),
        "negative_parity_fraction": float(np.mean(det < 0)),
        "near_critical_fraction": float(np.mean(~stable)),
        "minimum_abs_determinant": float(np.min(np.abs(det))),
        "median_abs_magnification_stable": float(np.median(1 / np.abs(det[stable]))) if np.any(stable) else None,
        "min_principal_eigenvalue": float(np.min(eigen_min)),
        "max_principal_eigenvalue": float(np.max(eigen_max)),
    }


def mass_sheet_invariance_audit(
    kappa: np.ndarray, gamma1: np.ndarray, gamma2: np.ndarray,
    lambdas: Iterable[float] = (0.6, 0.8, 1.0, 1.2, 1.4), *,
    min_denominator: float = 1e-6,
) -> list[dict[str, float | int]]:
    """Verify g'=g and mu'=mu/lambda² under the mass-sheet transform.

    Mask near-critical/denominator singularities; parity is unchanged for
    positive lambda. No mass-sheet degeneracy is *broken* by this check.
    """
    k, g1, g2 = _validate(kappa, gamma1, gamma2)
    if not np.isfinite(min_denominator) or min_denominator <= 0:
        raise ValueError("min_denominator must be finite and positive")
    denominator = 1 - k
    determinant = denominator**2 - g1**2 - g2**2
    rows = []
    for lam in lambdas:
        lam = float(lam)
        if not np.isfinite(lam) or lam <= 0:
            raise ValueError("lambda must be finite and positive")
        kt = lam * k + (1 - lam)
        gt1, gt2 = lam * g1, lam * g2
        dt = (1 - kt)**2 - gt1**2 - gt2**2
        valid = (np.abs(denominator) > min_denominator) & (np.abs(1 - kt) > min_denominator) & (np.abs(determinant) > min_denominator) & (np.abs(dt) > min_denominator)
        if not np.any(valid):
            raise ValueError("no noncritical pixels for this lambda")
        reduced_before = (g1[valid] + 1j * g2[valid]) / denominator[valid]
        reduced_after = (gt1[valid] + 1j * gt2[valid]) / (1 - kt[valid])
        mu_before = 1 / np.abs(determinant[valid])
        mu_after = 1 / np.abs(dt[valid])
        rows.append({
            "lambda": lam,
            "valid_pixels": int(valid.sum()),
            "max_reduced_shear_difference": float(np.max(np.abs(reduced_before - reduced_after))),
            "max_relative_magnification_scaling_error": float(np.max(np.abs(mu_after / (mu_before / lam**2) - 1))),
            "parity_changed_pixels": int(np.count_nonzero(np.sign(dt[valid]) != np.sign(determinant[valid]))),
        })
    return rows


def resolution_sensitivity(
    kappa: np.ndarray, gamma1: np.ndarray, gamma2: np.ndarray,
    factors: Iterable[int] = (1, 2, 4, 8), *, critical_tolerance: float = 0.05,
) -> list[dict[str, float | int]]:
    """Test how block averaging model maps changes nonlinear lensing diagnostics.

    Flux-preserving averaging applies to each gridded field separately. The
    derived magnification is recomputed *after* coarsening, not averaged.
    Truncated border pixels are excluded for factors not dividing the shape.
    """
    k, g1, g2 = _validate(kappa, gamma1, gamma2)
    results = []
    for factor in factors:
        if isinstance(factor, (bool, np.bool_)) or not isinstance(factor, (int, np.integer)) or factor < 1:
            raise ValueError("resolution factors must be positive integers")
        ny, nx = k.shape
        cy, cx = ny // factor, nx // factor
        if min(cy, cx) < 4:
            raise ValueError("coarsening would leave fewer than 4 pixels per axis")
        def coarse(x: np.ndarray) -> np.ndarray:
            return x[:cy * factor, :cx * factor].reshape(cy, factor, cx, factor).mean(axis=(1, 3))
        row = lensing_jacobian_diagnostics(coarse(k), coarse(g1), coarse(g2), critical_tolerance=critical_tolerance)
        results.append({
            "block_factor": int(factor),
            "retained_original_pixels": int(cy * cx * factor**2),
            "pixels": int(row["pixels"]),
            "near_critical_fraction": float(row["near_critical_fraction"]),
            "negative_parity_fraction": float(row["negative_parity_fraction"]),
            "median_abs_magnification_stable": row["median_abs_magnification_stable"],
        })
    return results
