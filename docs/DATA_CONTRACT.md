# FITS data contract

## Intensity image

- 2D primary HDU by default.
- Finite values over the analyzed region.
- Background, PSF, masks, and photometric meaning documented externally.
- Celestial WCS strongly recommended.

## Convergence

- 2D `κ[y, x]`, or 3D `κ[model, y, x]`.
- Same array shape, orientation, and sky grid as the intensity image.
- Source-redshift normalization recorded.
- Modeling team, version, constraints, and validity region recorded.
- Samples must be identified as posterior realizations or independent models; they are not interchangeable.

## Not accepted silently

- RGB screenshots;
- JPEG/PNG contour figures as mass maps;
- mismatched array shapes;
- table HDUs without image data;
- cubes with unknown axis order;
- physical-offset claims without a pixel scale and cosmology.

## Recommended provenance sidecar

`lensaudit hff-fetch` writes `provenance.json` using schema `lensaudit.hff-receipt/1`. It records archive URLs, expected and actual byte counts, SHA-256 checksums, filter/product roles, lens team and version, model method, cluster redshift, archive/readme routes, retrieval time, and release warnings. Source-redshift normalization remains `null` when it has not been established from the map-maker documentation; the software does not guess it.

`lensaudit hff-prepare` writes a reprojected light image and a footprint map on the unchanged κ WCS. Preserve these beside the receipt and record the package version in downstream analyses.
