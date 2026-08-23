"""FITS ingestion with explicit HDU and dimensionality checks."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS


def _extract(hdul: fits.HDUList, hdu: int | str = 0) -> tuple[np.ndarray, fits.Header, WCS | None]:
    unit = hdul[hdu]
    if unit.data is None:
        raise ValueError(f"HDU {hdu!r} contains no image data.")
    data = np.asarray(unit.data, dtype=float)
    data = np.squeeze(data)
    if data.ndim not in (2, 3):
        raise ValueError(f"Expected a 2D image or 3D ensemble, received {data.shape}.")
    header = unit.header.copy()
    try:
        wcs = WCS(header).celestial if header.get("CTYPE1") and header.get("CTYPE2") else None
    except Exception:
        wcs = None
    return data, header, wcs


def read_fits(path: str | Path, hdu: int | str = 0) -> tuple[np.ndarray, fits.Header, WCS | None]:
    """Read a FITS image from disk without mutating its contents."""

    with fits.open(Path(path), memmap=False) as hdul:
        return _extract(hdul, hdu)


def read_fits_bytes(payload: bytes, hdu: int | str = 0) -> tuple[np.ndarray, fits.Header, WCS | None]:
    """Read an uploaded FITS payload."""

    with fits.open(BytesIO(payload), memmap=False) as hdul:
        return _extract(hdul, hdu)
