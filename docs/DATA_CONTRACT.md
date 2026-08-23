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

Store a JSON or YAML file containing archive URLs, checksums, observation IDs, filters, model team/version, source redshift, cosmology, preprocessing commands, and citations. A future release will formalize this manifest.
