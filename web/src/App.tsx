import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowSquareOut, Atom, FileArrowUp, Flask, GithubLogo, Planet, SpinnerGap } from "@phosphor-icons/react";
import { LayerControl, SimulationControls } from "./components/Controls";
import { EvidencePanel } from "./components/EvidencePanel";
import { MapCanvas, type Layer } from "./components/MapCanvas";
import { FitsUploadPanel } from "./components/FitsUploadPanel";
import { auditHffDataset, loadHffCatalog, loadHffDataset } from "./science/observation";
import { DEFAULT_PARAMETERS, simulateExperiment } from "./science/simulation";
import type { HffCatalogEntry, HffWebDataset, SimulationParameters } from "./science/types";
import type { UploadedAudit } from "./science/fits";

type Mode = "simulation" | "observation" | "upload";
const DEFAULT_TARGET = "abell2744-sharon-v4cor";

export default function App() {
  const requestedMode = new URLSearchParams(window.location.search).get("mode");
  const initialMode: Mode = requestedMode === "observation" || requestedMode === "upload" ? requestedMode : "simulation";
  const [mode, setMode] = useState<Mode>(initialMode);
  const [params, setParams] = useState<SimulationParameters>(DEFAULT_PARAMETERS);
  const [layer, setLayer] = useState<Layer>("composite");
  const [showTruth, setShowTruth] = useState(false);
  const [targets, setTargets] = useState<HffCatalogEntry[]>([]);
  const requestedTarget = new URLSearchParams(window.location.search).get("target");
  const [selectedTarget, setSelectedTarget] = useState(requestedTarget ?? DEFAULT_TARGET);
  const [dataset, setDataset] = useState<HffWebDataset>();
  const [loadError, setLoadError] = useState<string>();
  const [uploadedAudit, setUploadedAudit] = useState<UploadedAudit>();
  const simulation = useMemo(() => simulateExperiment(params), [params]);
  const observation = useMemo(() => dataset ? auditHffDataset(dataset) : null, [dataset]);

  useEffect(() => {
    loadHffCatalog().then((catalog) => {
      setTargets(catalog.targets);
      if (!catalog.targets.some((target) => target.id === selectedTarget)) setSelectedTarget(DEFAULT_TARGET);
    }).catch((error: Error) => setLoadError(error.message));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setDataset(undefined);
    setLoadError(undefined);
    loadHffDataset(selectedTarget).then((next) => { if (!cancelled) setDataset(next); }).catch((error: Error) => { if (!cancelled) setLoadError(error.message); });
    return () => { cancelled = true; };
  }, [selectedTarget]);

  const product = mode === "simulation" ? simulation : mode === "observation" ? observation : uploadedAudit?.product ?? null;
  const truthPoint = mode === "simulation" ? { x: simulation.lightCentroid.x + params.offsetX, y: simulation.lightCentroid.y + params.offsetY } : undefined;
  const changeMode = (next: Mode) => {
    setMode(next);
    setShowTruth(false);
    const url = new URL(window.location.href);
    if (next === "observation" || next === "upload") url.searchParams.set("mode", next);
    else url.searchParams.delete("mode");
    window.history.replaceState({}, "", url);
  };
  const changeTarget = (next: string) => {
    setSelectedTarget(next);
    setShowTruth(false);
    const url = new URL(window.location.href);
    url.searchParams.set("mode", "observation");
    url.searchParams.set("target", next);
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
          <button className={mode === "observation" ? "active" : ""} type="button" aria-pressed={mode === "observation"} onClick={() => changeMode("observation")}><Planet aria-hidden="true" /><span><strong>HFF atlas</strong><small>Six public cluster fields</small></span></button>
          <button className={mode === "upload" ? "active" : ""} type="button" aria-pressed={mode === "upload"} onClick={() => changeMode("upload")}><FileArrowUp aria-hidden="true" /><span><strong>Upload FITS</strong><small>Local scientific pair</small></span></button>
        </div>
        <div className={`mode-boundary mode-boundary--${mode}`}><Atom aria-hidden="true" /><span>{mode === "simulation" ? "Truth is known by construction. Test estimator bias here." : mode === "observation" ? "Truth is unknown. Audit one model product; do not claim detection." : "Two products required. Image-only inference is disabled; files remain local."}</span></div>
      </div>

      <main id="main-workbench" className={`workbench workbench--${mode}`}>
        {mode === "simulation" ? (
          <SimulationControls params={params} setParams={setParams} layer={layer} setLayer={setLayer} />
        ) : mode === "observation" ? (
          <aside className="control-panel observation-panel" aria-labelledby="dataset-heading">
            <div className="panel-heading"><Planet aria-hidden="true" /><div><span className="overline">HFF TARGET ATLAS · 06 FIELDS</span><h2 id="dataset-heading">{dataset?.title.split(" · ", 1)[0] ?? "Select a cluster"}</h2></div></div>
            <div className="target-list" role="group" aria-label="Hubble Frontier Fields target">
              {targets.map((target, index) => <button key={target.id} type="button" className={selectedTarget === target.id ? "active" : ""} aria-pressed={selectedTarget === target.id} onClick={() => changeTarget(target.id)}><span>{String(index + 1).padStart(2, "0")}</span><strong>{target.title}</strong><small>z {target.redshift.toFixed(3)} · {target.release.startsWith("v4cor") ? "COR" : "V4"}</small></button>)}
            </div>
            {dataset ? <>
              <dl className="dataset-facts">
                <div><dt>Cluster redshift</dt><dd>{dataset.provenance.clusterRedshift}</dd></div>
                <div><dt>Lens reconstruction</dt><dd>{dataset.provenance.lensTeam}</dd></div>
                <div><dt>Release</dt><dd>{dataset.provenance.release}</dd></div>
                <div><dt>Web derivative</dt><dd>{dataset.width} × {dataset.height} cells</dd></div>
              </dl>
              <p className="panel-intro">Target-specific F814W light reprojected onto its reviewed Sharon convergence grid, then robustly aggregated for browser inspection. Full-resolution FITS analysis remains in the Python pipeline.</p>
              <details className="receipt"><summary>Provenance receipt</summary>{dataset.provenance.sourceAssets.map((asset) => <p key={asset.role}><strong>{asset.role}</strong><span>{asset.filename}</span><code>{asset.sha256}</code></p>)}</details>
              <a className="archive-link" href={dataset.provenance.sourceArchive} target="_blank" rel="noreferrer">Open authoritative archive <ArrowSquareOut aria-hidden="true" /></a>
              <a className="archive-link" href={dataset.provenance.modelReadme} target="_blank" rel="noreferrer">Read model-team contract <ArrowSquareOut aria-hidden="true" /></a>
            </> : loadError ? <div className="load-error" role="alert"><strong>Dataset unavailable</strong><span>{loadError}</span><button type="button" onClick={() => location.reload()}>Retry</button></div> : <div className="loading-state"><SpinnerGap aria-hidden="true" /><span>Loading verified derivative…</span></div>}
            <LayerControl layer={layer} setLayer={setLayer} />
          </aside>
        ) : <FitsUploadPanel onComplete={setUploadedAudit} onReset={() => setUploadedAudit(undefined)} hasResult={Boolean(uploadedAudit)} layer={layer} setLayer={setLayer} />}

        <AnimatePresence mode="wait">
          {product ? (
            <motion.div className="map-column" key={`${mode}-${dataset?.id ?? "local"}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.24 }}>
              <MapCanvas product={product} layer={layer} showTruth={showTruth} truthPoint={truthPoint} onToggleTruth={() => setShowTruth((value) => !value)} />
            </motion.div>
          ) : mode === "upload" ? <section className="upload-empty-map" aria-labelledby="upload-empty-title"><FileArrowUp aria-hidden="true" /><span className="overline">AWAITING A VALID PAIR</span><h2 id="upload-empty-title">Light is not mass.<br />Provide both products.</h2><p>Select a luminous-image FITS and a co-registered lensing convergence FITS. The evidence plane stays empty until the scientific contract passes.</p></section> : <div className="map-skeleton" aria-label="Loading map" />}
        </AnimatePresence>
        {product ? <EvidencePanel product={product} params={mode === "simulation" ? params : undefined} dataset={mode === "observation" ? dataset : undefined} uploadReceipt={mode === "upload" ? uploadedAudit?.receipt : undefined} /> : mode === "upload" ? <aside className="evidence-panel upload-guide" aria-labelledby="upload-guide-heading"><span className="overline">VALIDITY GATE</span><h2 id="upload-guide-heading">What will pass?</h2><ol><li><strong>Light image</strong><span>2D IMAGE HDU, calibrated pixels preferred.</span></li><li><strong>Mass product</strong><span>2D κ map or 3D ensemble cube.</span></li><li><strong>One grid</strong><span>Identical source dimensions; mismatched WCS is rejected.</span></li><li><strong>Interpretation</strong><span>Pixel-domain morphology audit, never particle detection.</span></li></ol></aside> : <aside className="evidence-panel evidence-panel--loading" />}
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
