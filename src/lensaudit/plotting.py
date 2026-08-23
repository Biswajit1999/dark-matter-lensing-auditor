"""Publication-style diagnostic figure generation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .core import AuditResult


def make_audit_figure(result: AuditResult, output: str | Path | None = None):
    """Render image, mass contours, residual, and discrepancy diagnostics."""

    figure, axes = plt.subplots(2, 2, figsize=(11, 9), constrained_layout=True)
    figure.patch.set_facecolor("#f7f8fb")
    panels = axes.ravel()
    panels[0].imshow(np.arcsinh(result.light_proxy), origin="lower", cmap="gray_r")
    panels[0].set_title("Luminous-matter proxy")
    panels[1].imshow(np.arcsinh(result.light_proxy), origin="lower", cmap="gray_r")
    panels[1].contour(result.mass_mean, levels=result.contour_levels, colors="#0057b8", linewidths=1.2)
    panels[1].scatter(*result.light_centroid_yx[::-1], marker="+", s=100, c="#e76f00", label="light centroid")
    panels[1].scatter(*result.mass_centroid_yx[::-1], marker="x", s=80, c="#0057b8", label="mass centroid")
    panels[1].legend(loc="lower right", fontsize=8)
    panels[1].set_title("Lensing mass contours on light")
    residual_limit = np.nanpercentile(np.abs(result.residual), 99)
    image = panels[2].imshow(result.residual, origin="lower", cmap="coolwarm", vmin=-residual_limit, vmax=residual_limit)
    figure.colorbar(image, ax=panels[2], shrink=0.8, label="normalized mass − fitted light")
    panels[2].set_title("Mass–light morphology residual")
    score_limit = max(3.0, float(np.nanpercentile(np.abs(result.discrepancy_score), 99)))
    image = panels[3].imshow(result.discrepancy_score, origin="lower", cmap="PuOr", vmin=-score_limit, vmax=score_limit)
    panels[3].contour(result.discrepancy_score, levels=[3], colors="black", linewidths=1)
    figure.colorbar(image, ax=panels[3], shrink=0.8, label="discrepancy score (diagnostic)")
    panels[3].set_title("Ensemble-aware discrepancy score")
    for panel in panels:
        panel.set_xlabel("x pixel")
        panel.set_ylabel("y pixel")
    figure.suptitle("Dark Matter Lensing Auditor — evidence map, not direct detection", fontsize=14, weight="bold")
    if output is not None:
        figure.savefig(Path(output), dpi=180, bbox_inches="tight")
    return figure
