# Abell 2744 Merten v1 observational-product validation

This validation uses official [MAST Hubble Frontier Fields lensing
products](https://archive.stsci.edu/prepds/frontier/lensmodels/) from the
Merten v1 SaWLens reconstruction of Abell 2744. The archive documentation
identifies this as a non-parametric strong+weak-lensing model incorporating
Subaru, VLT and HST/ACS shear catalogues. The inputs include 16,121 Subaru,
912 VLT and 1,205 HST/ACS selected background sources; those source catalogues
are not redistributed or reprocessed here.

The runner downloads the published `kappa`, `gamma`, `gamma1`, `gamma2`, and
source-redshift-nine magnification FITS maps, checks their byte counts and FITS
structure, and records retrieval time and SHA-256 hashes locally. Raw products
remain git-ignored; exact URLs and receipts are embedded in the tracked JSON
result.

Three internal product checks are performed:

1. Shear-component identity:
   `gamma = sqrt(gamma1**2 + gamma2**2)`.
2. Magnification closure away from extreme critical-curve pixels:
   `mu = 1 / abs((1 - kappa)**2 - gamma**2)`, evaluated where published
   absolute magnification is below 100.
3. A Kaiser–Squires reconstruction of `kappa` from the published gridded shear.
   Because the FFT reconstruction has an unknown mean/mass sheet and finite
   boundaries, a slope and intercept are fitted before reporting correlation
   and normalized RMSE. Repeating the comparison after excluding progressively
   larger edge margins exposes boundary sensitivity rather than hiding it.

   Because this is a two-dimensional map comparison, the same sweep also
   reports `scikit-image` structural similarity (SSIM) after the affine fit.
   SSIM complements rather than replaces correlation and RMSE. The
   SciencePlots figure is published as both PNG and vector PDF.

Run:

```bash
python scripts/validate_merten_products.py
```

## Claim boundary

These maps are observationally constrained model products, not direct images
of dark matter. This work validates consistency among the published maps; it
does not rerun the source-shape measurement, SaWLens inference, redshift
calibration, selection corrections, or bootstrap reconstruction. Agreement
between maps produced by one pipeline is not independent evidence for the
cluster mass distribution.

