# Local FITS upload contract

The Observatory can audit user-supplied scientific products without sending them to a server. This is an analysis of an existing lensing mass reconstruction—not a method for extracting dark matter from an optical image.

## Required pair

### 1. Luminous-image FITS

- one 2D `IMAGE` HDU;
- calibrated intensity or surface-brightness pixels are preferred;
- readable `BITPIX` of `8`, `16`, `32`, `64`, `-32`, or `-64`;
- celestial WCS is strongly recommended; and
- the image is treated as a morphology proxy, not a stellar-mass map.

The browser subtracts the 20th-percentile background, clips negative residuals, applies an `asinh` display compression, and performs one-pixel smoothing on the browser grid.

### 2. Lensing convergence FITS

- a 2D convergence (`κ`) map; or
- a 3D cube with FITS axes corresponding to `[model, y, x]` after decoding (`NAXIS1=x`, `NAXIS2=y`, `NAXIS3=model`).

For cubes with more than 24 planes, the browser selects 24 evenly spaced planes and records their zero-based indices. Use the Python package for a full posterior or model ensemble.

## Registration gate

Source `NAXIS1` and `NAXIS2` must match exactly. The browser never resizes one source product to make it fit another.

When both HDUs contain celestial WCS, LensAudit compares:

- `CTYPE1/2`;
- `CRPIX1/2`;
- `CRVAL1/2`; and
- available `CDELT`, `CD`, or `PC` scale/rotation terms.

A detected difference stops analysis and directs the user to the Python reprojection workflow. If dimensions match but WCS is incomplete, analysis may proceed only as an explicitly **unverified pixel-grid audit**. No angular or physical offset is reported.

## Browser derivative

The evidence plane is at most 128 × 128 cells. Every non-overlapping output bin uses:

- an exact finite-pixel mean when the source bin contains at most 64 pixels; or
- a deterministic stratified mean using at most 64 samples for larger source bins.

This bounded algorithm keeps large FITS products responsive and repeatable. It does not preserve the angular resolution needed for publication-grade measurement.

## Provenance and privacy

Each completed run exports a receipt containing:

- filenames and byte counts;
- selected HDU number, name, `BITPIX`, dimensions, `BUNIT`, and `CTYPE`;
- SHA-256 of both complete files;
- WCS compatibility status;
- browser target grid and aggregation method; and
- selected κ-ensemble plane indices.

File contents remain in the browser tab. The static site has no upload API, database, account, analytics SDK, or telemetry endpoint. Reloading or closing the tab discards the in-memory files.

## Unsupported inputs

- JPG, PNG, screenshots, and ordinary photographs;
- compressed `.fits.gz` payloads (decompress before selection);
- tables or catalogues without an image HDU;
- 4D+ data products;
- a light image without a κ product;
- source grids with different dimensions or conflicting WCS; and
- individual files larger than 512 MiB.

Use `lensaudit analyze` and astronomy-aware preprocessing for larger products, reprojection, masks, detailed posterior ensembles, or publication workflows.
