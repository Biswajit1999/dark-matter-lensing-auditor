"""Numerical methods for uncertainty-aware mass–light comparison.

The functions in this module do not infer dark matter from an intensity image.
They audit lensing-derived projected mass products against an image-derived light
proxy and, when available, compare independent reconstruction realizations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter


Array = np.ndarray


@dataclass(frozen=True)
class AuditResult:
    """Maps and diagnostics produced by :func:`audit_mass_light`."""

    light_proxy: Array
    mass_mean: Array
    mass_std: Array
    mass_normalized: Array
    light_normalized: Array
    residual: Array
    discrepancy_score: Array
    valid_mask: Array
    light_centroid_yx: tuple[float, float]
    mass_centroid_yx: tuple[float, float]
    centroid_offset_pixels: float
    centroid_offset_p16_p84: tuple[float, float]
    model_fractional_spread: float
    robust_excess_area_fraction: float
    contour_levels: tuple[float, ...]
    warnings: tuple[str, ...]

    def summary(self) -> dict[str, float | str | list[float]]:
        """Return JSON-serializable high-level results."""

        return {
            "centroid_offset_pixels": self.centroid_offset_pixels,
            "centroid_offset_p16_p84_pixels": list(self.centroid_offset_p16_p84),
            "model_fractional_spread": self.model_fractional_spread,
            "robust_excess_area_fraction": self.robust_excess_area_fraction,
            "maximum_discrepancy_score": float(np.nanmax(self.discrepancy_score)),
            "minimum_discrepancy_score": float(np.nanmin(self.discrepancy_score)),
            "interpretation": "mass-light discrepancy audit; not a direct dark-matter detection",
        }


def _finite(array: Array) -> Array:
    values = np.asarray(array, dtype=float)
    if values.ndim != 2:
        raise ValueError(f"Expected a 2D image, received shape {values.shape}.")
    if not np.isfinite(values).any():
        raise ValueError("The image contains no finite pixels.")
    fill = float(np.nanmedian(values[np.isfinite(values)]))
    return np.nan_to_num(values, nan=fill, posinf=fill, neginf=fill)


def robust_normalize(array: Array, mask: Array | None = None) -> Array:
    """Scale an image between robust 1st and 99th percentiles."""

    values = _finite(array)
    selected = values[np.asarray(mask, dtype=bool)] if mask is not None else values.ravel()
    low, high = np.percentile(selected, [1, 99])
    if high <= low:
        return np.zeros_like(values)
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def _centroid(weights: Array, mask: Array) -> tuple[float, float]:
    positive = np.where(mask, np.clip(weights, 0, None), 0.0)
    total = float(positive.sum())
    if total <= 0:
        return (float("nan"), float("nan"))
    y, x = np.indices(positive.shape)
    return (float((y * positive).sum() / total), float((x * positive).sum() / total))


def prepare_light_proxy(image: Array, smoothing_sigma: float = 2.0) -> Array:
    """Build a non-negative, background-subtracted luminous-matter proxy."""

    values = _finite(image)
    background = float(np.percentile(values, 20))
    positive = np.clip(values - background, 0, None)
    return gaussian_filter(positive, max(0.0, smoothing_sigma), mode="nearest")


def _as_cube(kappa: Array) -> Array:
    cube = np.asarray(kappa, dtype=float)
    if cube.ndim == 2:
        cube = cube[None, :, :]
    if cube.ndim != 3:
        raise ValueError("Kappa must be a 2D map or a 3D ensemble [model, y, x].")
    if not np.isfinite(cube).any():
        raise ValueError("Kappa contains no finite values.")
    for index in range(cube.shape[0]):
        cube[index] = _finite(cube[index])
    return cube


def audit_mass_light(
    image: Array,
    kappa: Array,
    *,
    smoothing_sigma: float = 2.0,
    significance_threshold: float = 3.0,
    mask: Array | None = None,
) -> AuditResult:
    """Compare an intensity image with one or more lensing convergence maps.

    The comparison is morphology-based because image intensity and convergence
    have different units. A fitted scale maps the normalized light proxy onto
    normalized convergence. Ensemble scatter and a conservative systematic floor
    determine a *discrepancy score*, not a Gaussian detection significance.
    """

    light = prepare_light_proxy(image, smoothing_sigma)
    cube = _as_cube(kappa)
    if cube.shape[1:] != light.shape:
        raise ValueError(
            "Image and kappa grids differ. Reproject them onto one WCS before audit: "
            f"{light.shape} versus {cube.shape[1:]}."
        )
    valid = np.isfinite(image) & np.isfinite(np.nanmean(cube, axis=0))
    if mask is not None:
        supplied = np.asarray(mask, dtype=bool)
        if supplied.shape != light.shape:
            raise ValueError("Mask shape must match the science image.")
        valid &= supplied
    if valid.sum() < 16:
        raise ValueError("Fewer than 16 valid pixels remain after masking.")

    normalized_models = np.stack([robust_normalize(model, valid) for model in cube])
    mass_mean = np.mean(cube, axis=0)
    mass_std = np.std(cube, axis=0, ddof=1) if cube.shape[0] > 1 else np.zeros_like(mass_mean)
    mass_norm = np.mean(normalized_models, axis=0)
    mass_norm_std = np.std(normalized_models, axis=0, ddof=1) if cube.shape[0] > 1 else np.zeros_like(mass_norm)
    light_norm = robust_normalize(light, valid)
    denominator = float(np.sum(light_norm[valid] ** 2))
    scale = float(np.sum(light_norm[valid] * mass_norm[valid]) / max(denominator, 1e-12))
    residual = mass_norm - scale * light_norm

    # Model scatter alone can be spuriously zero for a single reconstruction.
    # The floor prevents this visualization score from masquerading as formal σ.
    systematic_floor = max(0.05, float(np.median(mass_norm_std[valid])))
    discrepancy = residual / np.sqrt(mass_norm_std**2 + systematic_floor**2)
    discrepancy = np.where(valid, discrepancy, np.nan)

    light_centroid = _centroid(light_norm, valid)
    mass_centroid = _centroid(mass_norm, valid)
    offset = float(np.hypot(mass_centroid[0] - light_centroid[0], mass_centroid[1] - light_centroid[1]))
    ensemble_offsets = []
    for model in normalized_models:
        center = _centroid(model, valid)
        ensemble_offsets.append(np.hypot(center[0] - light_centroid[0], center[1] - light_centroid[1]))
    p16, p84 = np.percentile(ensemble_offsets, [16, 84])
    central_mass = np.abs(mass_norm[valid]) > np.percentile(np.abs(mass_norm[valid]), 25)
    fractional_spread = float(np.median(mass_norm_std[valid][central_mass] / np.maximum(np.abs(mass_norm[valid][central_mass]), 0.05)))
    robust_area = float(np.mean(discrepancy[valid] >= significance_threshold))
    contour_levels = tuple(float(value) for value in np.percentile(mass_mean[valid], [60, 75, 87.5, 95]))

    warnings: list[str] = []
    if cube.shape[0] == 1:
        warnings.append("Only one lens model was supplied; systematic disagreement is not measured.")
    if cube.shape[0] < 5:
        warnings.append("Use multiple teams or posterior realizations before treating contours as robust.")
    if robust_area > 0.25:
        warnings.append("A large discrepancy area can indicate WCS, PSF, masking, or background mismatch.")
    warnings.append("Discrepancy score is a model-audit diagnostic, not a formal dark-matter detection significance.")

    return AuditResult(
        light_proxy=light,
        mass_mean=mass_mean,
        mass_std=mass_std,
        mass_normalized=mass_norm,
        light_normalized=light_norm,
        residual=residual,
        discrepancy_score=discrepancy,
        valid_mask=valid,
        light_centroid_yx=light_centroid,
        mass_centroid_yx=mass_centroid,
        centroid_offset_pixels=offset,
        centroid_offset_p16_p84=(float(p16), float(p84)),
        model_fractional_spread=fractional_spread,
        robust_excess_area_fraction=robust_area,
        contour_levels=contour_levels,
        warnings=tuple(warnings),
    )


def kaiser_squires(gamma1: Array, gamma2: Array) -> tuple[Array, Array]:
    """Recover E/B convergence maps from gridded shear via Kaiser–Squires FFT.

    Edge effects, masks, reduced-shear corrections, source-redshift calibration,
    and PSF systematics are outside this compact implementation. The B map is a
    useful null diagnostic but is not proof that the E map is unbiased.
    """

    g1, g2 = _finite(gamma1), _finite(gamma2)
    if g1.shape != g2.shape:
        raise ValueError("gamma1 and gamma2 must have the same grid.")
    ny, nx = g1.shape
    ky = np.fft.fftfreq(ny)[:, None]
    kx = np.fft.fftfreq(nx)[None, :]
    radius2 = kx**2 + ky**2
    d1 = np.divide(kx**2 - ky**2, radius2, out=np.zeros_like(radius2), where=radius2 > 0)
    d2 = np.divide(2 * kx * ky, radius2, out=np.zeros_like(radius2), where=radius2 > 0)
    g1_hat, g2_hat = np.fft.fft2(g1), np.fft.fft2(g2)
    e_hat = d1 * g1_hat + d2 * g2_hat
    b_hat = -d2 * g1_hat + d1 * g2_hat
    return np.fft.ifft2(e_hat).real, np.fft.ifft2(b_hat).real


def make_synthetic_cluster(size: int = 192, models: int = 24, seed: int = 7) -> tuple[Array, Array]:
    """Create a documented toy cluster with an offset mass component."""

    if size < 32 or models < 1:
        raise ValueError("Use size >= 32 and at least one model.")
    rng = np.random.default_rng(seed)
    y, x = np.indices((size, size))

    def gaussian(cx: float, cy: float, sx: float, sy: float) -> Array:
        return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))

    light = 1.0 * gaussian(size * 0.47, size * 0.52, size * 0.11, size * 0.09)
    light += 0.36 * gaussian(size * 0.68, size * 0.41, size * 0.06, size * 0.05)
    light += rng.normal(0, 0.018, light.shape)
    mass_models = []
    for _ in range(models):
        dx, dy = rng.normal(0, 1.7, 2)
        mass = 0.82 * gaussian(size * 0.51 + dx, size * 0.49 + dy, size * 0.16, size * 0.14)
        mass += 0.31 * gaussian(size * 0.72 + dx, size * 0.39 + dy, size * 0.08, size * 0.08)
        mass += gaussian_filter(rng.normal(0, 0.025, light.shape), 4)
        mass_models.append(mass)
    return light, np.stack(mass_models)
