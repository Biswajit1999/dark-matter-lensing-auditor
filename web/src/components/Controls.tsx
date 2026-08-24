import { ArrowsClockwise, Flask, SlidersHorizontal } from "@phosphor-icons/react";
import type { Layer } from "./MapCanvas";
import type { SimulationParameters } from "../science/types";

type Props = {
  params: SimulationParameters;
  setParams: (next: SimulationParameters) => void;
  layer: Layer;
  setLayer: (layer: Layer) => void;
};

type SliderProps = {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (value: number) => void;
};

function ParameterSlider({ label, value, min, max, step, unit = "", onChange }: SliderProps) {
  const id = `parameter-${label.toLowerCase().replace(/[^a-z]+/g, "-")}`;
  return (
    <div className="parameter">
      <div className="parameter__label"><label htmlFor={id}>{label}</label><output htmlFor={id}>{value.toFixed(step < 1 ? 2 : 0)}{unit}</output></div>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <div className="parameter__extent" aria-hidden="true"><span>{min}</span><span>{max}</span></div>
    </div>
  );
}

const layers: Array<{ id: Layer; label: string }> = [
  { id: "composite", label: "Overlay" },
  { id: "mass", label: "κ morphology" },
  { id: "residual", label: "Residual" },
  { id: "uncertainty", label: "Model σ" },
];

export function LayerControl({ layer, setLayer }: Pick<Props, "layer" | "setLayer">) {
  return (
    <fieldset className="layer-control">
      <legend>Evidence plane</legend>
      {layers.map((item) => (
        <button key={item.id} type="button" className={layer === item.id ? "active" : ""} aria-pressed={layer === item.id} onClick={() => setLayer(item.id)}>{item.label}</button>
      ))}
    </fieldset>
  );
}

export function SimulationControls({ params, setParams, layer, setLayer }: Props) {
  const update = <Key extends keyof SimulationParameters>(key: Key, value: SimulationParameters[Key]) => setParams({ ...params, [key]: value });
  return (
    <aside className="control-panel" aria-labelledby="controls-heading">
      <div className="panel-heading"><SlidersHorizontal aria-hidden="true" /><div><span className="overline">GENERATIVE MODEL</span><h2 id="controls-heading">Injection controls</h2></div></div>
      <p className="panel-intro">Move the latent mass halo away from its luminous proxy, then test whether two stylized reconstruction families recover the injected separation.</p>
      <ParameterSlider label="Halo Δx" value={params.offsetX} min={-16} max={16} step={1} unit=" px" onChange={(value) => update("offsetX", value)} />
      <ParameterSlider label="Halo Δy" value={params.offsetY} min={-16} max={16} step={1} unit=" px" onChange={(value) => update("offsetY", value)} />
      <ParameterSlider label="Subhalo mass ratio" value={params.haloMassRatio} min={0.08} max={0.7} step={0.01} onChange={(value) => update("haloMassRatio", value)} />
      <ParameterSlider label="Ellipticity" value={params.ellipticity} min={0} max={0.7} step={0.01} onChange={(value) => update("ellipticity", value)} />
      <ParameterSlider label="Model-position noise" value={params.modelNoise} min={0.2} max={4.5} step={0.1} unit=" px" onChange={(value) => update("modelNoise", value)} />
      <ParameterSlider label="Realizations" value={params.realizations} min={8} max={48} step={2} onChange={(value) => update("realizations", value)} />
      <button className="seed-button" type="button" onClick={() => update("seed", params.seed + 1)}><ArrowsClockwise aria-hidden="true" />Reseed experiment <span>{params.seed}</span></button>
      <LayerControl layer={layer} setLayer={setLayer} />
      <div className="controlled-badge"><Flask aria-hidden="true" /><span><strong>Controlled experiment</strong>Known truth is available; no observational claim is made.</span></div>
    </aside>
  );
}
