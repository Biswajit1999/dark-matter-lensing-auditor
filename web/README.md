# LensAudit Observatory

The Observatory is the browser-native instrument inside this repository. It is intentionally separate from the Streamlit/FITS application:

- **Injection–recovery mode** has known synthetic truth and measures estimator bias.
- **Abell 2744 mode** displays a traceable, area-aggregated derivative of verified Hubble Frontier Fields products and has no truth labels.
- **Upload FITS mode** pairs a local 2D luminous image with a local 2D/3D convergence product, validates registration, hashes both inputs, and never transfers them to a server.

All simulation and auditing run locally in the browser. There is no API, account, analytics script, or data upload.

```bash
npm ci
npm test
npm run dev
```

Production:

```bash
npm run build
npm run preview
```

The GitHub Pages base path is configured in `vite.config.ts`. See [`../docs/WEB_LAB.md`](../docs/WEB_LAB.md) for equations and [`../docs/UPLOAD_FITS.md`](../docs/UPLOAD_FITS.md) for the local-file contract.
