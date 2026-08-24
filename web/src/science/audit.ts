import { centroid, distance, percentile, robustNormalize } from "./math";
import type { AuditMetrics, EvidenceProduct, Grid, Point } from "./types";

type AuditOptions = {
  mode: "simulation" | "observation";
  light: Grid;
  models: Grid[];
  familyLabels?: Array<"parametric" | "adaptive">;
  injectedOffset?: number;
  threshold?: number;
};

function averageModels(models: Grid[]): { mean: Grid; std: Grid } {
  const { width, height } = models[0];
  const mean = new Float32Array(width * height);
  const std = new Float32Array(width * height);
  for (const model of models) {
    for (let i = 0; i < mean.length; i += 1) mean[i] += model.values[i] / models.length;
  }
  if (models.length > 1) {
    for (const model of models) {
      for (let i = 0; i < std.length; i += 1) {
        const delta = model.values[i] - mean[i];
        std[i] += (delta * delta) / (models.length - 1);
      }
    }
    for (let i = 0; i < std.length; i += 1) std[i] = Math.sqrt(std[i]);
  }
  return { mean: { width, height, values: mean }, std: { width, height, values: std } };
}

function normalizedGrid(grid: Grid): Grid {
  return { ...grid, values: robustNormalize(grid.values) };
}

function familyCentroid(models: Grid[], labels: Array<"parametric" | "adaptive">, family: "parametric" | "adaptive"): Point {
  const selected = models.filter((_, index) => labels[index] === family);
  return centroid(normalizedGrid(averageModels(selected).mean));
}

export function auditEvidence(options: AuditOptions): EvidenceProduct {
  if (!options.models.length) throw new Error("At least one mass reconstruction is required.");
  const { mean, std } = averageModels(options.models);
  const light = normalizedGrid(options.light);
  const mass = normalizedGrid(mean);
  const normalizedModels = options.models.map(normalizedGrid);
  const normalizedStats = averageModels(normalizedModels);
  const uncertainty = normalizedStats.std;
  let lightPower = 0;
  let crossPower = 0;
  for (let i = 0; i < light.values.length; i += 1) {
    lightPower += light.values[i] ** 2;
    crossPower += light.values[i] * normalizedStats.mean.values[i];
  }
  const alpha = crossPower / Math.max(lightPower, 1e-9);
  const residualValues = new Float32Array(light.values.length);
  const discrepancyValues = new Float32Array(light.values.length);
  const medianScatter = percentile(uncertainty.values, 0.5);
  const systematicFloor = Math.max(0.05, medianScatter);
  let excess = 0;
  const threshold = options.threshold ?? 3;
  for (let i = 0; i < residualValues.length; i += 1) {
    residualValues[i] = normalizedStats.mean.values[i] - alpha * light.values[i];
    discrepancyValues[i] = residualValues[i] / Math.hypot(uncertainty.values[i], systematicFloor);
    if (discrepancyValues[i] >= threshold) excess += 1;
  }
  const lightCentroid = centroid(light);
  const massCentroid = centroid(mass);
  const offsets = normalizedModels.map((model) => distance(centroid(model), lightCentroid)).sort((a, b) => a - b);
  const recoveredOffset = distance(massCentroid, lightCentroid);
  let familyCentroids: EvidenceProduct["familyCentroids"];
  let modelDisagreement: number | null = null;
  if (options.familyLabels && options.familyLabels.includes("parametric") && options.familyLabels.includes("adaptive")) {
    familyCentroids = {
      parametric: familyCentroid(options.models, options.familyLabels, "parametric"),
      adaptive: familyCentroid(options.models, options.familyLabels, "adaptive"),
    };
    modelDisagreement = distance(familyCentroids.parametric, familyCentroids.adaptive);
  }
  const interval16 = percentile(offsets, 0.16);
  const interval84 = percentile(offsets, 0.84);
  const injected = options.injectedOffset ?? null;
  const recoveryBias = injected === null ? null : recoveredOffset - injected;
  const width = Math.max(interval84 - interval16, 0.01);
  let verdict: AuditMetrics["verdict"] = "observational-only";
  if (injected !== null) {
    const containsTruth = injected >= interval16 && injected <= interval84;
    verdict = containsTruth && Math.abs(recoveryBias ?? 0) <= Math.max(1.5, width) ? "identified" : width > 5 || (modelDisagreement ?? 0) > 4 ? "fragile" : "inconclusive";
  }
  const positiveMean = Array.from(normalizedStats.mean.values).filter((value) => value > 0.05);
  const fractionalSpread = positiveMean.length
    ? percentile(Array.from(uncertainty.values).map((value, index) => value / Math.max(normalizedStats.mean.values[index], 0.05)), 0.5)
    : 0;
  const warnings = options.mode === "observation"
    ? [
        "A single public lens model is displayed; between-team systematics are not measured.",
        "The score is a morphology diagnostic, not a Gaussian significance or particle detection.",
      ]
    : [
        "Synthetic truth is known only inside this controlled injection–recovery experiment.",
        "The two reconstruction families are stylized priors, not outputs from LENSTOOL, GRALE, or another lens solver.",
      ];
  return {
    mode: options.mode,
    light,
    mass,
    uncertainty,
    residual: { ...light, values: residualValues },
    discrepancy: { ...light, values: discrepancyValues },
    lightCentroid,
    massCentroid,
    familyCentroids,
    metrics: {
      injectedOffset: injected,
      recoveredOffset,
      interval16,
      interval84,
      recoveryBias,
      modelDisagreement,
      fractionalSpread,
      excessAreaFraction: excess / residualValues.length,
      verdict,
    },
    warnings,
  };
}
