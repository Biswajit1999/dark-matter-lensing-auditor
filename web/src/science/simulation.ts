import { auditEvidence } from "./audit";
import { gaussianBlur } from "./math";
import type { EvidenceProduct, Grid, SimulationParameters } from "./types";

const SIZE = 128;

function mulberry32(seed: number) {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function normal(random: () => number): number {
  return Math.sqrt(-2 * Math.log(Math.max(random(), 1e-9))) * Math.cos(2 * Math.PI * random());
}

function gaussian(x: number, y: number, cx: number, cy: number, sx: number, sy: number, angle = 0): number {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const dx = x - cx;
  const dy = y - cy;
  const rx = cos * dx + sin * dy;
  const ry = -sin * dx + cos * dy;
  return Math.exp(-0.5 * ((rx / sx) ** 2 + (ry / sy) ** 2));
}

function makeLight(random: () => number): Grid {
  const values = new Float32Array(SIZE * SIZE);
  const galaxies = Array.from({ length: 22 }, () => ({
    x: 38 + random() * 55,
    y: 36 + random() * 58,
    amplitude: 0.025 + random() * 0.065,
    width: 0.7 + random() * 1.5,
  }));
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      let value = 1.0 * gaussian(x, y, 56, 67, 14, 10, -0.25);
      value += 0.42 * gaussian(x, y, 84, 46, 8, 6, 0.5);
      for (const galaxy of galaxies) value += galaxy.amplitude * gaussian(x, y, galaxy.x, galaxy.y, galaxy.width, galaxy.width * 0.72);
      value += normal(random) * 0.006;
      values[y * SIZE + x] = Math.max(0, value);
    }
  }
  return { width: SIZE, height: SIZE, values };
}

function makeMassModel(
  params: SimulationParameters,
  family: "parametric" | "adaptive",
  random: () => number,
): Grid {
  const isAdaptive = family === "adaptive";
  const jitter = params.modelNoise * (isAdaptive ? 1.45 : 0.85);
  const biasX = isAdaptive ? -0.8 : 0.55;
  const biasY = isAdaptive ? 0.65 : -0.4;
  const cx = 56 + params.offsetX + biasX + normal(random) * jitter;
  const cy = 67 + params.offsetY + biasY + normal(random) * jitter;
  const secondaryX = 84 + params.offsetX * 0.7 + normal(random) * jitter;
  const secondaryY = 46 + params.offsetY * 0.7 + normal(random) * jitter;
  const axisRatio = 1 - params.ellipticity * 0.55;
  const values = new Float32Array(SIZE * SIZE);
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      let value = gaussian(x, y, cx, cy, 20, 20 * axisRatio, -0.18);
      value += params.haloMassRatio * gaussian(x, y, secondaryX, secondaryY, 10, 9 * axisRatio, 0.42);
      if (isAdaptive) {
        value += 0.055 * gaussian(x, y, 73 + normal(random) * 0.08, 83, 5.5, 7);
        value += normal(random) * params.modelNoise * 0.00045;
      } else {
        value += 0.028 * gaussian(x, y, 67, 34, 11, 7);
      }
      values[y * SIZE + x] = value;
    }
  }
  return gaussianBlur({ width: SIZE, height: SIZE, values }, isAdaptive ? 0.75 : 1.25);
}

export const DEFAULT_PARAMETERS: SimulationParameters = {
  seed: 2744,
  offsetX: 7,
  offsetY: -4,
  haloMassRatio: 0.34,
  ellipticity: 0.35,
  modelNoise: 1.8,
  realizations: 24,
};

export function simulateExperiment(params: SimulationParameters): EvidenceProduct {
  const random = mulberry32(params.seed);
  const light = makeLight(random);
  const models: Grid[] = [];
  const labels: Array<"parametric" | "adaptive"> = [];
  for (let index = 0; index < params.realizations; index += 1) {
    const family = index % 2 === 0 ? "parametric" : "adaptive";
    labels.push(family);
    models.push(makeMassModel(params, family, random));
  }
  return auditEvidence({
    mode: "simulation",
    light,
    models,
    familyLabels: labels,
    injectedOffset: Math.hypot(params.offsetX, params.offsetY),
  });
}
