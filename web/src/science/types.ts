export type Grid = {
  width: number;
  height: number;
  values: Float32Array;
};

export type Point = { x: number; y: number };

export type SimulationParameters = {
  seed: number;
  offsetX: number;
  offsetY: number;
  haloMassRatio: number;
  ellipticity: number;
  modelNoise: number;
  realizations: number;
};

export type AuditMetrics = {
  injectedOffset: number | null;
  recoveredOffset: number;
  interval16: number;
  interval84: number;
  recoveryBias: number | null;
  modelDisagreement: number | null;
  fractionalSpread: number;
  excessAreaFraction: number;
  verdict: "identified" | "fragile" | "inconclusive" | "observational-only";
};

export type EvidenceProduct = {
  mode: "simulation" | "observation";
  light: Grid;
  mass: Grid;
  uncertainty: Grid;
  residual: Grid;
  discrepancy: Grid;
  lightCentroid: Point;
  massCentroid: Point;
  familyCentroids?: { parametric: Point; adaptive: Point };
  metrics: AuditMetrics;
  warnings: string[];
};

export type HffWebDataset = {
  schema: "lensaudit.web-dataset/1";
  id: string;
  title: string;
  width: number;
  height: number;
  light: number[];
  kappa: number[];
  footprint: number[];
  display: { lightTransform: string; kappaUnit: string };
  provenance: {
    clusterRedshift: number;
    lensTeam: string;
    release: string;
    sourceArchive: string;
    modelReadme: string;
    generatedUtc: string;
    derivativeMethod: string;
    sourceAssets: Array<{ role: string; filename: string; sha256: string }>;
  };
  limitations: string[];
};
