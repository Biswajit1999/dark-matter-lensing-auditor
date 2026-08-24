import { useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle, Cpu, FileArrowUp, LockSimple, SpinnerGap, WarningCircle, XCircle } from "@phosphor-icons/react";
import { analyzeFitsPair, compareFitsWcs, formatHdu, loadFitsFile, type LoadedFitsFile, type UploadedAudit } from "../science/fits";
import type { Layer } from "./MapCanvas";
import { LayerControl } from "./Controls";

type Role = "light" | "kappa";

type Props = {
  onComplete: (audit: UploadedAudit) => void;
  onReset: () => void;
  hasResult: boolean;
  layer: Layer;
  setLayer: (layer: Layer) => void;
};

type FileState = {
  status: "idle" | "reading" | "ready" | "error";
  loaded?: LoadedFitsFile;
  selectedHdu?: number;
  error?: string;
};

const EMPTY: FileState = { status: "idle" };

function prettyBytes(bytes: number): string {
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MiB`;
  return `${(bytes / 1024).toFixed(1)} KiB`;
}

function FitsField({ role, state, onFile, onHdu }: { role: Role; state: FileState; onFile: (file: File) => void; onHdu: (hdu: number) => void }) {
  const inputId = `${role}-fits-file`;
  const errorId = `${role}-fits-error`;
  const label = role === "light" ? "Luminous image FITS" : "Lensing κ FITS or cube";
  const helper = role === "light" ? "A calibrated 2D intensity image; this is only a luminous-matter proxy." : "A 2D convergence map or 3D ensemble cube ordered [model, y, x].";
  return (
    <fieldset className={`fits-field fits-field--${state.status}`}>
      <legend>{label} <span>required</span></legend>
      <p>{helper}</p>
      <label className="fits-drop" htmlFor={inputId}>
        {state.status === "reading" ? <SpinnerGap aria-hidden="true" className="spin" /> : state.status === "ready" ? <CheckCircle aria-hidden="true" /> : state.status === "error" ? <XCircle aria-hidden="true" /> : <FileArrowUp aria-hidden="true" />}
        <span>
          <strong>{state.loaded?.file.name ?? (state.status === "reading" ? "Inspecting FITS headers…" : "Choose a local FITS file")}</strong>
          <small>{state.loaded ? `${prettyBytes(state.loaded.file.size)} · ${state.loaded.imageHdus.length} compatible image HDU${state.loaded.imageHdus.length === 1 ? "" : "s"}` : "FITS / FIT / FTS · maximum 512 MiB"}</small>
        </span>
        <input
          id={inputId}
          type="file"
          accept=".fits,.fit,.fts,application/fits"
          aria-describedby={state.error ? errorId : undefined}
          onChange={(event) => { const file = event.target.files?.[0]; if (file) onFile(file); event.target.value = ""; }}
        />
      </label>
      {state.error && <p className="field-error" id={errorId} role="alert">{state.error}</p>}
      {state.loaded && state.selectedHdu !== undefined && (
        <div className="hdu-select">
          <label htmlFor={`${role}-hdu`}>Image HDU</label>
          <select id={`${role}-hdu`} value={state.selectedHdu} onChange={(event) => onHdu(Number(event.target.value))}>
            {state.loaded.imageHdus.map((hdu) => <option key={hdu.index} value={hdu.index}>{formatHdu(hdu)}</option>)}
          </select>
        </div>
      )}
    </fieldset>
  );
}

export function FitsUploadPanel({ onComplete, onReset, hasResult, layer, setLayer }: Props) {
  const [light, setLight] = useState<FileState>(EMPTY);
  const [kappa, setKappa] = useState<FileState>(EMPTY);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string>();
  const errorRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (error) errorRef.current?.focus(); }, [error]);

  const inspect = async (role: Role, file: File) => {
    const setter = role === "light" ? setLight : setKappa;
    setter({ status: "reading" });
    setError(undefined);
    onReset();
    try {
      const loaded = await loadFitsFile(file);
      const preferred = role === "light" ? loaded.imageHdus.find((hdu) => hdu.axes.length === 2) : loaded.imageHdus.find((hdu) => hdu.axes.length === 3) ?? loaded.imageHdus[0];
      if (!preferred) throw new Error(role === "light" ? "No 2D image HDU is available for the luminous proxy." : "No compatible convergence image is available.");
      setter({ status: "ready", loaded, selectedHdu: preferred.index });
    } catch (reason) {
      setter({ status: "error", error: reason instanceof Error ? reason.message : String(reason) });
    }
  };

  const compatibility = useMemo(() => {
    if (!light.loaded || light.selectedHdu === undefined || !kappa.loaded || kappa.selectedHdu === undefined) return null;
    return compareFitsWcs(light.loaded.hdus[light.selectedHdu], kappa.loaded.hdus[kappa.selectedHdu]);
  }, [light, kappa]);

  const analyze = async () => {
    setError(undefined);
    if (!light.loaded || light.selectedHdu === undefined || !kappa.loaded || kappa.selectedHdu === undefined) {
      setError("Select both required FITS products and compatible IMAGE HDUs.");
      return;
    }
    if (compatibility?.status === "mismatch") { setError(compatibility.message); return; }
    setRunning(true);
    try {
      onComplete(await analyzeFitsPair(light.loaded, light.selectedHdu, kappa.loaded, kappa.selectedHdu));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setRunning(false);
    }
  };

  const updateHdu = (role: Role, hdu: number) => {
    const setter = role === "light" ? setLight : setKappa;
    setter((current) => ({ ...current, selectedHdu: hdu }));
    setError(undefined);
    onReset();
  };

  return (
    <aside className="control-panel upload-panel" aria-labelledby="upload-heading">
      <div className="panel-heading"><FileArrowUp aria-hidden="true" /><div><span className="overline">LOCAL FITS WORKSPACE</span><h2 id="upload-heading">Pair scientific products</h2></div></div>
      <p className="panel-intro">The browser audits an existing lensing reconstruction against light. It does not reconstruct dark matter from the telescope image.</p>
      {error && <div className="upload-error" role="alert" tabIndex={-1} ref={errorRef}><WarningCircle aria-hidden="true" /><span><strong>Analysis stopped</strong>{error}</span></div>}
      <FitsField role="light" state={light} onFile={(file) => inspect("light", file)} onHdu={(hdu) => updateHdu("light", hdu)} />
      <div className="pair-link" aria-hidden="true"><i /><span>same source grid + compatible WCS</span><i /></div>
      <FitsField role="kappa" state={kappa} onFile={(file) => inspect("kappa", file)} onHdu={(hdu) => updateHdu("kappa", hdu)} />
      {compatibility && (
        <div className={`compatibility compatibility--${compatibility.status}`} aria-live="polite">
          {compatibility.status === "mismatch" ? <XCircle aria-hidden="true" /> : compatibility.status === "verified" ? <CheckCircle aria-hidden="true" /> : <WarningCircle aria-hidden="true" />}
          <span><strong>{compatibility.status === "verified" ? "WCS verified" : compatibility.status === "mismatch" ? "Grid rejected" : "WCS unverified"}</strong>{compatibility.message}</span>
        </div>
      )}
      <button className="analyze-button" type="button" disabled={running || light.status !== "ready" || kappa.status !== "ready" || compatibility?.status === "mismatch"} onClick={analyze}>
        {running ? <SpinnerGap aria-hidden="true" className="spin" /> : <Cpu aria-hidden="true" />}
        {running ? "Hashing and auditing locally…" : hasResult ? "Re-run local audit" : "Run local audit"}
      </button>
      <div className="privacy-note"><LockSimple aria-hidden="true" /><span><strong>No upload occurs</strong>Files stay in this browser tab. No API, storage, account, or telemetry receives their contents.</span></div>
      {hasResult && <LayerControl layer={layer} setLayer={setLayer} />}
    </aside>
  );
}
