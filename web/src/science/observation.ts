import { auditEvidence } from "./audit";
import type { EvidenceProduct, Grid, HffWebDataset } from "./types";

export function auditHffDataset(dataset: HffWebDataset): EvidenceProduct {
  const light: Grid = { width: dataset.width, height: dataset.height, values: Float32Array.from(dataset.light) };
  const kappa: Grid = { width: dataset.width, height: dataset.height, values: Float32Array.from(dataset.kappa) };
  const result = auditEvidence({ mode: "observation", light, models: [kappa] });
  return { ...result, warnings: [...result.warnings, ...dataset.limitations] };
}

export async function loadHffDataset(): Promise<HffWebDataset> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/abell2744-sharon-v4cor.json`);
  if (!response.ok) throw new Error(`Dataset request failed with HTTP ${response.status}.`);
  return response.json() as Promise<HffWebDataset>;
}
