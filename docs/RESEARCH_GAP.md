# Research gap: uncertainty-first exploration of public lensing maps

## Problem

Mass contours over a beautiful HST cluster image are visually compelling and easy to misread. The image is a tracer of luminous emission; the contour map is the result of a lens-model inversion. Their overlay is evidence only within a chain of WCS alignment, source-redshift normalization, arc/shear constraints, priors, degeneracies, and model systematics.

The Hubble Frontier Fields created an unusually rich public experiment: several independent teams modeled the same clusters and released mass-related FITS products. Comparisons show that differences between teams can exceed the internal statistical uncertainty of one team, particularly for magnification.

## Existing landscape

| Tool or resource | Strength | Boundary for this project |
|---|---|---|
| lenstronomy / Lenstool / GLAFIC / GRALE / SaWLens | infer lens parameters and mass products | not reimplemented here |
| HFF lens archive | public κ, γ, magnification, deflection, and realizations | used as an external-data route |
| model-comparison literature | quantifies reconstruction fidelity and systematics | motivates ensemble-first metrics |
| image viewers / contour scripts | fast qualitative overlays | often omit model disagreement and invalidity checks |

## Contribution

This repository is a downstream evidence auditor with three differentiators:

1. **Scientific refusal:** image-only mode cannot produce a mass claim.
2. **Ensemble by default:** disagreement is visible in scores, intervals, and warnings.
3. **Reproducible exports:** every diagnostic can be inspected outside the dashboard.

## Falsifiable research questions

1. Which apparent mass–light offsets survive independent reconstruction teams?
2. How much does PSF, background, smoothing, mask, and light-tracer choice move the inferred centroid?
3. Where does between-model variance dominate the claimed residual?
4. Can a blinded synthetic challenge recover injected offsets at a controlled false-positive rate?

## Novelty boundary

The numerical ingredients are established. The novelty claim is the integration of uncertainty, refusal states, and mass–light falsification into an approachable FITS workflow. It should be described as a workflow contribution until a systematic benchmark demonstrates new scientific performance.
