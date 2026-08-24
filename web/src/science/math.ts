import type { Grid, Point } from "./types";

export const clamp = (value: number, low = 0, high = 1) => Math.min(high, Math.max(low, value));

export function percentile(values: ArrayLike<number>, quantile: number): number {
  const finite = Array.from(values).filter(Number.isFinite).sort((a, b) => a - b);
  if (!finite.length) return 0;
  const index = clamp(quantile) * (finite.length - 1);
  const lower = Math.floor(index);
  const fraction = index - lower;
  return finite[lower] * (1 - fraction) + finite[Math.min(lower + 1, finite.length - 1)] * fraction;
}

export function robustNormalize(values: ArrayLike<number>): Float32Array {
  const low = percentile(values, 0.01);
  const high = percentile(values, 0.99);
  const span = Math.max(high - low, 1e-9);
  return Float32Array.from(values, (value) => clamp((value - low) / span));
}

export function centroid(grid: Grid): Point {
  let total = 0;
  let weightedX = 0;
  let weightedY = 0;
  for (let y = 0; y < grid.height; y += 1) {
    for (let x = 0; x < grid.width; x += 1) {
      const weight = Math.max(0, grid.values[y * grid.width + x]);
      total += weight;
      weightedX += x * weight;
      weightedY += y * weight;
    }
  }
  return total > 0 ? { x: weightedX / total, y: weightedY / total } : { x: 0, y: 0 };
}

export const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

export function gaussianBlur(grid: Grid, sigma: number): Grid {
  if (sigma <= 0) return { ...grid, values: new Float32Array(grid.values) };
  const radius = Math.max(1, Math.ceil(sigma * 3));
  const kernel = new Float32Array(radius * 2 + 1);
  let sum = 0;
  for (let i = -radius; i <= radius; i += 1) {
    const value = Math.exp(-(i * i) / (2 * sigma * sigma));
    kernel[i + radius] = value;
    sum += value;
  }
  for (let i = 0; i < kernel.length; i += 1) kernel[i] /= sum;
  const horizontal = new Float32Array(grid.values.length);
  const output = new Float32Array(grid.values.length);
  for (let y = 0; y < grid.height; y += 1) {
    for (let x = 0; x < grid.width; x += 1) {
      let value = 0;
      for (let k = -radius; k <= radius; k += 1) {
        const sx = Math.min(grid.width - 1, Math.max(0, x + k));
        value += grid.values[y * grid.width + sx] * kernel[k + radius];
      }
      horizontal[y * grid.width + x] = value;
    }
  }
  for (let y = 0; y < grid.height; y += 1) {
    for (let x = 0; x < grid.width; x += 1) {
      let value = 0;
      for (let k = -radius; k <= radius; k += 1) {
        const sy = Math.min(grid.height - 1, Math.max(0, y + k));
        value += horizontal[sy * grid.width + x] * kernel[k + radius];
      }
      output[y * grid.width + x] = value;
    }
  }
  return { ...grid, values: output };
}
