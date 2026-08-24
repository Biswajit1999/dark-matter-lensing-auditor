import { auditEvidence } from "./audit";
import { gaussianBlur, percentile } from "./math";
import type { EvidenceProduct, Grid } from "./types";

export type FitsHeaderValue = string | number | boolean;

export type FitsHdu = {
  index: number;
  name: string;
  kind: string;
  bitpix: number;
  axes: number[];
  dataOffset: number;
  dataBytes: number;
  header: Record<string, FitsHeaderValue>;
  supportedImage: boolean;
};

export type LoadedFitsFile = {
  file: File;
  buffer: ArrayBuffer;
  hdus: FitsHdu[];
  imageHdus: FitsHdu[];
};

export type WcsCompatibility = {
  status: "verified" | "unverified" | "mismatch";
  message: string;
};

export type UploadReceipt = {
  schema: "lensaudit.upload-receipt/1";
  generatedUtc: string;
  light: UploadAssetReceipt;
  kappa: UploadAssetReceipt;
  wcs: WcsCompatibility;
  targetGrid: [number, number];
  aggregationMethod: string;
  selectedKappaPlanes: number[];
};

export type UploadAssetReceipt = {
  role: "light" | "kappa";
  filename: string;
  bytes: number;
  sha256: string;
  hduIndex: number;
  hduName: string;
  bitpix: number;
  axes: number[];
  bunit: string | null;
  ctype: [string | null, string | null];
};

export type UploadedAudit = { product: EvidenceProduct; receipt: UploadReceipt };

const BLOCK = 2880;
const CARD = 80;
const MAX_FILE_BYTES = 512 * 1024 * 1024;
const SUPPORTED_BITPIX = new Set([8, 16, 32, 64, -32, -64]);
const decoder = new TextDecoder("ascii");

function roundBlock(bytes: number): number {
  return Math.ceil(bytes / BLOCK) * BLOCK;
}

function unquotedValue(field: string): string {
  let quoted = false;
  for (let index = 0; index < field.length; index += 1) {
    if (field[index] === "'") {
      if (quoted && field[index + 1] === "'") index += 1;
      else quoted = !quoted;
    } else if (field[index] === "/" && !quoted) return field.slice(0, index).trim();
  }
  return field.trim();
}

function parseValue(field: string): FitsHeaderValue {
  const clean = unquotedValue(field);
  if (clean.startsWith("'")) return clean.slice(1, clean.lastIndexOf("'")).replace(/''/g, "'").trimEnd();
  if (clean === "T") return true;
  if (clean === "F") return false;
  const numeric = Number(clean.replace(/[dD]/, "E"));
  return Number.isFinite(numeric) ? numeric : clean;
}

export function parseFitsHdus(buffer: ArrayBuffer): FitsHdu[] {
  if (buffer.byteLength < BLOCK) throw new Error("The file is too small to contain a FITS header.");
  const view = new Uint8Array(buffer);
  const signature = decoder.decode(view.subarray(0, 8)).trim();
  if (signature !== "SIMPLE") throw new Error("The first FITS card is not SIMPLE; select an uncompressed FITS file.");
  const hdus: FitsHdu[] = [];
  let offset = 0;
  while (offset + CARD <= buffer.byteLength) {
    const header: Record<string, FitsHeaderValue> = {};
    let cursor = offset;
    let foundEnd = false;
    while (cursor + CARD <= buffer.byteLength) {
      const card = decoder.decode(view.subarray(cursor, cursor + CARD));
      cursor += CARD;
      const key = card.slice(0, 8).trim();
      if (key === "END") { foundEnd = true; break; }
      if (key && card[8] === "=") header[key] = parseValue(card.slice(10));
    }
    if (!foundEnd) throw new Error(`HDU ${hdus.length} has no END card.`);
    const dataOffset = offset + roundBlock(cursor - offset);
    const bitpix = Number(header.BITPIX ?? 0);
    const naxis = Number(header.NAXIS ?? 0);
    if (!Number.isInteger(naxis) || naxis < 0 || naxis > 9) throw new Error(`HDU ${hdus.length} has invalid NAXIS=${naxis}.`);
    const axes = Array.from({ length: naxis }, (_, axis) => Number(header[`NAXIS${axis + 1}`] ?? 0));
    const elements = axes.length ? axes.reduce((product, length) => product * Math.max(0, length), 1) : 0;
    const pcount = Number(header.PCOUNT ?? 0);
    const gcount = Number(header.GCOUNT ?? 1);
    const bytesPerElement = Math.abs(bitpix) / 8;
    const dataBytes = Number.isFinite(bytesPerElement) ? (elements * bytesPerElement + pcount) * gcount : 0;
    if (dataOffset + dataBytes > buffer.byteLength) throw new Error(`HDU ${hdus.length} data extends beyond the uploaded file.`);
    const kind = String(header.XTENSION ?? (hdus.length === 0 ? "PRIMARY" : "UNKNOWN")).trim();
    const name = String(header.EXTNAME ?? (hdus.length === 0 ? "PRIMARY" : `HDU ${hdus.length}`)).trim();
    const isImageKind = hdus.length === 0 || kind.toUpperCase().includes("IMAGE");
    const supportedImage = isImageKind && (naxis === 2 || naxis === 3) && axes.every((length) => Number.isInteger(length) && length > 0) && SUPPORTED_BITPIX.has(bitpix);
    hdus.push({ index: hdus.length, name, kind, bitpix, axes, dataOffset, dataBytes, header, supportedImage });
    const next = dataOffset + roundBlock(dataBytes);
    if (next <= offset || next >= buffer.byteLength) break;
    offset = next;
  }
  return hdus;
}

export async function loadFitsFile(file: File): Promise<LoadedFitsFile> {
  if (file.size > MAX_FILE_BYTES) throw new Error(`Files larger than 512 MiB are not accepted in the browser. Use the Python CLI for ${file.name}.`);
  if (file.size < BLOCK) throw new Error(`${file.name} is too small to be a FITS file.`);
  const buffer = await file.arrayBuffer();
  const hdus = parseFitsHdus(buffer);
  const imageHdus = hdus.filter((hdu) => hdu.supportedImage);
  if (!imageHdus.length) throw new Error(`${file.name} has no supported 2D or 3D IMAGE HDU. Supported BITPIX values: 8, 16, 32, 64, -32, -64.`);
  return { file, buffer, hdus, imageHdus };
}

function headerNumber(hdu: FitsHdu, key: string): number | null {
  const value = hdu.header[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function headerString(hdu: FitsHdu, key: string): string | null {
  const value = hdu.header[key];
  return typeof value === "string" ? value.trim() : null;
}

export function compareFitsWcs(light: FitsHdu, kappa: FitsHdu): WcsCompatibility {
  if (light.axes[0] !== kappa.axes[0] || light.axes[1] !== kappa.axes[1]) {
    return { status: "mismatch", message: `Source grids differ: light ${light.axes[0]}×${light.axes[1]} versus κ ${kappa.axes[0]}×${kappa.axes[1]}. Reproject with the Python workflow.` };
  }
  const stringKeys = ["CTYPE1", "CTYPE2"];
  for (const key of stringKeys) {
    const left = headerString(light, key);
    const right = headerString(kappa, key);
    if (left && right && left !== right) return { status: "mismatch", message: `${key} differs (${left} versus ${right}); browser analysis stops rather than aligning by array shape.` };
  }
  const checks: Array<[string, number]> = [
    ["CRPIX1", 1e-2], ["CRPIX2", 1e-2], ["CRVAL1", 1e-7], ["CRVAL2", 1e-7],
    ["CDELT1", 1e-10], ["CDELT2", 1e-10], ["CD1_1", 1e-10], ["CD1_2", 1e-10],
    ["CD2_1", 1e-10], ["CD2_2", 1e-10], ["PC1_1", 1e-10], ["PC1_2", 1e-10],
    ["PC2_1", 1e-10], ["PC2_2", 1e-10],
  ];
  for (const [key, tolerance] of checks) {
    const left = headerNumber(light, key);
    const right = headerNumber(kappa, key);
    if (left !== null && right !== null && Math.abs(left - right) > tolerance * Math.max(1, Math.abs(left), Math.abs(right))) {
      return { status: "mismatch", message: `${key} differs (${left} versus ${right}); reproject the light image onto the κ WCS before upload.` };
    }
  }
  const core = ["CTYPE1", "CTYPE2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2"];
  const hasCore = core.every((key) => light.header[key] !== undefined && kappa.header[key] !== undefined);
  const lightHasScale = (light.header.CDELT1 !== undefined && light.header.CDELT2 !== undefined) || light.header.CD1_1 !== undefined;
  const kappaHasScale = (kappa.header.CDELT1 !== undefined && kappa.header.CDELT2 !== undefined) || kappa.header.CD1_1 !== undefined;
  if (!hasCore || !lightHasScale || !kappaHasScale) {
    return { status: "unverified", message: "Array dimensions match, but one or both HDUs lack a complete celestial WCS. Results remain in pixels and registration is unverified." };
  }
  return { status: "verified", message: "Dimensions and compared celestial-WCS terms agree within strict browser tolerances." };
}

function readPixel(view: DataView, hdu: FitsHdu, element: number): number {
  const bytes = Math.abs(hdu.bitpix) / 8;
  const offset = hdu.dataOffset + element * bytes;
  let raw: number;
  if (hdu.bitpix === 8) raw = view.getUint8(offset);
  else if (hdu.bitpix === 16) raw = view.getInt16(offset, false);
  else if (hdu.bitpix === 32) raw = view.getInt32(offset, false);
  else if (hdu.bitpix === 64) raw = Number(view.getBigInt64(offset, false));
  else if (hdu.bitpix === -32) raw = view.getFloat32(offset, false);
  else raw = view.getFloat64(offset, false);
  const blank = headerNumber(hdu, "BLANK");
  if (hdu.bitpix > 0 && blank !== null && raw === blank) return Number.NaN;
  return raw * (headerNumber(hdu, "BSCALE") ?? 1) + (headerNumber(hdu, "BZERO") ?? 0);
}

function selectedPlanes(hdu: FitsHdu, maximum = 24): number[] {
  const depth = hdu.axes[2] ?? 1;
  if (depth <= maximum) return Array.from({ length: depth }, (_, index) => index);
  return Array.from({ length: maximum }, (_, index) => Math.round(index * (depth - 1) / (maximum - 1)));
}

function aggregatePlane(buffer: ArrayBuffer, hdu: FitsHdu, plane: number, target: number): Grid {
  const width = hdu.axes[0];
  const height = hdu.axes[1];
  const view = new DataView(buffer);
  const values = new Float32Array(target * target);
  const planeOffset = plane * width * height;
  for (let targetY = 0; targetY < target; targetY += 1) {
    const y0 = Math.floor(targetY * height / target);
    const y1 = Math.max(y0 + 1, Math.floor((targetY + 1) * height / target));
    for (let targetX = 0; targetX < target; targetX += 1) {
      const x0 = Math.floor(targetX * width / target);
      const x1 = Math.max(x0 + 1, Math.floor((targetX + 1) * width / target));
      const area = (x1 - x0) * (y1 - y0);
      const stride = Math.max(1, Math.ceil(Math.sqrt(area / 64)));
      let total = 0;
      let count = 0;
      for (let y = y0 + Math.floor(stride / 2); y < y1; y += stride) {
        for (let x = x0 + Math.floor(stride / 2); x < x1; x += stride) {
          const value = readPixel(view, hdu, planeOffset + y * width + x);
          if (Number.isFinite(value)) { total += value; count += 1; }
        }
      }
      values[targetY * target + targetX] = count ? total / count : Number.NaN;
    }
  }
  return { width: target, height: target, values };
}

function prepareLight(grid: Grid): Grid {
  const finite = Array.from(grid.values).filter(Number.isFinite);
  const background = percentile(finite, 0.2);
  const positive = Float32Array.from(grid.values, (value) => Number.isFinite(value) ? Math.max(0, value - background) : 0);
  const scale = Math.max(percentile(positive, 0.9), 1e-12);
  const compressed = Float32Array.from(positive, (value) => Math.asinh(value / scale));
  return gaussianBlur({ ...grid, values: compressed }, 1);
}

async function sha256(buffer: ArrayBuffer): Promise<string> {
  const hash = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function assetReceipt(role: "light" | "kappa", source: LoadedFitsFile, hdu: FitsHdu, hash: string): UploadAssetReceipt {
  return {
    role,
    filename: source.file.name,
    bytes: source.file.size,
    sha256: hash,
    hduIndex: hdu.index,
    hduName: hdu.name,
    bitpix: hdu.bitpix,
    axes: hdu.axes,
    bunit: headerString(hdu, "BUNIT"),
    ctype: [headerString(hdu, "CTYPE1"), headerString(hdu, "CTYPE2")],
  };
}

export async function analyzeFitsPair(lightSource: LoadedFitsFile, lightHduIndex: number, kappaSource: LoadedFitsFile, kappaHduIndex: number): Promise<UploadedAudit> {
  const lightHdu = lightSource.hdus[lightHduIndex];
  const kappaHdu = kappaSource.hdus[kappaHduIndex];
  if (!lightHdu?.supportedImage || !kappaHdu?.supportedImage) throw new Error("Select supported IMAGE HDUs for both files.");
  if (lightHdu.axes.length !== 2) throw new Error("The luminous proxy must be a 2D IMAGE HDU.");
  const wcs = compareFitsWcs(lightHdu, kappaHdu);
  if (wcs.status === "mismatch") throw new Error(wcs.message);
  const target = Math.min(128, lightHdu.axes[0], lightHdu.axes[1]);
  if (target < 16) throw new Error("The selected source grid is smaller than 16×16 pixels.");
  const planes = selectedPlanes(kappaHdu);
  const light = prepareLight(aggregatePlane(lightSource.buffer, lightHdu, 0, target));
  const models = planes.map((plane) => aggregatePlane(kappaSource.buffer, kappaHdu, plane, target));
  const [lightHash, kappaHash] = await Promise.all([sha256(lightSource.buffer), sha256(kappaSource.buffer)]);
  const product = auditEvidence({ mode: "observation", light, models });
  const sampling = "Non-overlapping area bins; each bin is exact when ≤64 source pixels, otherwise deterministic stratified means with at most 64 samples per cell.";
  const warnings = [
    wcs.message,
    `Browser grid is ${target}×${target}; full-resolution measurement must use the Python pipeline.`,
    ...(kappaHdu.axes[2] && kappaHdu.axes[2] > planes.length ? [`The κ cube contains ${kappaHdu.axes[2]} planes; ${planes.length} evenly spaced planes were audited in-browser.`] : []),
    ...product.warnings,
  ];
  const receipt: UploadReceipt = {
    schema: "lensaudit.upload-receipt/1",
    generatedUtc: new Date().toISOString(),
    light: assetReceipt("light", lightSource, lightHdu, lightHash),
    kappa: assetReceipt("kappa", kappaSource, kappaHdu, kappaHash),
    wcs,
    targetGrid: [target, target],
    aggregationMethod: sampling,
    selectedKappaPlanes: planes,
  };
  return { product: { ...product, warnings }, receipt };
}

export function formatHdu(hdu: FitsHdu): string {
  const dimensions = [...hdu.axes].reverse().join(" × ");
  return `HDU ${hdu.index} · ${hdu.name} · ${dimensions} · BITPIX ${hdu.bitpix}`;
}
