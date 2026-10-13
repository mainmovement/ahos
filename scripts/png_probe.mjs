// Minimal PNG pixel probe: inflate the IDAT stream and undo the PNG filters,
// then report the colour distribution. Used to prove a screenshot is a real
// render and not a blank frame, because this agent cannot view images.
//
// node scripts/png_probe.mjs <file.png> [sampleStep]
import { readFileSync } from "node:fs";
import { inflateSync } from "node:zlib";

const file = process.argv[2];
const step = Number(process.argv[3] ?? 1);
const buf = readFileSync(file);

let pos = 8; // skip the PNG signature
let width = 0, height = 0, bitDepth = 0, colourType = 0;
const idat = [];
while (pos < buf.length) {
  const len = buf.readUInt32BE(pos); pos += 4;
  const type = buf.toString("ascii", pos, pos + 4); pos += 4;
  const data = buf.subarray(pos, pos + len); pos += len;
  pos += 4; // CRC
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

const channels = colourType === 2 ? 3 : colourType === 6 ? 4 : colourType === 0 ? 1 : 0;
if (channels === 0 || bitDepth !== 8) {
  console.error(`unsupported PNG: colourType=${colourType} bitDepth=${bitDepth}`);
  process.exit(2);
}

const raw = inflateSync(Buffer.concat(idat));

const stride = width * channels + 1; // +1 for the filter byte per scanline
const out = new Uint8Array(width * height * channels);
let prev = new Uint8Array(width * channels);

const counts = new Map();
for (let y = 0; y < height; y++) {
  const rowStart = y * stride;
  const f = raw[rowStart];
  const line = raw.subarray(rowStart + 1, rowStart + stride);
  const dst = out.subarray(y * width * channels, (y + 1) * width * channels);
  for (let x = 0; x < width * channels; x++) {
    const a = x >= channels ? dst[x - channels] : 0;
    const b = prev[x];
    const c = x >= channels ? prev[x - channels] : 0;
    const v = line[x];
    let p;
    switch (f) {
      case 0: p = v; break;
      case 1: p = (v + a) & 0xff; break;
      case 2: p = (v + b) & 0xff; break;
      case 3: p = (v + ((a + b) >> 1)) & 0xff; break;
      case 4: {
        const pp = a + b - c;
        const pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
        p = (v + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c)) & 0xff;
        break;
      }
      default: throw new Error(`bad filter ${f} at row ${y}`);
    }
    dst[x] = p;
  }
  prev = dst;
}

for (let y = 0; y < height; y += step) {
  for (let x = 0; x < width; x += step) {
    const i = (y * width + x) * channels;
    const key = channels === 3
      ? (out[i] << 16) | (out[i + 1] << 8) | out[i + 2]
      : (out[i] << 16) | (out[i + 1] << 8) | out[i + 2]; // ignore alpha for stats
    counts.set(key, (counts.get(key) || 0) + 1);
  }
}

const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
const hex = (n) => "#" + n.toString(16).padStart(6, "0");
console.log(`${file}: ${width}x${height} colourType=${colourType}`);
console.log(`distinct sampled colours: ${counts.size}`);
for (const [rgb, n] of top) console.log(`  ${hex(rgb)}  ${n}`);
