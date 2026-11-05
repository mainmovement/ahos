/**
 * Generates the stylized Earth land-mask used by the 3D globe.
 *
 * Reads the public-domain Natural Earth land topology from the `world-atlas`
 * npm package (build-time only), rasterizes it to a 256×128 bitmask, and emits
 * a compact base64 TS module. Runtime never touches this script or network.
 *
 * Usage: npm run gen:earth
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const W = 256;
const H = 128;

const topo = JSON.parse(
  readFileSync(new URL("../node_modules/world-atlas/land-110m.json", import.meta.url), "utf8"),
);

const { scale, translate } = topo.transform;
const arcs = topo.arcs.map((arc) => {
  let x = 0;
  let y = 0;
  return arc.map(([dx, dy]) => {
    x += dx;
    y += dy;
    return [(x * scale[0] + translate[0]), (y * scale[1] + translate[1])];
  });
});

function ringPoints(indices) {
  const pts = [];
  for (const idx of indices) {
    let a = idx < 0 ? [...arcs[~idx]].reverse() : arcs[idx];
    if (pts.length > 0) a = a.slice(1);
    pts.push(...a);
  }
  return pts;
}

const polygons = [];
const geometries = topo.objects.land.geometries ?? [topo.objects.land];
for (const geom of geometries) {
  if (geom.type === "MultiPolygon") {
    for (const poly of geom.arcs) polygons.push(poly.map(ringPoints));
  } else if (geom.type === "Polygon") {
    polygons.push(geom.arcs.map(ringPoints));
  }
}

// Convert lon/lat rings to pixel-space edges.
const edges = [];
for (const poly of polygons) {
  for (const ring of poly) {
    for (let i = 0; i < ring.length - 1; i += 1) {
      const [lon1, lat1] = ring[i];
      const [lon2, lat2] = ring[i + 1];
      const x1 = ((lon1 + 180) / 360) * W;
      const y1 = ((90 - lat1) / 180) * H;
      const x2 = ((lon2 + 180) / 360) * W;
      const y2 = ((90 - lat2) / 180) * H;
      if (y1 !== y2) edges.push([x1, y1, x2, y2]);
    }
  }
}

const mask = new Uint8Array(W * H);
for (let y = 0; y < H; y += 1) {
  const py = y + 0.5;
  const crossings = [];
  for (const [x1, y1, x2, y2] of edges) {
    if (y1 <= py !== y2 <= py) {
      crossings.push(x1 + ((py - y1) * (x2 - x1)) / (y2 - y1));
    }
  }
  crossings.sort((a, b) => a - b);
  for (let c = 0; c + 1 < crossings.length; c += 2) {
    const x0 = Math.max(0, Math.floor(crossings[c]));
    const x1 = Math.min(W - 1, Math.ceil(crossings[c + 1]));
    for (let x = x0; x <= x1; x += 1) {
      const cx = x + 0.5;
      if (cx >= crossings[c] && cx <= crossings[c + 1]) mask[y * W + x] = 1;
    }
  }
}

// Pack bits, MSB first.
const packed = Buffer.alloc(Math.ceil((W * H) / 8));
mask.forEach((bit, i) => {
  if (bit) packed[i >> 3] |= 0x80 >> (i & 7);
});

let landCount = 0;
for (const bit of mask) landCount += bit;
const ratio = ((landCount / (W * H)) * 100).toFixed(1);
console.log(`land coverage: ${landCount}/${W * H} px (${ratio}%) — expected ~29%`);

const ts = `/**
 * GENERATED FILE — do not edit by hand. Run \`npm run gen:earth\`.
 * Rasterized Natural Earth land mask (public domain, 110m) for the
 * command-deck globe. Build-time artifact; no runtime data source.
 */
export const EARTH_MASK = {
  width: ${W},
  height: ${H},
  base64: "${packed.toString("base64")}",
} as const;

export function decodeEarthMask(): Uint8Array {
  const bin = Buffer.from(EARTH_MASK.base64, "base64");
  return new Uint8Array(bin.buffer, bin.byteOffset, bin.byteLength);
}

/** true = land at integer pixel (x: 0..W-1 left→right from −180°, y: 0..H-1 top→bottom from 90°N). */
export function isLand(x: number, y: number, mask: Uint8Array): boolean {
  const xi = ((x % EARTH_MASK.width) + EARTH_MASK.width) % EARTH_MASK.width;
  const yi = Math.min(EARTH_MASK.height - 1, Math.max(0, y));
  const idx = yi * EARTH_MASK.width + xi;
  return ((mask[idx >> 3] ?? 0) & (0x80 >> (idx & 7))) !== 0;
}
`;

mkdirSync(new URL("../components/visualization/globe/", import.meta.url), { recursive: true });
writeFileSync(new URL("../components/visualization/globe/earth-mask.ts", import.meta.url), ts);
console.log("wrote components/visualization/globe/earth-mask.ts");
