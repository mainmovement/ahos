/**
 * Land mask + Iran outline, decoded at runtime from the generated module.
 *
 * The mask is a 1-degree equirectangular grid (row 0 = 90°N, column 0 = 180°W) rasterised from
 * Natural Earth 1:50m land in scripts/generate-geo.mjs. It is used for:
 *   - the flat dot map (`mode="map"`),
 *   - the Iran highlight on the dot globe,
 *   - test assertions that known cities fall on land (`tests/mask.test.ts`).
 */

import {
  IRAN_RINGS,
  LAND_CELL_COUNT,
  LAND_RLE_B64,
  LAND_ROW_COUNTS,
  LAND_RUN_COUNT,
  MASK_H,
  MASK_W,
} from "./mask.generated";

export { IRAN_RINGS, LAND_CELL_COUNT, LAND_RUN_COUNT, MASK_H, MASK_W };

type Mask = {
  readonly width: number;
  readonly height: number;
  readonly cells: Uint8Array;
};

/** Base64 → bytes. Browser-safe (`atob`) and Node-safe (`Buffer`) via a single code path. */
function base64ToBytes(base64: string): Uint8Array {
  if (typeof atob === "function") {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }
  const buffer = Buffer.from(base64, "base64");
  return new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.byteLength);
}

let cached: Mask | null = null;

/** Decodes the run-length encoded land mask. Throws if the generated module is inconsistent. */
export function landMask(): Mask {
  if (cached) return cached;
  const bytes = base64ToBytes(LAND_RLE_B64);
  const cells = new Uint8Array(MASK_W * MASK_H);
  let index = 0;
  let value = 0;
  for (let bit = 0; bit + 32 <= bytes.length * 8; bit += 32) {
    let run = 0;
    for (let k = 0; k < 32; k++) {
      const byte = bytes[(bit + k) >> 3] ?? 0;
      run = run * 2 + ((byte >> (7 - ((bit + k) & 7))) & 1);
    }
    const end = Math.min(cells.length, index + run);
    if (value === 1) cells.fill(1, index, end);
    index = end;
    value = value === 0 ? 1 : 0;
    if (index >= cells.length) break;
  }
  let land = 0;
  for (let i = 0; i < cells.length; i++) land += cells[i] ?? 0;
  if (index !== cells.length || land !== LAND_CELL_COUNT) {
    throw new Error(
      `Land mask decode mismatch: filled ${index}/${cells.length} cells, ${land}/${LAND_CELL_COUNT} land cells`,
    );
  }
  cached = { width: MASK_W, height: MASK_H, cells };
  return cached;
}

/** True when the given lon/lat falls on a land cell of the 1° mask. */
export function isLand(lng: number, lat: number): boolean {
  const mask = landMask();
  const x = Math.floor(((lng + 180) / 360) * mask.width);
  const y = Math.floor(((90 - lat) / 180) * mask.height);
  if (y < 0 || y >= mask.height) return false;
  const wrapped = ((x % mask.width) + mask.width) % mask.width;
  return mask.cells[y * mask.width + wrapped] === 1;
}

/** Standard point-in-ring test (ray casting, lon/lat plane). */
export function pointInRing(ring: readonly (readonly [number, number])[], lng: number, lat: number): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const a = ring[i];
    const b = ring[j];
    if (!a || !b) continue;
    const intersects = a[1] > lat !== b[1] > lat && lng < ((b[0] - a[0]) * (lat - a[1])) / (b[1] - a[1]) + a[0];
    if (intersects) inside = !inside;
  }
  return inside;
}

/** True when the point falls inside the bundled Iran outline. */
export function isInIran(lng: number, lat: number): boolean {
  for (const ring of IRAN_RINGS) {
    if (pointInRing(ring, lng, lat)) return true;
  }
  return false;
}

export type MaskDot = {
  x: number;
  y: number;
  iran: boolean;
};

/**
 * Equirectangular dot grid: land cells become dots inside a `width x height` rectangle whose top-left
 * corner is at `(originX, originY)` of the surface they are drawn on (x: 180°W → 0, y: 90°N → 0).
 * The stride is chosen from the dot radius so dots breathe instead of smearing into a solid
 * rectangle (the failure mode the brief calls out).
 */
export function mapDots(
  width: number,
  height: number,
  dotRadius: number,
  originX = 0,
  originY = 0,
): MaskDot[] {
  const mask = landMask();
  const cellW = width / mask.width;
  const cellH = height / mask.height;
  const stride = Math.max(1, Math.ceil((dotRadius * 2.3) / Math.max(cellW, cellH)));
  const dots: MaskDot[] = [];
  const offset = Math.floor(stride / 2);
  for (let y = offset; y < mask.height; y += stride) {
    const lat = 90 - (y + 0.5) * (180 / mask.height);
    for (let x = offset; x < mask.width; x += stride) {
      if (mask.cells[y * mask.width + x] !== 1) continue;
      const lng = -180 + (x + 0.5) * (360 / mask.width);
      dots.push({
        x: originX + (x + 0.5) * cellW,
        y: originY + (y + 0.5) * cellH,
        iran: isInIran(lng, lat),
      });
    }
  }
  return dots;
}

/** Single SVG path with one round-capped tick per dot — far cheaper than thousands of <circle>. */
export function dotsPath(dots: readonly MaskDot[]): string {
  let path = "";
  for (const dot of dots) {
    path += `M${dot.x.toFixed(1)} ${dot.y.toFixed(1)}h0.01`;
  }
  return path;
}

/** Guard used by tests and dev tooling: the generated row histogram must match a fresh decode. */
export function maskRowCountsMatch(): boolean {
  const mask = landMask();
  if (LAND_ROW_COUNTS.length !== mask.height) return false;
  for (let y = 0; y < mask.height; y++) {
    let count = 0;
    for (let x = 0; x < mask.width; x++) count += mask.cells[y * mask.width + x] ?? 0;
    if (count !== LAND_ROW_COUNTS[y]) return false;
  }
  return true;
}
