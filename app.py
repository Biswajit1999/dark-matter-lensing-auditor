"""Map-centric evidence console for FITS-based mass–light auditing."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from astropy.io import fits

from lensaudit import HFF_DATASETS, audit_mass_light, get_hff_dataset, make_synthetic_cluster, read_fits, read_fits_bytes
from lensaudit.plotting import make_audit_figure


st.set_page_config(page_title="LensAudit · Mass is inferred, not photographed", page_icon="◌", layout="wide")
st.markdown(
    """
    <style>
    :root{--void:#070a0b;--panel:#101516;--chalk:#eef1e8;--ash:#99a3a0;--acid:#b7f36b;--coral:#ff6b50;--rule:#303a38}
    .stApp{background:var(--void);color:var(--chalk)}
    [data-testid="stHeader"]{background:rgba(7,10,11,.88);border-bottom:1px solid var(--rule)}
    [data-testid="stSidebar"]{background:#0c1011;border-right:1px solid var(--rule)}
    h1,h2,h3{font-family:Georgia,serif;letter-spacing:-.035em;color:var(--chalk)}
    p,li,label{color:#c4cbc7}.block-container{max-width:1600px;padding-top:1.5rem}
    .mast{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(260px,.55fr);gap:3rem;padding:3rem 0 4rem;border-bottom:1px solid var(--rule)}
    .eyebrow{font:700 .7rem ui-monospace,monospace;letter-spacing:.16em;color:var(--acid);text-transform:uppercase}
    .mast h1{font-size:clamp(4rem,7vw,7rem);line-height:.82;margin:.8rem 0 1.5rem;max-width:1050px;overflow-wrap:normal;word-break:normal}
    .mast h1 i{color:var(--ash);font-weight:400}.thesis{align-self:end;border-top:1px solid var(--chalk);padding-top:1rem;color:#c4cbc7;line-height:1.65}
    .boundary{border:1px solid var(--coral);padding:1rem 1.2rem;color:#ffd1c8;background:#1b100e;margin:1rem 0}
    .dataset-card{display:grid;grid-template-columns:1.1fr 1fr;gap:2rem;background:var(--panel);border:1px solid var(--rule);padding:1.5rem;margin:1rem 0 2rem}
    .dataset-card b{display:block;color:var(--acid);font:700 .72rem ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.8rem}
    .dataset-card p{margin:.35rem 0}.receipt{font:500 .72rem/1.6 ui-monospace,monospace;color:var(--ash);overflow-wrap:anywhere}
    [data-testid="stMetric"]{background:var(--panel);border-top:2px solid var(--acid);padding:1rem}
    [data-testid="stMetricValue"]{font-family:Georgia,serif}.stTabs [data-baseweb="tab-list"]{gap:1rem;border-bottom:1px solid var(--rule)}
    .stTabs [data-baseweb="tab"]{min-height:48px;font:700 .72rem ui-monospace,monospace;text-transform:uppercase;letter-spacing:.08em}
    button{min-height:44px}:focus-visible{outline:3px solid var(--acid)!important;outline-offset:3px!important}
    code{color:var(--acid)!important}.stAlert{border-radius:0}
    @media(max-width:800px){.mast,.dataset-card{grid-template-columns:1fr}.mast{gap:1rem}.mast h1{font-size:4.5rem}.thesis{align-self:auto}}
    </style>
    <section class="mast">
      <div><div class="eyebrow">Gravitational lensing · public HST products · model disagreement</div><h1>Mass is <i>inferred.</i><br>Never photographed.</h1></div>
      <div class="thesis">A spatial evidence workbench for testing whether luminous structure and independently reconstructed lensing mass agree—and whether the conclusion survives a change of lens model.</div>
    </section>
    """,
    unsafe_allow_html=True,
)

dataset_key = st.selectbox(
    "Official Hubble Frontier Fields target",
    list(HFF_DATASETS),
    format_func=lambda key: f"{HFF_DATASETS[key].cluster} · z={HFF_DATASETS[key].cluster_redshift:.3f} · {HFF_DATASETS[key].release}",
)
dataset = get_hff_dataset(dataset_key)
st.markdown(
    f"""
    <div class="dataset-card">
      <div><b>Curated HFF target contract</b><h2>{dataset.cluster}</h2><p>{dataset.lens_team} · {dataset.lens_method}</p><p>{dataset.release} · cluster z={dataset.cluster_redshift}</p></div>
      <div class="receipt"><strong>OFFICIAL ARCHIVE CONTRACT</strong><br>{dataset.assets[0].description}<br>{dataset.assets[1].description}<br>Combined transfer: {(sum(a.expected_bytes for a in dataset.assets)/1024**2):.1f} MiB<br><br>{dataset.warning}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.caption("LENSAUDIT / EVIDENCE CONTROLS")
    smoothing = st.slider("Light-proxy smoothing · px", 0.0, 8.0, 2.0, 0.5)
    threshold = st.slider("Ensemble discrepancy threshold", 2.0, 6.0, 3.0, 0.25)
    st.divider()
    st.caption("The displayed score is diagnostic, not Gaussian significance. Never convert pixel offsets to kpc before verifying WCS and cosmology.")

real_tab, upload_tab, falsification_tab = st.tabs(["01 · Official HFF", "02 · Your FITS", "03 · Validation lab"])
image = None
kappa = None
image_name = ""
kappa_name = ""

with real_tab:
    st.subheader("Run from source receipts, not screenshots")
    transfer_mib = sum(asset.expected_bytes for asset in dataset.assets) / 1024**2
    st.markdown(f"The app does not hide a {transfer_mib:.0f} MiB network transfer behind a button. Fetch, hash, and align the official products from the CLI; then point this console at the prepared directory.")
    st.code(
        f"lensaudit hff-fetch {dataset.key} --output data/hff\n"
        f"lensaudit hff-prepare data/hff/{dataset.key} --output data/hff/prepared",
        language="bash",
    )
    prepared_root = Path(st.text_input("Prepared data directory", "data/hff/prepared")).expanduser()
    aligned_path = prepared_root / dataset.prepared_light_filename
    kappa_path = prepared_root.parent / dataset.key / dataset.asset("kappa").filename
    st.caption(f"Expected aligned light: {aligned_path} · expected κ: {kappa_path}")
    if st.button("Open verified local products", type="primary"):
        if not aligned_path.exists() or not kappa_path.exists():
            st.error("Prepared products were not found. Run the two provenance-preserving CLI commands above first.")
        else:
            try:
                image, _, image_wcs = read_fits(aligned_path)
                kappa, _, kappa_wcs = read_fits(kappa_path)
                image_name, kappa_name = aligned_path.name, kappa_path.name
                if image_wcs is None or kappa_wcs is None:
                    st.error("A celestial WCS is missing; the official workflow fails closed.")
                    image = kappa = None
            except Exception as error:
                st.error(f"Official products could not be opened: {error}")

with upload_tab:
    st.subheader("Audit your co-registered products")
    left, right = st.columns(2)
    image_upload = left.file_uploader("Science image FITS", type=["fits", "fit", "fts"])
    kappa_upload = right.file_uploader("Convergence κ FITS or ensemble", type=["fits", "fit", "fts"])
    if image_upload and kappa_upload:
        try:
            image, _, image_wcs = read_fits_bytes(image_upload.getvalue())
            kappa, _, kappa_wcs = read_fits_bytes(kappa_upload.getvalue())
            image_name, kappa_name = image_upload.name, kappa_upload.name
            if image_wcs is None or kappa_wcs is None:
                st.warning("At least one celestial WCS is unreadable. Array shape alone does not establish sky alignment.")
        except Exception as error:
            st.error(f"FITS ingestion stopped: {error}")

with falsification_tab:
    st.subheader("Synthetic data belongs in a validation lab")
    st.markdown("This mode tests code behavior against declared truth. It is not the homepage evidence and it cannot support a claim about a real cluster.")
    seed = st.number_input("Declared nuisance seed", 1, 10000, 7)
    if st.button("Run injected-offset recovery"):
        image, kappa = make_synthetic_cluster(seed=int(seed))
        image_name, kappa_name = "synthetic-validation-light.fits", "synthetic-validation-kappa.fits"

if image is not None and kappa is not None:
    try:
        result = audit_mass_light(image, kappa, smoothing_sigma=smoothing, significance_threshold=threshold)
    except Exception as error:
        st.error(f"Audit stopped: {error}")
    else:
        st.divider()
        st.caption("SPATIAL EVIDENCE RECORD")
        st.header("Where mass and light cease to agree")
        metrics = st.columns(4)
        metrics[0].metric("Centroid offset", f"{result.centroid_offset_pixels:.2f} px")
        metrics[1].metric("Model spread", f"{100 * result.model_fractional_spread:.1f}%")
        metrics[2].metric(f"Area above {threshold:g}", f"{100 * result.robust_excess_area_fraction:.2f}%")
        metrics[3].metric("Lens realizations", np.asarray(kappa).shape[0] if np.asarray(kappa).ndim == 3 else 1)
        figure = make_audit_figure(result)
        st.pyplot(figure, width="stretch")
        plt.close(figure)

        st.markdown('<div class="boundary"><strong>Validity boundary.</strong> Contours trace the supplied lensing convergence model. Residuals locate morphology disagreement after normalization. Neither is a particle-physics dark-matter detection, a calibrated mass-to-light ratio, or immunity from the mass-sheet degeneracy.</div>', unsafe_allow_html=True)
        warning_col, test_col = st.columns([1, 1])
        with warning_col:
            st.subheader("Machine warnings")
            for warning in result.warnings:
                st.warning(warning)
        with test_col:
            st.subheader("What could falsify this map")
            st.markdown("- A different modeling team moves the κ peak.\n- PSF matching or member subtraction removes the residual.\n- The feature lies outside the multiply-imaged constraint region.\n- Reprojection changes the centroid offset.\n- A stellar-mass proxy disagrees with raw F814W light.")

        summary = json.dumps({"inputs": {"image": image_name, "kappa": kappa_name}, "parameters": {"smoothing_sigma_pixels": smoothing, "score_threshold": threshold}, "result": result.summary(), "warnings": result.warnings}, indent=2)
        score_buffer = BytesIO()
        fits.writeto(score_buffer, result.discrepancy_score, overwrite=True)
        first, second = st.columns(2)
        first.download_button("Export evidence receipt · JSON", summary, "lensing-audit.json", "application/json", width="stretch")
        second.download_button("Export discrepancy map · FITS", score_buffer.getvalue(), "discrepancy-score.fits", "application/fits", width="stretch")

st.divider()
st.caption("DATA LINEAGE · STScI HFF archive → immutable source URLs → local SHA-256 receipt → explicit WCS reprojection → mass/light audit → falsification checklist")
