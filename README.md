# Dark Matter Lensing Auditor

**An uncertainty-aware FITS workflow for comparing gravitational-lensing mass maps with telescope-image light proxies—without confusing a contour overlay with a dark-matter detection.**

[![CI](https://github.com/Biswajit1999/dark-matter-lensing-auditor/actions/workflows/ci.yml/badge.svg)](https://github.com/Biswajit1999/dark-matter-lensing-auditor/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-174a8b.svg)](LICENSE)
[![Astropy](https://img.shields.io/badge/FITS-Astropy-b85d00.svg)](https://www.astropy.org/)

## The idea, made scientifically defensible

An optical image contains photons from luminous matter. Dark matter does not appear as a dim patch waiting for an image contour. Its projected gravitational influence can be reconstructed from strong- or weak-lensing constraints, producing convergence (`κ`), shear (`γ`), deflection, or magnification products.

This project accepts:

1. a FITS intensity image that acts as a luminous-matter morphology proxy; and
2. a co-registered lensing convergence FITS map—or preferably an ensemble cube from multiple models or posterior realizations.

It then overlays mass contours on light, compares normalized morphologies, propagates ensemble disagreement, measures mass–light centroid offsets, and exports diagnostic maps. Image-only mode is available, but explicitly disables mass inference.

## Research gap

Full lens solvers such as `lenstronomy`, Lenstool, GRALE, GLAFIC, and SaWLens already address the difficult inversion problem. The Hubble Frontier Fields archive publishes lens products from several teams. The gap pursued here is narrower and complementary:

> Make cross-model uncertainty, mass–light mismatch, and invalid-input safeguards the default workflow for people exploring public lensing FITS products.

Published HFF comparisons show that statistical uncertainties from a single model can be smaller than the differences between modeling teams. An attractive single contour map can therefore imply more certainty than the model landscape supports.

## Features

- 2D FITS intensity ingestion with readable-WCS reporting.
- 2D κ map or `[model, y, x]` ensemble-cube ingestion.
- Strict grid checks that stop rather than silently resize mismatched products.
- Robust background subtraction and smoothed light-proxy construction.
- Ensemble mean and scatter maps.
- Fitted normalized mass–light morphology residual.
- Conservative ensemble-aware discrepancy score with a documented systematic floor.
- Mass and light centroids with ensemble offset intervals.
- Percentile κ contours over image morphology.
- Kaiser–Squires E/B reconstruction utility for gridded shear null tests.
- Streamlit research console, Python API, and reproducible CLI.
- JSON, PNG, and FITS outputs.
- Synthetic cluster with an injected offset for test-driven demonstrations.

## Quick start

### Install the package and app

```bash
git clone https://github.com/Biswajit1999/dark-matter-lensing-auditor.git
cd dark-matter-lensing-auditor
python -m pip install -e ".[app,test]"
```

### Launch the research console

```bash
streamlit run app.py
```

The default synthetic example runs without external data.

### Run the reproducible CLI demo

```bash
lensaudit demo --output results/demo --seed 7
```

Outputs:

```text
results/demo/
├── audit.png
├── discrepancy-score.fits
├── kappa-ensemble.fits
├── science-image.fits
└── summary.json
```

### Analyze aligned FITS files

```bash
lensaudit analyze cluster-image.fits kappa-ensemble.fits \
  --output results/cluster \
  --sigma 2.0
```

The CLI intentionally rejects different array shapes. Reproject the products onto one celestial WCS using an astronomy-aware workflow before running the audit.

## Python API

```python
from lensaudit import audit_mass_light, read_fits
from lensaudit.plotting import make_audit_figure

image, image_header, image_wcs = read_fits("cluster-image.fits")
kappa, kappa_header, kappa_wcs = read_fits("kappa-ensemble.fits")

result = audit_mass_light(image, kappa, smoothing_sigma=2.0)
print(result.summary())
make_audit_figure(result, "audit.png")
```

For gridded weak shear:

```python
from lensaudit import kaiser_squires

kappa_e, kappa_b = kaiser_squires(gamma1, gamma2)
```

The B-mode map is a useful null diagnostic, but a small B mode does not prove the E-mode reconstruction is unbiased.

## What the score means

Image intensity and convergence have different physical units. The code therefore robustly normalizes each morphology and fits one scale factor between them. The residual is

```text
R = normalized mean κ − α × normalized light proxy.
```

The displayed discrepancy score divides `R` by the quadrature sum of ensemble scatter and a conservative floor. It is designed to reveal regions worth investigating and models that disagree.

It is **not**:

- a calibrated mass-to-light ratio;
- a Gaussian detection significance;
- a solution to the mass-sheet degeneracy;
- a particle-physics dark-matter detection;
- a replacement for a lens inversion;
- valid when the image and κ map are misregistered.

## Required scientific checks

Before interpreting an offset or excess:

- verify celestial WCS, pixel scale, orientation, and source redshift convention;
- use PSF-matched, background-treated, and consistently masked images;
- compare independent modeling teams as well as posterior samples within one team;
- inspect arc constraints and the region where the lens model is actually constrained;
- test smoothing scale and alternate stellar-mass/light tracers;
- propagate cluster-member subtraction and intracluster-light uncertainty;
- inspect shear B modes, boundaries, masks, and reduced-shear corrections for weak lensing;
- state the cosmology used to convert angular to physical offsets.

## Public data route

The [Hubble Frontier Fields lens-model archive](https://archive.stsci.edu/prepds/frontier/lensmodels/) provides public κ and γ maps, magnification products, deflection maps, and—in several releases—model realizations. The [Frontier Fields data archive](https://archive.stsci.edu/prepds/frontier/) provides co-located HST imaging and catalogs.

Always read the map-maker README, validity region, source-redshift normalization, and requested acknowledgements. This repository does not redistribute those products.

## Evidence base

- [Schneider (1996)](https://arxiv.org/abs/astro-ph/9601039) introduced the aperture-mass framework for detecting projected mass concentrations through weak lensing.
- [Meneghetti et al. (2017)](https://arxiv.org/abs/1606.04548) compared lens-reconstruction methods on controlled synthetic clusters.
- [Priewe et al. (2017)](https://arxiv.org/abs/1605.07621) found that HFF model predictions can differ by more than quoted statistical uncertainties.
- [Raney et al. (2020)](https://arxiv.org/abs/2004.05952) quantified systematic versus statistical differences in HFF masses and magnifications.
- [Johnson et al. (2014)](https://arxiv.org/abs/1405.0222) describe public HFF mass/magnification products and mass–light comparisons.
- [STScI Hubble Frontier Fields lens models](https://archive.stsci.edu/prepds/frontier/lensmodels/) document the public FITS products and their modeling approaches.
- [`lenstronomy`](https://github.com/lenstronomy/lenstronomy) is a mature open-source strong-lensing solver; this project audits downstream products rather than duplicating that solver.

See [Research gap](docs/RESEARCH_GAP.md), [Methods](docs/METHODS.md), and [Data contract](docs/DATA_CONTRACT.md).

## Verification

```bash
pytest
lensaudit demo --output results/smoke-test
```

Tests cover deterministic synthetic generation, finite audit maps, single-model warnings, shape-mismatch rejection, FITS upload ingestion, and zero-shear E/B behavior.

## Roadmap to a research release

- HFF/MAST manifest adapter with checksums and citation metadata.
- WCS-aware reprojection with a recorded target grid.
- Cross-team κ normalization and source-redshift harmonization.
- Stellar-mass rather than raw-light proxy support.
- Mask-aware Kaiser–Squires and aperture-mass significance maps.
- Bootstrap centroid uncertainties including image-background choices.
- Synthetic recovery challenge with blinded truth and preregistered metrics.
- Reproduction notebooks for a Frontier Fields cluster.

## Repository map

```text
app.py                    Streamlit evidence console
src/lensaudit/core.py     mass–light audit and Kaiser–Squires utility
src/lensaudit/io.py       FITS ingestion
src/lensaudit/plotting.py publication-style evidence figure
src/lensaudit/cli.py      reproducible batch workflow
tests/                    physics and data-contract safeguards
docs/                     assumptions, gap, and input contract
```

## Citation and contribution

Use [CITATION.cff](CITATION.cff) for the software and separately cite the lens-model products and scientific method used. Contributions should include a validity statement, a synthetic recovery test, and an example that fails safely.

## License

MIT. Telescope data and third-party lens models retain their own terms, attribution, and publication requirements.
