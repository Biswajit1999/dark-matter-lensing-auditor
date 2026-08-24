# Architecture

```text
Official STScI HFF FITS
        │
        ├── hash + size + FITS validation ── provenance.json
        │
        └── WCS-aware image reprojection
                    │
          full-resolution Python audit
                    │
                    └── explicit area aggregation ── web dataset JSON
                                                        │
Synthetic seeded generator ─────────────────────────────┤
Local FITS pair ── HDU/WCS gate ── SHA-256 ─────────────┤
                                                        ▼
                                            browser audit kernel
                                                        │
                       ┌────────────────┬────────────────┼───────────────┐
                       ▼                ▼                ▼               ▼
                  layered maps   recovery interval  model shift   JSON / CSV
```

## Components

- `src/lensaudit/`: numerical Python package, FITS I/O, HFF registry, WCS preparation, CLI.
- `scripts/build_web_dataset.py`: deterministic bridge from verified local FITS products to the static web derivative.
- `web/src/science/`: framework-independent TypeScript simulation and audit functions.
- `web/src/science/fits.ts`: bounded local FITS/HDU parser, WCS compatibility gate, deterministic spatial aggregation, and provenance hashing.
- `web/src/components/`: accessible evidence controls, canvas renderer, and report surface.
- `web/public/data/`: small reviewable derived data; never a replacement for source FITS.
- `.github/workflows/`: independent Python CI, browser CI, dependency audit, and Pages deployment.

## Failure posture

The Python pipeline fails on mismatched grids, unreadable FITS products, byte-count mismatches, missing WCS for the official preparation route, and invalid dimensionality. Browser upload fails on mismatched dimensions or conflicting WCS and cannot run with only an image. It labels missing WCS and single-model uncertainty rather than inventing registration or an ensemble. Synthetic truth is only available in injection–recovery mode.
