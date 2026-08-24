import { describe, expect, it } from "vitest";
import { DEFAULT_PARAMETERS, simulateExperiment } from "./simulation";

describe("injection–recovery simulation", () => {
  it("is deterministic for a fixed seed", () => {
    const first = simulateExperiment(DEFAULT_PARAMETERS);
    const second = simulateExperiment(DEFAULT_PARAMETERS);
    expect(first.metrics).toEqual(second.metrics);
    expect(Array.from(first.mass.values.slice(0, 64))).toEqual(Array.from(second.mass.values.slice(0, 64)));
  });

  it("recovers a larger displacement when the injected offset grows", () => {
    const centered = simulateExperiment({ ...DEFAULT_PARAMETERS, offsetX: 0, offsetY: 0, modelNoise: 0.4 });
    const displaced = simulateExperiment({ ...DEFAULT_PARAMETERS, offsetX: 14, offsetY: 0, modelNoise: 0.4 });
    expect(displaced.metrics.recoveredOffset).toBeGreaterThan(centered.metrics.recoveredOffset + 7);
    expect(displaced.metrics.injectedOffset).toBe(14);
  });

  it("reports two reconstruction-family centroids", () => {
    const result = simulateExperiment(DEFAULT_PARAMETERS);
    expect(result.familyCentroids?.parametric).toBeDefined();
    expect(result.familyCentroids?.adaptive).toBeDefined();
    expect(result.metrics.modelDisagreement).not.toBeNull();
  });

  it("keeps every evidence map on the same grid", () => {
    const result = simulateExperiment(DEFAULT_PARAMETERS);
    for (const grid of [result.light, result.mass, result.uncertainty, result.residual, result.discrepancy]) {
      expect(grid.width).toBe(128);
      expect(grid.height).toBe(128);
      expect(grid.values).toHaveLength(128 * 128);
    }
  });
});
