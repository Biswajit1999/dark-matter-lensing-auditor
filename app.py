"""Streamlit research console for FITS-based mass–light auditing."""

from __future__ import annotations

from io import BytesIO
import json

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from astropy.io import fits

from lensaudit import audit_mass_light, make_synthetic_cluster, read_fits_bytes
from lensaudit.plotting import make_audit_figure


st.set_page_config(page_title="Dark Matter Lensing Auditor", page_icon=None, layout="wide")
st.markdown(
    """
    <style>
    :root { --ink:#14243a; --blue:#174a8b; --amber:#b85d00; }
    .stApp { background: #f6f8fb; color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(246,248,251,.9); }
    h1,h2,h3 { letter-spacing: -.025em; }
    .kicker { color:var(--amber);font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase; }
    .hero { padding:1.2rem 0 1.8rem;border-bottom:1px solid #d8e0ea;margin-bottom:1.5rem; }
    .hero h1 { font-size:clamp(2.5rem,5vw,5rem);line-height:.95;max-width:900px;margin:.35rem 0 1rem; }
    .hero p:last-child { color:#52647b;max-width:820px;font-size:1.05rem;line-height:1.6; }
    .scope { background:#fff7ea;border-left:4px solid #b85d00;padding:1rem 1.2rem;margin:1rem 0; }
    [data-testid="stMetric"] { background:white;border:1px solid #d8e0ea;padding:1rem; }
    button { min-height:44px; }
    :focus-visible { outline:3px solid #b85d00!important;outline-offset:2px!important; }
    </style>
    <div class="hero">
      <div class="kicker">FITS · LENSING ENSEMBLES · MASS / LIGHT NULL TEST</div>
      <h1>Dark Matter Lensing Auditor</h1>
      <p>Overlay gravitational-lensing mass contours on telescope imaging, propagate disagreement across lens models, and locate mass–light discrepancies without pretending that a bright-pixel contour is a dark-matter detection.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Evidence inputs")
    mode = st.radio("Analysis mode", ["Validated synthetic example", "Upload FITS products", "Image morphology only"], help="Mass evidence requires a kappa ensemble or calibrated shear—not only an intensity image.")
    smoothing = st.slider("Light-proxy smoothing (pixels)", 0.0, 8.0, 2.0, 0.5)
    threshold = st.slider("Discrepancy contour threshold", 2.0, 6.0, 3.0, 0.25, help="A diagnostic ensemble score, not formal Gaussian sigma.")
    seed = st.number_input("Synthetic seed", 1, 10000, 7, disabled=mode != "Validated synthetic example")
    st.divider()
    st.caption("Required scientific checks")
    st.checkbox("Image and κ share a WCS/grid", value=mode == "Validated synthetic example")
    st.checkbox("PSF/background treatment documented", value=mode == "Validated synthetic example")
    st.checkbox("Multiple models or posterior samples supplied", value=mode == "Validated synthetic example")

image = None
kappa = None
image_name = "synthetic-light.fits"
kappa_name = "synthetic-kappa-ensemble.fits"

if mode == "Validated synthetic example":
    image, kappa = make_synthetic_cluster(seed=int(seed))
elif mode == "Upload FITS products":
    image_upload = st.file_uploader("Science image FITS", type=["fits", "fit", "fts"], help="A background-treated intensity image on the same pixel/WCS grid as κ.")
    kappa_upload = st.file_uploader("Convergence κ FITS", type=["fits", "fit", "fts"], help="A 2D best map or, preferably, a [model,y,x] ensemble cube.")
    if image_upload and kappa_upload:
        try:
            image, _, image_wcs = read_fits_bytes(image_upload.getvalue())
            kappa, _, kappa_wcs = read_fits_bytes(kappa_upload.getvalue())
            image_name, kappa_name = image_upload.name, kappa_upload.name
            if image_wcs is None or kappa_wcs is None:
                st.warning("One or both headers lack a readable celestial WCS. Grid equality will be checked, but sky alignment cannot be established here.")
        except Exception as error:
            st.error(f"Could not read the FITS inputs: {error}")
elif mode == "Image morphology only":
    image_upload = st.file_uploader("Telescope image (FITS)", type=["fits", "fit", "fts"])
    if image_upload:
        try:
            image, _, _ = read_fits_bytes(image_upload.getvalue())
        except Exception as error:
            st.error(f"Could not read the FITS image: {error}")
    st.markdown('<div class="scope"><strong>No mass inference in this mode.</strong><br>An intensity image traces luminous emission after instrument, distance, stellar-population, dust, and background effects. Upload a lensing κ ensemble to audit projected mass evidence.</div>', unsafe_allow_html=True)

if image is not None and kappa is not None:
    try:
        result = audit_mass_light(image, kappa, smoothing_sigma=smoothing, significance_threshold=threshold)
    except Exception as error:
        st.error(f"Audit stopped: {error}")
    else:
        st.subheader("Evidence dashboard")
        first, second, third, fourth = st.columns(4)
        first.metric("Mass–light centroid offset", f"{result.centroid_offset_pixels:.2f} px", help="Convert with the FITS pixel scale only after confirming WCS and cosmology.")
        second.metric("Model fractional spread", f"{100 * result.model_fractional_spread:.1f}%")
        third.metric(f"Area above score {threshold:g}", f"{100 * result.robust_excess_area_fraction:.2f}%")
        fourth.metric("Lens realizations", f"{np.asarray(kappa).shape[0] if np.asarray(kappa).ndim == 3 else 1}")
        figure = make_audit_figure(result)
        st.pyplot(figure, width="stretch")
        plt.close(figure)

        st.markdown('<div class="scope"><strong>Interpretation boundary.</strong><br>Blue contours trace a supplied gravitational-lensing convergence product. Orange/blue discrepancy regions show where normalized projected mass and image-derived light morphology disagree after a fitted scale. This can motivate a dark-matter analysis; it is not, alone, a particle detection or a calibrated mass-to-light ratio.</div>', unsafe_allow_html=True)

        left, right = st.columns([1, 1])
        with left:
            st.subheader("Audit warnings")
            for warning in result.warnings:
                st.warning(warning)
        with right:
            st.subheader("Falsification checklist")
            st.markdown("""
            - Reproject image and every lens map onto an explicitly verified WCS.
            - Repeat with independent lens-modeling teams, not only samples from one model.
            - Match PSF, masks, and smoothing scales before interpreting offsets.
            - Test alternate light tracers and stellar mass maps.
            - Inspect shear B-modes, edge effects, mass-sheet degeneracy, and redshift calibration.
            - Report physical offsets only after propagating cosmology and pixel-scale uncertainty.
            """)

        summary = json.dumps({"inputs": {"image": image_name, "kappa": kappa_name}, "parameters": {"smoothing_sigma_pixels": smoothing, "score_threshold": threshold}, "result": result.summary(), "warnings": result.warnings}, indent=2)
        score_buffer = BytesIO()
        fits.writeto(score_buffer, result.discrepancy_score, overwrite=True)
        export_left, export_right = st.columns(2)
        export_left.download_button("Download audit JSON", summary, "lensing-audit.json", "application/json", width="stretch")
        export_right.download_button("Download discrepancy FITS", score_buffer.getvalue(), "discrepancy-score.fits", "application/fits", width="stretch")

elif image is not None and mode == "Image morphology only":
    st.subheader("Intensity morphology preview")
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.imshow(np.arcsinh(image), origin="lower", cmap="gray_r")
    axis.set_title("Image only — no gravitational mass information supplied")
    axis.set_xlabel("x pixel")
    axis.set_ylabel("y pixel")
    st.pyplot(figure, width="stretch")
    plt.close(figure)
elif mode == "Upload FITS products":
    st.info("Upload both the science image and a κ map or ensemble cube to begin the audit.")

st.divider()
st.subheader("Why this workflow exists")
st.markdown("""
Hubble Frontier Fields products include public convergence and shear maps from multiple lens-modeling teams, often with ensembles for uncertainty estimation. Comparisons in the literature show that model-to-model systematics can exceed the statistical uncertainties reported by a single team, particularly for magnification. This application makes those caveats part of the interface instead of hiding them behind an attractive contour overlay.

**Next research step:** add an official HFF data adapter, WCS reprojection, stellar-mass maps, cross-team ensemble harmonization, shear E/B null maps, and a preregistered synthetic recovery challenge.
""")
