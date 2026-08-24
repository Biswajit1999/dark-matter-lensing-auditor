import { ArrowSquareOut, DownloadSimple, SealWarning } from "@phosphor-icons/react";
import type { EvidenceProduct, HffWebDataset, SimulationParameters } from "../science/types";

type Props = {
  product: EvidenceProduct;
  params?: SimulationParameters;
  dataset?: HffWebDataset;
};

function fmt(value: number | null, digits = 2) { return value === null ? "—" : value.toFixed(digits); }

function download(name: string, body: string, mime: string) {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function EvidencePanel({ product, params, dataset }: Props) {
  const { metrics } = product;
  const report = {
    schema: "lensaudit.browser-report/1",
    generatedUtc: new Date().toISOString(),
    mode: product.mode,
    simulationParameters: params ?? null,
    observationalDataset: dataset?.id ?? null,
    metrics,
    centroids: { light: product.lightCentroid, mass: product.massCentroid, families: product.familyCentroids ?? null },
    warnings: product.warnings,
    interpretation: "Mass–light discrepancy audit; not a direct dark-matter detection.",
  };
  const rows = [
    ["Injected separation", metrics.injectedOffset, "px"],
    ["Recovered separation", metrics.recoveredOffset, "px"],
    ["Recovery interval (16–84%)", null, `${fmt(metrics.interval16)}–${fmt(metrics.interval84)} px`],
    ["Recovery bias", metrics.recoveryBias, "px"],
    ["Between-family centroid shift", metrics.modelDisagreement, "px"],
    ["Median fractional spread", metrics.fractionalSpread, ""],
    ["Area above audit threshold", metrics.excessAreaFraction * 100, "%"],
  ] as const;
  const csv = ["metric,value,unit", ...rows.map(([label, value, unit]) => `"${label}",${value === null ? "" : value},"${unit}"`)].join("\n");
  return (
    <aside className="evidence-panel" aria-labelledby="evidence-heading">
      <div className="panel-heading"><div className={`verdict-dot verdict-dot--${metrics.verdict}`} aria-hidden="true" /><div><span className="overline">RECOVERY DIAGNOSTIC</span><h2 id="evidence-heading">{metrics.verdict.replace("-", " ")}</h2></div></div>
      <div className="primary-metric">
        <span>Recovered offset</span>
        <strong>{fmt(metrics.recoveredOffset, 1)}<small> px</small></strong>
        <div className="interval-bar" aria-label={`16th to 84th percentile interval: ${fmt(metrics.interval16)} to ${fmt(metrics.interval84)} pixels`}><i style={{ left: `${Math.min(92, metrics.interval16 / 24 * 100)}%`, width: `${Math.max(4, (metrics.interval84 - metrics.interval16) / 24 * 100)}%` }} /></div>
        <p>P16 {fmt(metrics.interval16)} · P84 {fmt(metrics.interval84)}</p>
      </div>
      <div className="metric-grid">
        <div><span>Recovery bias</span><strong>{fmt(metrics.recoveryBias)}</strong><small>px</small></div>
        <div><span>Model shift</span><strong>{fmt(metrics.modelDisagreement)}</strong><small>px</small></div>
        <div><span>Fractional σ</span><strong>{fmt(metrics.fractionalSpread)}</strong><small>median</small></div>
        <div><span>Excess area</span><strong>{fmt(metrics.excessAreaFraction * 100, 1)}</strong><small>% grid</small></div>
      </div>
      <details className="evidence-table">
        <summary>Numerical evidence table</summary>
        <table>
          <caption>Audit metrics and units</caption>
          <tbody>{rows.map(([label, value, unit]) => <tr key={label}><th scope="row">{label}</th><td>{value === null ? unit : `${fmt(value)} ${unit}`}</td></tr>)}</tbody>
        </table>
      </details>
      <div className="warning-stack">
        {product.warnings.slice(0, 3).map((warning) => <p key={warning}><SealWarning aria-hidden="true" />{warning}</p>)}
      </div>
      <div className="export-actions">
        <button type="button" onClick={() => download("lensaudit-report.json", JSON.stringify(report, null, 2), "application/json")}><DownloadSimple aria-hidden="true" />JSON report</button>
        <button type="button" onClick={() => download("lensaudit-metrics.csv", csv, "text/csv")}><DownloadSimple aria-hidden="true" />Metrics CSV</button>
      </div>
      <a className="methods-link" href="https://github.com/Biswajit1999/dark-matter-lensing-auditor/blob/main/docs/METHODS.md" target="_blank" rel="noreferrer">Read the methods and validity boundaries <ArrowSquareOut aria-hidden="true" /></a>
    </aside>
  );
}
