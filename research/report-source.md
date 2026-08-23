# Internal research synthesis and claim ledger

## Decision

Build a downstream, uncertainty-first auditor for lensing mass products, not a raw-image dark-matter detector and not another lens inversion framework.

## Primary evidence

1. STScI publishes Hubble Frontier Fields κ, γ, deflection, magnification, and realization products from several teams: https://archive.stsci.edu/prepds/frontier/lensmodels/
2. Schneider establishes aperture mass as a gravitational-lensing method for projected mass concentrations: https://arxiv.org/abs/astro-ph/9601039
3. Meneghetti et al. compare reconstruction methods on controlled synthetic clusters: https://arxiv.org/abs/1606.04548
4. Priewe et al. find model-to-model differences often exceed quoted statistical errors: https://arxiv.org/abs/1605.07621
5. Raney et al. report constrained circular mass profiles but substantial magnification scatter and underestimated systematics: https://arxiv.org/abs/2004.05952
6. Johnson et al. publish HFF products and compare mass to light while documenting modeling caveats: https://arxiv.org/abs/1405.0222
7. STScI's Abell 2744 release page identifies the official HST F814W mosaics: https://archive.stsci.edu/prepds/frontier/abell2744.html
8. STScI records that Sharon v4 products were corrected on 2018-08-24 and that `v4orig` has incorrect scaling: https://archive.stsci.edu/prepds/frontier/lensmodels/

## Claim ledger

| Claim | Support | Confidence | Design response |
|---|---|---:|---|
| lensing, not raw intensity, supplies projected mass evidence | lensing formalism and archive products | high | image-only mode refuses mass inference |
| cross-model systematics matter | Priewe; Raney; Meneghetti | high | prefer ensembles and show warnings |
| public FITS products make reproducible audits possible | STScI HFF archive | high | FITS/WCS input contract |
| an uncertainty-first beginner workflow is underserved | landscape search vs mature solvers | medium | limit novelty claim to workflow integration |
| the selected Abell 2744 files are official archive products | STScI HFF product pages and direct archive headers | high | curate exact HTTPS URLs and expected byte counts |
| Sharon `v4orig` must not be treated as valid | STScI correction notice | high | registry exposes only `v4cor` and tests the safeguard |
| shape equality alone does not establish sky alignment | FITS/WCS data model | high | real-data preparation maps light onto κ WCS and records a footprint |

## Gap matrix

Mature solvers already infer lenses. Archive viewers expose products. General FITS tools plot contours. The chosen opening is a reproducible layer that makes invalid states, ensemble disagreement, centroid sensitivity, source receipts, corrected-release selection, and non-claims unavoidable.
