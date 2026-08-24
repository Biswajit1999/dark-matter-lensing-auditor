# Observatory experiment contract

## Why there are two modes

The central epistemic error in many visual dark-matter demos is a silent transition from *known synthetic truth* to *unknown observational truth*. LensAudit makes that boundary a top-level control.

### Injection–recovery

The browser creates one luminous morphology and an offset two-halo projected mass field. It then produces two interleaved reconstruction ensembles:

- a smoother **parametric-prior** family with compact extra structure; and
- a less-smoothed **adaptive-grid-prior** family with different centroid bias and substructure.

These are deliberately stylized forward products. They are not claimed to reproduce LENSTOOL, GRALE, GLAFIC, WSLAP+, or any other solver. Their purpose is to expose a research habit: a recovered offset is meaningful only after the estimator is challenged under a known injection and materially different assumptions.

For a seeded experiment, the application records:

- injected halo–light separation;
- recovered mean-map separation;
- 16th–84th percentile separation across realizations;
- recovery bias;
- centroid disagreement between reconstruction families;
- median fractional ensemble scatter; and
- area whose positive residual exceeds the conservative audit threshold.

### Observation

The Abell 2744 browser product contains:

- the official HST ACS/WFC F814W mosaic, reprojected onto the lens-model WCS;
- the official corrected Sharon/Johnson `v4cor` convergence map; and
- the reprojection footprint.

The site bundles an area-aggregated 128 × 128 derivative, not the original FITS products. Every JSON derivative records both source filenames and their SHA-256 hashes. It retains dimensionless convergence cell means but compresses the light proxy for display. Full-resolution measurement belongs in the Python workflow.

### Local FITS upload

The third interface accepts a 2D luminous-image FITS and an independently reconstructed 2D κ map or 3D κ ensemble. It inspects compatible image HDUs, enforces identical source dimensions, compares available celestial-WCS terms, computes complete-file SHA-256 receipts, and runs the same morphology audit locally. Image-only analysis cannot enable the evidence plane.

See the [local upload contract](UPLOAD_FITS.md) for supported `BITPIX` values, WCS tolerances, bounded browser aggregation, privacy, and failure behavior.

## Browser equations

Each light and mass morphology is robustly mapped between its first and 99th percentiles. With normalized light `L`, normalized ensemble mean mass `K`, and normalized ensemble scatter `S`:

```text
α = Σ(LK) / Σ(L²)
R = K − αL
D = R / √(S² + floor²)
floor = max(0.05, median(S))
```

`D` is a discrepancy diagnostic. It is not Gaussian significance because the denominator does not contain the complete lens-model, image, source-redshift, line-of-sight, masking, PSF, or calibration covariance.

## Rebuilding the HFF web derivative

After running the verified HFF fetch and preparation commands:

```bash
python scripts/build_web_dataset.py \
  --image data/hff/prepared/abell2744-f814w-on-sharon-v4cor-grid.fits \
  --kappa data/hff/abell2744-sharon-v4cor/hlsp_frontier_model_abell2744_sharon_v4cor_kappa.fits \
  --footprint data/hff/prepared/abell2744-f814w-reprojection-footprint.fits \
  --receipt data/hff/abell2744-sharon-v4cor/provenance.json \
  --output web/public/data/abell2744-sharon-v4cor.json \
  --size 128
```

The generated JSON is small enough for static hosting, while the large third-party FITS assets stay out of Git.

## Validity boundary

Neither mode detects a dark-matter particle. Observation mode audits a projected mass model against a one-band luminous morphology proxy. A publishable astrophysical offset requires independent lens teams or posterior samples, constrained-region masks, PSF and background treatment, cluster-member or stellar-mass modeling, source-redshift and cosmology consistency, line-of-sight treatment, null tests, and expert review.
