import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowSquareOut, Atom, Flask, GithubLogo, Planet, SpinnerGap } from "@phosphor-icons/react";
import { LayerControl, SimulationControls } from "./components/Controls";
import { EvidencePanel } from "./components/EvidencePanel";
import { MapCanvas, type Layer } from "./components/MapCanvas";
import { auditHffDataset, loadHffDataset } from "./science/observation";
import { DEFAULT_PARAMETERS, simulateExperiment } from "./science/simulation";
import type { HffWebDataset, SimulationParameters } from "./science/types";

type Mode = "simulation" | "observation";

export default function App() {
  const initialMode = new URLSearchParams(window.location.search).get("mode") === "observation" ? "observation" : "simulation";
  const [mode, setMode] = useState<Mode>(initialMode);
  const [params, setParams] = useState<SimulationParameters>(DEFAULT_PARAMETERS);
  const [layer, setLayer] = useState<Layer>("composite");
  const [showTruth, setShowTruth] = useState(false);
  const [dataset, setDataset] = useState<HffWebDataset>();
  const [loadError, setLoadError] = useState<string>();
  const simulation = useMemo(() => simulateExperiment(params), [params]);
  const observation = useMemo(() => dataset ? auditHffDataset(dataset) : null, [dataset]);

  useEffect(() => {
    loadHffDataset().then(setDataset).catch((error: Error) => setLoadError(error.message));
  }, []);

  const product = mode === "simulation" ? simulation : observation;
  const truthPoint = mode === "simulation" ? { x: simulation.lightCentroid.x + params.offsetX, y: simulation.lightCentroid.y + params.offsetY } : undefined;
  const changeMode = (next: Mode) => {
    setMode(next);
    setShowTruth(false);
    const url = new URL(window.location.href);
    if (next === "observation") url.searchParams.set("mode", "observation");
    else url.searchParams.delete("mode");
    window.history.replaceState({}, "", url);
  };
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="LensAudit Observatory home"><span>LA</span><div><strong>LensAudit</strong><small>Observatory / v1.0</small></div></a>
        <div className="topbar__status"><i />Browser compute · deterministic seed · no telemetry</div>
        <nav aria-label="Project links">
          <a href="https://archive.stsci.edu/prepds/frontier/lensmodels/" target="_blank" rel="noreferrer"><Planet aria-hidden="true" />HFF archive</a>
          <a href="https://github.com/Biswajit1999/dark-matter-lensing-auditor" target="_blank" rel="noreferrer"><GithubLogo aria-hidden="true" />Source</a>
        </nav>
      </header>

      <section className="research-banner" id="top">
        <div><span className="overline">PROJECTED MASS / MODEL AUDIT / INJECTION–RECOVERY</span><h1>Where does the mass appear <em>after the assumptions change?</em></h1></div>
        <p>Dark matter is not detected from an image contour. This instrument compares a luminous morphology proxy with lensing-derived convergence and makes reconstruction fragility visible.</p>
      </section>

      <div className="mode-bar">
        <div className="mode-switch" role="group" aria-label="Experiment mode">
          <button className={mode === "simulation" ? "active" : ""} type="button" aria-pressed={mode === "simulation"} onClick={() => changeMode("simulation")}><Flask aria-hidden="true" /><span><strong>Injection–recovery</strong><small>Known synthetic truth</small></span></button>
          <button className={mode === "observation" ? "active" : ""} type="button" aria-pressed={mode === "observation"} onClick={() => changeMode("observation")}><Planet aria-hidden="true" /><span><strong>Abell 2744</strong><small>Public HFF derivative</small></span></button>
        </div>
        <div className={`mode-boundary mode-boundary--${mode}`}><Atom aria-hidden="true" /><span>{mode === "simulation" ? "Truth is known by construction. Test estimator bias here." : "Truth is unknown. Audit one model product; do not claim detection."}</span></div>
      </div>

      <main id="main-workbench" className={`workbench workbench--${mode}`}>
        {mode === "simulation" ? (
          <SimulationControls params={params} setParams={setParams} layer={layer} setLayer={setLayer} />
        ) : (
          <aside className="control-panel observation-panel" aria-labelledby="dataset-heading">
            <div className="panel-heading"><Planet aria-hidden="true" /><div><span className="overline">OBSERVATIONAL PRODUCT</span><h2 id="dataset-heading">Abell 2744</h2></div></div>
            {dataset ? <>
              <dl className="dataset-facts">
                <div><dt>Cluster redshift</dt><dd>{dataset.provenance.clusterRedshift}</dd></div>
                <div><dt>Lens reconstruction</dt><dd>{dataset.provenance.lensTeam}</dd></div>
                <div><dt>Release</dt><dd>{dataset.provenance.release}</dd></div>
                <div><dt>Web derivative</dt><dd>{dataset.width} × {dataset.height} cells</dd></div>
              </dl>
              <p className="panel-intro">F814W light reprojected onto the corrected Sharon v4 convergence grid, then robustly aggregated for browser inspection. Full-resolution FITS analysis remains in the Python pipeline.</p>
              <details className="receipt"><summary>Provenance receipt</summary>{dataset.provenance.sourceAssets.map((asset) => <p key={asset.role}><strong>{asset.role}</strong><span>{asset.filename}</span><code>{asset.sha256}</code></p>)}</details>
              <a className="archive-link" href={dataset.provenance.sourceArchive} target="_blank" rel="noreferrer">Open authoritative archive <ArrowSquareOut aria-hidden="true" /></a>
            </> : loadError ? <div className="load-error" role="alert"><strong>Dataset unavailable</strong><span>{loadError}</span><button type="button" onClick={() => location.reload()}>Retry</button></div> : <div className="loading-state"><SpinnerGap aria-hidden="true" /><span>Loading verified derivative…</span></div>}
            <LayerControl layer={layer} setLayer={setLayer} />
          </aside>
        )}

        <AnimatePresence mode="wait">
          {product ? (
            <motion.div className="map-column" key={mode} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.24 }}>
              <MapCanvas product={product} layer={layer} showTruth={showTruth} truthPoint={truthPoint} onToggleTruth={() => setShowTruth((value) => !value)} />
            </motion.div>
          ) : <div className="map-skeleton" aria-label="Loading map" />}
        </AnimatePresence>
        {product ? <EvidencePanel product={product} params={mode === "simulation" ? params : undefined} dataset={dataset} /> : <aside className="evidence-panel evidence-panel--loading" />}
      </main>

      <section className="method-strip" aria-labelledby="method-title">
        <span className="overline">FALSIFIABILITY BEFORE AESTHETICS</span>
        <h2 id="method-title">One interface. Two epistemic regimes.</h2>
        <div className="method-grid">
          <article><span>01</span><h3>Inject</h3><p>Choose a known halo–light displacement and reconstruction noise. The seed makes every experiment repeatable.</p></article>
          <article><span>02</span><h3>Reconstruct</h3><p>Compare parametric-prior and adaptive-grid-prior toy ensembles. Their disagreement is reported, not averaged away.</p></article>
          <article><span>03</span><h3>Audit</h3><p>Fit normalized morphology, propagate model scatter, recover centroids, and measure bias against hidden truth.</p></article>
          <article><span>04</span><h3>Escalate</h3><p>Move to full-resolution FITS, WCS validation, multi-team products, null tests, and peer-reviewed lens solvers before inference.</p></article>
        </div>
      </section>

      <footer><p>Built as an open research instrument by Biswajit Jana.</p><p>MIT code · third-party HFF data remain under archive terms · <a href="https://github.com/Biswajit1999/dark-matter-lensing-auditor/blob/main/CITATION.cff">Cite this project</a></p></footer>
    </div>
  );
}
