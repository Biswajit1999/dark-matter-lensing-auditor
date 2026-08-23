# Methods and interpretation

## Inputs

The intensity image must be two-dimensional. The convergence input may be a two-dimensional map or a three-dimensional cube ordered as `[model, y, x]`. Both must already share a grid. The software refuses shape mismatches instead of resampling arrays without WCS knowledge.

## Luminous-matter proxy

The 20th intensity percentile is treated as a simple background estimate, negative residuals are clipped, and a Gaussian filter is applied. This produces a morphology proxy—not a stellar-mass map. Dust, populations, intracluster light, cluster-member subtraction, and PSF effects remain potential biases.

## Robust normalization

Each map is scaled between its valid-pixel 1st and 99th percentiles. This allows morphology comparison across unlike units while explicitly giving up absolute mass-to-light calibration.

## Residual

One non-negative least-squares-like scale is fitted between normalized light `L` and ensemble-mean normalized mass `K`:

```text
α = Σ(LK) / Σ(L²)
R = K − αL.
```

## Discrepancy score

The score divides `R` by the quadrature sum of normalized ensemble scatter and a floor of at least 0.05. The floor prevents a single model or tightly clustered internal samples from creating infinite certainty. Because it excludes many observational and modeling errors, the score is a triage statistic, not formal sigma.

## Centroids

Positive normalized weights define mass and light centroids. Repeating the mass centroid over the ensemble produces 16th–84th percentile offset bounds. These bounds include only variation represented in the supplied maps.

## Kaiser–Squires utility

The package includes a compact FFT inversion from gridded `(γ1, γ2)` to E- and B-mode convergence. Masks, boundaries, reduced shear, PSF residuals, redshift weights, and mass-sheet degeneracy require a more complete analysis. The B mode is a null test, not a certificate of correctness.

## Validity envelope

Use results for exploratory auditing, teaching, synthetic challenges, and prioritizing follow-up. Do not publish a physical dark-matter offset from this workflow alone. A science result must add calibrated inputs, independent models, source-redshift and cosmology handling, complete systematics, and domain review.
