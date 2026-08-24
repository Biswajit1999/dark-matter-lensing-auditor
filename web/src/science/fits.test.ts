import { describe, expect, it, vi } from "vitest";
import { analyzeFitsPair, compareFitsWcs, loadFitsFile, parseFitsHdus } from "./fits";

const BLOCK = 2880;

function card(key: string, value?: string): string {
  const text = value === undefined ? key : `${key.padEnd(8)}= ${value}`;
  return text.padEnd(80, " ").slice(0, 80);
}

function fitsBuffer(width: number, height: number, planes = 1, options: { crpix1?: number; includeWcs?: boolean } = {}): ArrayBuffer {
  const includeWcs = options.includeWcs ?? true;
  const cards = [
    card("SIMPLE", "T"), card("BITPIX", "-32"), card("NAXIS", planes > 1 ? "3" : "2"),
    card("NAXIS1", String(width)), card("NAXIS2", String(height)),
    ...(planes > 1 ? [card("NAXIS3", String(planes))] : []),
    card("BUNIT", "'dimensionless'"),
    ...(includeWcs ? [
      card("CTYPE1", "'RA---TAN'"), card("CTYPE2", "'DEC--TAN'"),
      card("CRPIX1", String(options.crpix1 ?? width / 2)), card("CRPIX2", String(height / 2)),
      card("CRVAL1", "3.5"), card("CRVAL2", "-30.4"),
      card("CDELT1", "-1.0E-4"), card("CDELT2", "1.0E-4"),
    ] : []),
    card("END"),
  ];
  const headerText = cards.join("").padEnd(Math.ceil(cards.length * 80 / BLOCK) * BLOCK, " ");
  const pixels = width * height * planes;
  const dataBytes = pixels * 4;
  const buffer = new ArrayBuffer(headerText.length + Math.ceil(dataBytes / BLOCK) * BLOCK);
  const bytes = new Uint8Array(buffer);
  bytes.set(new TextEncoder().encode(headerText));
  const view = new DataView(buffer);
  for (let index = 0; index < pixels; index += 1) {
    const plane = Math.floor(index / (width * height));
    const local = index % (width * height);
    const x = local % width;
    const y = Math.floor(local / width);
    const value = Math.exp(-0.5 * (((x - width * 0.55 - plane * 0.2) / 3) ** 2 + ((y - height * 0.48) / 2.5) ** 2));
    view.setFloat32(headerText.length + index * 4, value, false);
  }
  return buffer;
}

function fileFrom(buffer: ArrayBuffer, name: string): File {
  return {
    name,
    size: buffer.byteLength,
    type: "application/fits",
    lastModified: 1,
    arrayBuffer: async () => buffer,
  } as File;
}

describe("browser FITS contract", () => {
  it("parses a primary 2D floating-point image HDU", () => {
    const hdus = parseFitsHdus(fitsBuffer(16, 20));
    expect(hdus).toHaveLength(1);
    expect(hdus[0].supportedImage).toBe(true);
    expect(hdus[0].axes).toEqual([16, 20]);
    expect(hdus[0].bitpix).toBe(-32);
    expect(hdus[0].header.CTYPE1).toBe("RA---TAN");
  });

  it("rejects a payload without the SIMPLE FITS signature", () => {
    expect(() => parseFitsHdus(new ArrayBuffer(BLOCK))).toThrow(/SIMPLE/);
  });

  it("distinguishes verified, unverified, and mismatched registration", () => {
    const verifiedLight = parseFitsHdus(fitsBuffer(16, 16))[0];
    const verifiedKappa = parseFitsHdus(fitsBuffer(16, 16, 3))[0];
    expect(compareFitsWcs(verifiedLight, verifiedKappa).status).toBe("verified");
    const noWcs = parseFitsHdus(fitsBuffer(16, 16, 1, { includeWcs: false }))[0];
    expect(compareFitsWcs(noWcs, verifiedKappa).status).toBe("unverified");
    const shifted = parseFitsHdus(fitsBuffer(16, 16, 1, { crpix1: 3 }))[0];
    expect(compareFitsWcs(shifted, verifiedKappa).status).toBe("mismatch");
  });

  it("audits a local light-plus-kappa ensemble and creates hashes", async () => {
    vi.spyOn(crypto.subtle, "digest").mockResolvedValue(new Uint8Array(32).fill(10).buffer);
    const light = await loadFitsFile(fileFrom(fitsBuffer(16, 16), "light.fits"));
    const kappa = await loadFitsFile(fileFrom(fitsBuffer(16, 16, 4), "kappa-cube.fits"));
    const result = await analyzeFitsPair(light, 0, kappa, 0);
    expect(result.product.mass.values).toHaveLength(16 * 16);
    expect(result.receipt.selectedKappaPlanes).toEqual([0, 1, 2, 3]);
    expect(result.receipt.light.sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(result.receipt.kappa.sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(result.receipt.wcs.status).toBe("verified");
  });
});
