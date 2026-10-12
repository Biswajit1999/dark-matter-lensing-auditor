# Synthetic weak-lensing validation

This extension validates three numerical and statistical limits with known
synthetic truth. It does not analyse an HFF observation, infer a physical
cluster mass, or resolve lensing degeneracies.

## Kaiser–Squires resolution convergence

An analytic Gaussian convergence field is mapped to shear with the discrete
Fourier forward operator and reconstructed with the existing Kaiser–Squires
inverse. Because the zero Fourier mode is not observable, validation compares
the mean-subtracted field. The recovered aperture integral is compared with
the continuous Gaussian integral on grids from 32 to 256 pixels per side;
the B-mode RMS is retained as a numerical null.

## Shape-noise sensitivity

Synthetic sources are uniform in area between 0.2 and 2.0 arcmin. Their known
tangential shear is

`gamma_t(r) = 0.08 / [1 + (r / 0.7 arcmin)^2]`.

Independent intrinsic tangential ellipticity noise with standard deviation
0.28 is added at source densities from 10 to 80 arcmin^-2. Fixed radial-bin
means report profile RMSE and nominal 95% normal-interval coverage over 160
replicates. This is an estimator test, not a mass posterior or a survey forecast.

## Mass-sheet degeneracy

The transformation

`kappa' = lambda kappa + (1-lambda)`, `gamma' = lambda gamma`

changes the convergence normalization while leaving reduced shear
`g = gamma/(1-kappa)` invariant. The sweep records both the changed mean kappa
and the numerical reduced-shear difference. This is a regression test for a
fundamental non-identifiability, not a correction for it.

## Reproduce

```bash
python scripts/run_weak_lensing_validation.py
pytest -q tests/test_weak_lensing_validation.py
```

CSV/JSON evidence is stored in `research/`; the labelled figure is
`docs/assets/weak-lensing-validation.png`.
