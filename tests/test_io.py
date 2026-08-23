from io import BytesIO

import numpy as np
from astropy.io import fits

from lensaudit.io import read_fits_bytes


def test_reads_uploaded_fits_payload():
    buffer = BytesIO()
    fits.writeto(buffer, np.arange(36).reshape(6, 6), overwrite=True)
    data, header, wcs = read_fits_bytes(buffer.getvalue())
    assert data.shape == (6, 6)
    assert header["NAXIS"] == 2
    assert wcs is None
