import { useEffect, useMemo, useRef, useState } from "react";
import { CrosshairSimple, Eye, EyeSlash } from "@phosphor-icons/react";
import type { EvidenceProduct, Grid, Point } from "../science/types";
import { clamp, percentile, robustNormalize } from "../science/math";

export type Layer = "composite" | "mass" | "residual" | "uncertainty";

type Props = {
  product: EvidenceProduct;
  layer: Layer;
  showTruth: boolean;
  truthPoint?: Point;
  onToggleTruth: () => void;
};

type Rgb = [number, number, number];

const VIRIDIS: Rgb[] = [[9, 18, 32], [45, 46, 104], [42, 116, 142], [63, 180, 115], [224, 227, 93]];
const HEAT: Rgb[] = [[7, 12, 14], [75, 23, 81], [191, 54, 48], [244, 151, 61], [248, 244, 206]];
const DIVERGING: Rgb[] = [[20, 65, 126], [58, 145, 181], [220, 228, 219], [232, 132, 73], [119, 29, 47]];
const UNCERTAINTY: Rgb[] = [[8, 16, 20], [34, 71, 93], [46, 139, 130], [202, 222, 133]];

function paletteColor(value: number, palette: Rgb[]): Rgb {
  const position = clamp(value) * (palette.length - 1);
  const index = Math.min(palette.length - 2, Math.floor(position));
  const mix = position - index;
  return palette[index].map((component, channel) => Math.round(component * (1 - mix) + palette[index + 1][channel] * mix)) as Rgb;
}

function rasterGrid(ctx: CanvasRenderingContext2D, grid: Grid, palette: Rgb[], mode: "sequential" | "diverging" = "sequential") {
  const image = ctx.createImageData(grid.width, grid.height);
  const normalized = mode === "sequential" ? robustNormalize(grid.values) : null;
  const scale = mode === "diverging" ? Math.max(Math.abs(percentile(grid.values, 0.02)), Math.abs(percentile(grid.values, 0.98)), 1e-6) : 1;
  for (let i = 0; i < grid.values.length; i += 1) {
    const value = normalized ? normalized[i] : clamp(0.5 + grid.values[i] / (2 * scale));
    const [red, green, blue] = paletteColor(value, palette);
    image.data[i * 4] = red;
    image.data[i * 4 + 1] = green;
    image.data[i * 4 + 2] = blue;
    image.data[i * 4 + 3] = 255;
  }
  const buffer = document.createElement("canvas");
  buffer.width = grid.width;
  buffer.height = grid.height;
  buffer.getContext("2d")!.putImageData(image, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(buffer, 0, 0, ctx.canvas.width, ctx.canvas.height);
}

function compositeGrid(ctx: CanvasRenderingContext2D, light: Grid, mass: Grid) {
  const l = robustNormalize(light.values);
  const m = robustNormalize(mass.values);
  const image = ctx.createImageData(light.width, light.height);
  for (let i = 0; i < l.length; i += 1) {
    const base = Math.round(8 + l[i] * 158);
    const heat = paletteColor(m[i], HEAT);
    const alpha = 0.16 + m[i] * 0.56;
    image.data[i * 4] = Math.round(base * (1 - alpha) + heat[0] * alpha);
    image.data[i * 4 + 1] = Math.round((base + 7) * (1 - alpha) + heat[1] * alpha);
    image.data[i * 4 + 2] = Math.round((base + 5) * (1 - alpha) + heat[2] * alpha);
    image.data[i * 4 + 3] = 255;
  }
  const buffer = document.createElement("canvas");
  buffer.width = light.width;
  buffer.height = light.height;
  buffer.getContext("2d")!.putImageData(image, 0, 0);
  ctx.drawImage(buffer, 0, 0, ctx.canvas.width, ctx.canvas.height);
}

function drawContours(ctx: CanvasRenderingContext2D, grid: Grid) {
  const values = robustNormalize(grid.values);
  const levels = [0.42, 0.58, 0.72, 0.84];
  const sx = ctx.canvas.width / grid.width;
  const sy = ctx.canvas.height / grid.height;
  ctx.save();
  ctx.lineWidth = Math.max(1, ctx.canvas.width / 700);
  for (const [levelIndex, level] of levels.entries()) {
    ctx.beginPath();
    ctx.strokeStyle = levelIndex === levels.length - 1 ? "rgba(255,248,218,.95)" : "rgba(255,242,204,.58)";
    for (let y = 0; y < grid.height - 1; y += 1) {
      for (let x = 0; x < grid.width - 1; x += 1) {
        const tl = values[y * grid.width + x] >= level;
        const tr = values[y * grid.width + x + 1] >= level;
        const bl = values[(y + 1) * grid.width + x] >= level;
        const br = values[(y + 1) * grid.width + x + 1] >= level;
        const crossings: Array<[number, number]> = [];
        if (tl !== tr) crossings.push([x + 0.5, y]);
        if (tr !== br) crossings.push([x + 1, y + 0.5]);
        if (br !== bl) crossings.push([x + 0.5, y + 1]);
        if (bl !== tl) crossings.push([x, y + 0.5]);
        if (crossings.length >= 2) {
          ctx.moveTo(crossings[0][0] * sx, crossings[0][1] * sy);
          ctx.lineTo(crossings[1][0] * sx, crossings[1][1] * sy);
          if (crossings.length === 4) {
            ctx.moveTo(crossings[2][0] * sx, crossings[2][1] * sy);
            ctx.lineTo(crossings[3][0] * sx, crossings[3][1] * sy);
          }
        }
      }
    }
    ctx.stroke();
  }
  ctx.restore();
}

function drawMarker(ctx: CanvasRenderingContext2D, point: Point, grid: Grid, color: string, shape: "cross" | "circle" | "diamond") {
  const x = (point.x / grid.width) * ctx.canvas.width;
  const y = (point.y / grid.height) * ctx.canvas.height;
  const size = Math.max(7, ctx.canvas.width / 75);
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = "rgba(7,16,15,.7)";
  ctx.lineWidth = Math.max(2, ctx.canvas.width / 420);
  ctx.beginPath();
  if (shape === "circle") ctx.arc(x, y, size, 0, Math.PI * 2);
  else if (shape === "diamond") {
    ctx.moveTo(x, y - size); ctx.lineTo(x + size, y); ctx.lineTo(x, y + size); ctx.lineTo(x - size, y); ctx.closePath();
  } else {
    ctx.moveTo(x - size, y); ctx.lineTo(x + size, y); ctx.moveTo(x, y - size); ctx.lineTo(x, y + size);
  }
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

const layerNames: Record<Layer, string> = {
  composite: "Mass contours over luminous morphology",
  mass: "Mean convergence morphology",
  residual: "Normalized mass minus fitted light proxy",
  uncertainty: "Across-model reconstruction scatter",
};

export function MapCanvas({ product, layer, showTruth, truthPoint, onToggleTruth }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [probe, setProbe] = useState<Point>(() => ({ x: Math.round(product.massCentroid.x), y: Math.round(product.massCentroid.y) }));
  const grid = layer === "residual" ? product.residual : layer === "uncertainty" ? product.uncertainty : product.mass;
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const side = 960;
    canvas.width = side;
    canvas.height = side;
    if (layer === "composite") compositeGrid(ctx, product.light, product.mass);
    else if (layer === "mass") rasterGrid(ctx, product.mass, VIRIDIS);
    else if (layer === "residual") rasterGrid(ctx, product.residual, DIVERGING, "diverging");
    else rasterGrid(ctx, product.uncertainty, UNCERTAINTY);
    if (layer === "composite" || layer === "mass") drawContours(ctx, product.mass);
    drawMarker(ctx, product.lightCentroid, product.light, "#a7edca", "cross");
    drawMarker(ctx, product.massCentroid, product.mass, "#ffd166", "circle");
    if (showTruth && truthPoint) drawMarker(ctx, truthPoint, product.mass, "#ff7d67", "diamond");
  }, [layer, product, showTruth, truthPoint]);

  const sample = useMemo(() => {
    const x = Math.min(grid.width - 1, Math.max(0, Math.round(probe.x)));
    const y = Math.min(grid.height - 1, Math.max(0, Math.round(probe.y)));
    const index = y * grid.width + x;
    return { x, y, light: product.light.values[index], mass: product.mass.values[index], residual: product.residual.values[index], uncertainty: product.uncertainty.values[index] };
  }, [grid, probe, product]);

  const setFromPointer = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const bounds = canvas.getBoundingClientRect();
    setProbe({ x: ((clientX - bounds.left) / bounds.width) * grid.width, y: ((clientY - bounds.top) / bounds.height) * grid.height });
  };

  return (
    <section className="map-stage" aria-labelledby="map-heading">
      <div className="map-stage__header">
        <div>
          <span className="overline">ACTIVE EVIDENCE PLANE</span>
          <h2 id="map-heading">{layerNames[layer]}</h2>
        </div>
        {truthPoint && (
          <button className="icon-label-button" type="button" aria-pressed={showTruth} onClick={onToggleTruth}>
            {showTruth ? <EyeSlash aria-hidden="true" /> : <Eye aria-hidden="true" />}
            {showTruth ? "Hide truth" : "Reveal truth"}
          </button>
        )}
      </div>
      <div className="map-frame">
        <canvas
          ref={canvasRef}
          className="science-canvas"
          role="img"
          tabIndex={0}
          aria-label={`${layerNames[layer]}. Light centroid is a cross, mass centroid is a circle${truthPoint ? ", and injected truth is a diamond when enabled" : ""}. Use arrow keys to move the numerical probe.`}
          onPointerMove={(event) => setFromPointer(event.clientX, event.clientY)}
          onPointerDown={(event) => setFromPointer(event.clientX, event.clientY)}
          onKeyDown={(event) => {
            const delta: Record<string, Point> = { ArrowLeft: { x: -1, y: 0 }, ArrowRight: { x: 1, y: 0 }, ArrowUp: { x: 0, y: -1 }, ArrowDown: { x: 0, y: 1 } };
            if (!delta[event.key]) return;
            event.preventDefault();
            setProbe((current) => ({ x: Math.min(grid.width - 1, Math.max(0, current.x + delta[event.key].x)), y: Math.min(grid.height - 1, Math.max(0, current.y + delta[event.key].y)) }));
          }}
        />
        <div className="probe" aria-live="polite">
          <CrosshairSimple aria-hidden="true" />
          <span>x {sample.x} · y {sample.y}</span>
          <strong>κ′ {sample.mass.toFixed(3)}</strong>
          <span>light′ {sample.light.toFixed(3)}</span>
          <span>R {sample.residual.toFixed(3)}</span>
          <span>σmodel {sample.uncertainty.toFixed(3)}</span>
        </div>
        <div className="map-scale" aria-hidden="true"><span>0</span><i /><span>{grid.width} px</span></div>
      </div>
      <div className="map-legend" aria-label="Map marker legend">
        <span><i className="legend-marker legend-marker--cross" />Light centroid</span>
        <span><i className="legend-marker legend-marker--circle" />Mass centroid</span>
        {truthPoint && showTruth && <span><i className="legend-marker legend-marker--diamond" />Injected truth</span>}
        <span className="legend-gradient" aria-hidden="true" />
        <span>{layer === "residual" ? "negative → positive" : "low → high"}</span>
      </div>
    </section>
  );
}
