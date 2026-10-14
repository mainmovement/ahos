// Crown-blowout probe: where do the brightest warm pixels cluster, and how
// saturated are they? A blow-out hot patch at the globe's crown reads as a
// tight cluster of near-white-gold pixels (R high, G high, B clearly lower,
// luminance near the top of the range). A healthy lit crown may be warm, but
// not blown: its warm pixels stay well under near-white.
//
// This exists because this agent cannot view images and GLOBE_MEMORY floor #2
// is stated as a measurement, not a look: "a saturated gold disc at the top of
// the globe". Nothing here edits anything.
//
// node scripts/probe_crown.mjs <file.png>
import { readFileSync } from "node:fs";
import { inflateSync } from "node:zlib";

const file = process.argv[2];
const buf = readFileSync(file);

let pos = 8;
let width = 0, height = 0, bitDepth = 0, colourType = 0;
const idat = [];
while (pos < buf.length) {
  const len = buf.readUInt32BE(pos);
  pos += 4;
  const type = buf.toString("ascii", pos, pos + 4);
  pos += 4;
  const data = buf.subarray(pos, pos + len);
  pos += len;
  pos += 4;
  if (type === "IHDR") {
    width = data.readUInt32BE(0);
    height = data.readUInt32BE(4);
    bitDepth = data[8];
    colourType = data[9];
  } else if (type === "IDAT") {
    idat.push(data);
  } else if (type === "IEND") {
    break;
  }
}
const channels = colourType === 2 ? 3 : colourType === 6 ? 4 : 0;
if (channels === 0 || bitDepth !== 8) {
  console.error(`unsupported PNG: colourType=${colourType} bitDepth=${bitDepth}`);
  process.exit(2);
}
const raw = inflateSync(Buffer.concat(idat));
const stride = width * channels + 1;
const out = new Uint8Array(width * height * channels);
let prev = new Uint8Array(width * channels);
for (let y = 0; y < height; y++) {
  const rowStart = y * stride;
  const f = raw[rowStart];
  const line = raw.subarray(rowStart + 1, rowStart + stride);
  const dst = out.subarray(y * width * channels, (y + 1) * width * channels);
  for (let x = 0; x < width * channels; x++) {
    const a = line[x] ?? 0;
    const b = prev[x] ?? 0;
    const c = x >= channels ? dst[x - channels] ?? 0 : 0;
    let v = 0;
    if (f === 0) v = a;
    else if (f === 1) v = (a + b) & 255;
    else if (f === 2) v = (a + c) & 255;
    else if (f === 3) v = (a + ((b + c) >> 1)) & 255;
    else if (f === 4) {
      const p = b + c;
      const pa = Math.abs(p - (b << 1));
      const pb = Math.abs(p - (c << 1));
      const pc = Math.abs(p - ((b + c) << 1));
      v = (a + (pa <= pb && pa <= pc ? b : pb <= pc ? c : 0)) & 255;
    }
    dst[x] = v;
  }
  prev = dst;
}

/** Near-white warm: the blow-out signature. R leads, G close behind, B low. */
const isBlown = (r, g, b) => r >= 225 && g >= 180 && b <= 160 && r - b >= 90;
/** Any warm gold pixel, for the overall field. */
const isGold = (r, g, b) => r >= 120 && r > g && g > b && r - b >= 40;

let blown = 0;
let gold = 0;
let sx = 0, sy = 0;
let bx0 = width, bx1 = 0, by0 = height, by1 = 0;
let gx0 = width, gx1 = 0, gy0 = height, gy1 = 0;

for (let y = 0; y < height; y++) {
  for (let x = 0; x < width; x++) {
    const i = (y * width + x) * channels;
    const r = out[i], g = out[i + 1], b = out[i + 2];
    if (isGold(r, g, b)) {
      gold++;
      if (x < gx0) gx0 = x;
      if (x > gx1) gx1 = x;
      if (y < gy0) gy0 = y;
      if (y > gy1) gy1 = y;
    }
    if (isBlown(r, g, b)) {
      blown++;
      sx += x; sy += y;
      if (x < bx0) bx0 = x;
      if (x > bx1) bx1 = x;
      if (y < by0) by0 = y;
      if (y > by1) by1 = y;
    }
  }
}

console.log(`${file}: ${width}x${height}`);
console.log(`gold field: ${gold} px, bbox x[${gx0},${gx1}] y[${gy0},${gy1}]`);
if (blown > 0) {
  console.log(`BLOWN warm px: ${blown}, centroid (${Math.round(sx / blown)}, ${Math.round(sy / blown)}), bbox x[${bx0},${bx1}] y[${by0},${by1}]`);
} else {
  console.log("BLOWN warm px: 0 — no near-white-gold cluster anywhere");
}

// A blow-out is a *cluster*, not a sprinkle: diffuse warm text spreads evenly,
// a saturated disc piles into one cell. 64px cells, report the densest few.
const CELL = 64;
const cols = Math.ceil(width / CELL);
const rows = Math.ceil(height / CELL);
const cells = new Int32Array(cols * rows);
for (let y = 0; y < height; y++) {
  for (let x = 0; x < width; x++) {
    const i = (y * width + x) * channels;
    const r = out[i], g = out[i + 1], b = out[i + 2];
    if (isBlown(r, g, b)) cells[Math.floor(y / CELL) * cols + Math.floor(x / CELL)]++;
  }
}
const order = [...cells.entries()].sort((a, b) => b[1] - a[1]);
console.log("densest 64px cells (count, x, y):");
for (const [idx, n] of order.slice(0, 6)) {
  const cx = (idx % cols) * CELL;
  const cy = Math.floor(idx / cols) * CELL;
  console.log(`  ${String(n).padStart(6)}  @(${cx},${cy})`);
}
const top = order[0]?.[1] ?? 0;
const mean = blown / Math.max(1, cells.length);
console.log(`hottest cell ${top} px vs mean ${mean.toFixed(1)} per cell — ratio ${(top / Math.max(0.1, mean)).toFixed(1)}x`);
