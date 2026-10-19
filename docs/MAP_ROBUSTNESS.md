# Merten lensing model-product robustness checks

After downloading official Merten v1 FITS files using the existing archive-fetch script, run `python scripts/run_map_robustness.py PATH_TO_MAP_DIRECTORY`. The module `lensaudit.map_robustness` uses only NumPy, while the runner uses the project's installed Astropy FITS loader. No source-galaxy catalogues are downloaded or refitted.

Three independent diagnostics:

1. **Jacobian parity and critical-curve proximity.** For convergence `kappa` and complex shear `gamma1+i gamma2`, the inverse magnification is `det(A)=(1-kappa)^2-(gamma1^2+gamma2^2)`. The eigenvalues are `1-kappa±|gamma|`. Report negative parity and pixels within a stated dimensionless determinant tolerance; mask those near-critical pixels before computing median absolute magnification. The eigenvalues are principal stretches, not automatically radial/tangential eigenvalues.
2. **Mass-sheet transformation.** Transform `kappa'=lambda*kappa+(1-lambda)` and `gamma'=lambda*gamma` for positive lambda. Check the unchanged reduced shear `g=gamma/(1-kappa)`, preserved parity, and `|mu'|=|mu|/lambda²` away from singular pixels. This explicitly demonstrates that reduced shear alone cannot fix the mass sheet.
3. **Resolution sensitivity.** Block-average kappa and both shear components at several integer scales, then recompute determinant, parity and magnification diagnostics. The nonlinearity means the coarse-map magnification is not the average of the fine-map magnification. Edge pixels not divisible by the block size are omitted and the retained pixel count is reported.

These are tests of published observationally constrained **model products**, not independent detections, new lens masses, redshift calibration, or validation of the source-shape measurement pipeline. Critical-curve and resolution metrics are sensitive to model choice, map grid and masking.
