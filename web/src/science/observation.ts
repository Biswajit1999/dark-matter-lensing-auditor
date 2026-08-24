import { auditEvidence } from "./audit";
import type { EvidenceProduct, Grid, HffCatalog, HffWebDataset } from "./types";

export function auditHffDataset(dataset: HffWebDataset): EvidenceProduct {
  const light: Grid = { width: dataset.width, height: dataset.height, values: Float32Array.from(dataset.light) };
  const kappa: Grid = { width: dataset.width, height: dataset.height, values: Float32Array.from(dataset.kappa) };
  const result = auditEvidence({ mode: "observation", light, models: [kappa] });
  return { ...result, warnings: [...result.warnings, ...dataset.limitations] };
}

export async function loadHffCatalog(): Promise<HffCatalog> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/catalog.json`);
  if (!response.ok) throw new Error(`Catalogue request failed with HTTP ${response.status}.`);
  const catalog = await response.json() as HffCatalog;
  if (catalog.schema !== "lensaudit.hff-catalog/1" || catalog.targets.length !== 6) {
    throw new Error("The HFF catalogue failed its six-target schema gate.");
  }
  return catalog;
}

export async function loadHffDataset(id = "abell2744-sharon-v4cor"): Promise<HffWebDataset> {
  if (!/^[a-z0-9-]+$/.test(id)) throw new Error("Target identifier failed validation.");
  const response = await fetch(`${import.meta.env.BASE_URL}data/${id}.json`);
  if (!response.ok) throw new Error(`Dataset request failed with HTTP ${response.status}.`);
  const dataset = await response.json() as HffWebDataset;
  if (dataset.schema !== "lensaudit.web-dataset/1" || dataset.id !== id) {
    throw new Error("Dataset identity did not match the requested target.");
  }
  return dataset;
}
