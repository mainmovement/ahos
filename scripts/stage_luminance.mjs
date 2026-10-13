/**
 * M-D6.4 QA — measure luminance on a stage screenshot, at fixed pixels or as peaks.
 *
 * Why this exists: the glow-spot investigation kept being closed on visual guesses
 * that the owner's screenshots disproved, and one commit quoted luminance numbers
 * that did not match its own PNG. Reading the actual pixels removes the guesswork —
 * "the spot is gone" becomes a number at the same pixel in the before and after shot.
 *
 * Run:
 *   node scripts/stage_luminance.mjs <png>                     hottest peaks in the globe box
 *   node scripts/stage_luminance.mjs <png> x,y [x,y ...]       luminance + RGB at fixed pixels
 *   node scripts/stage_luminance.mjs <png> --box x0,y0,x1,y1   peaks inside a custom box
 *   node scripts/stage_luminance.mjs <png> --map              ASCII luminance map of the box
 *
 * Luminance is Rec. 601 (the value a dot's additive stacking actually raises). Peaks
 * are non-max-suppressed so one bloated highlight does not fill the whole report. The
 * ASCII map exists because a text session cannot look at the PNG: it turns "is this a
 * blob or a broad arc?" into something readable without eyes on the screenshot.
 *
 * Reads PNGs only. Never touches .env, tokens, or any authority surface.
 */
import sharp from "sharp";

const [, , png, ...rest] = process.argv;
if (!png) {
  console.error("usage: node scripts/stage_luminance.mjs <png> [x,y ...] [--box x0,y0,x1,y1]");
  process.exit(2);
}

const luminance = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

const boxArg = rest.findIndex((a) => a === "--box");
let box = { x0: 476, y0: 135, x1: 1109, y1: 731 };   // the globe box from M-D6.4's README
if (boxArg >= 0) {
  const [x0, y0, x1, y1] = rest[boxArg + 1].split(",").map(Number);
  box = { x0, y0, x1, y1 };
}
const probes = rest
  .filter((a, i) => a !== "--box" && a !== "--map" && !(boxArg >= 0 && i === boxArg + 1))
  .map((p) => {
  const [x, y] = p.split(",").map(Number);
  return { x, y };
});

const { data, info } = await sharp(png).raw().toBuffer({ resolveWithObject: true });
const channels = info.channels;
const at = (x, y) => {
  const o = (y * info.width + x) * channels;
  return [data[o], data[o + 1], data[o + 2]];
};

if (probes.length) {
  console.log(`${png}  (${info.width}x${info.height})`);
  for (const { x, y } of probes) {
    if (x < 0 || y < 0 || x >= info.width || y >= info.height) {
      console.log(`  (${x},${y})  OUT OF RANGE`);
      continue;
    }
    const [r, g, b] = at(x, y);
    console.log(`  (${x},${y})  L=${luminance(r, g, b).toFixed(1)}  rgb(${r},${g},${b})`);
  }
  process.exit(0);
}

const w = info.width;
const h = info.height;
const lum = new Float32Array(w * h);
for (let y = 0; y < h; y++) {
  for (let x = 0; x < w; x++) {
    const [r, g, b] = at(x, y);
    lum[y * w + x] = luminance(r, g, b);
  }
}

if (rest.includes("--map")) {
  const COLS = 118;
  const ROWS = 52;
  const bands = [" ", ".", ":", "-", "+", "*", "o", "#", "@"];
  const bandOf = (v) => (v < 2 ? 0 : v < 8 ? 1 : v < 16 ? 2 : v < 30 ? 3 : v < 48 ? 4 : v < 75 ? 5 : v < 110 ? 6 : v < 165 ? 7 : 8);
  const bw = box.x1 - box.x0;
  const bh = box.y1 - box.y0;
  const cw = Math.max(1, Math.round(bw / COLS));
  const ch = Math.max(1, Math.round(bh / ROWS));
  const cols = Math.ceil(bw / cw);
  const rows = Math.ceil(bh / ch);
  let out = `${png}  (${w}x${h})  map of box ${box.x0},${box.y0},${box.x1},${box.y1}  cell ${cw}x${ch}px\n`;
  out += `luminance: ' '<2 '.'<8 ':'<16 '-'<30 '+'<48 '*'<75 'o'<110 '#'<165 '@'>=165\n`;
  for (let ry = 0; ry < rows; ry++) {
    let line = "";
    for (let cx = 0; cx < cols; cx++) {
      let sum = 0;
      let n = 0;
      for (let y = box.y0 + ry * ch; y < Math.min(box.y0 + (ry + 1) * ch, box.y1 + 1); y++) {
        for (let x = box.x0 + cx * cw; x < Math.min(box.x0 + (cx + 1) * cw, box.x1 + 1); x++) {
          if (x < 0 || y < 0 || x >= w || y >= h) continue;
          sum += lum[y * w + x];
          n++;
        }
      }
      line += bands[bandOf(n ? sum / n : 0)];
    }
    out += line + "\n";
  }
  console.log(out);
  process.exit(0);
}
const R = 8;
const smooth = new Float32Array(w * h);
for (let y = 0; y < h; y++) {
  for (let x = 0; x < w; x++) {
    let sum = 0;
    let n = 0;
    for (let dy = -R; dy <= R; dy++) {
      for (let dx = -R; dx <= R; dx++) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        sum += lum[ny * w + nx];
        n++;
      }
    }
    smooth[y * w + x] = sum / n;
  }
}

const inBox = (x, y) => x >= box.x0 && x <= box.x1 && y >= box.y0 && y <= box.y1;
const picked = [];
const SUPPRESS = 48;
for (let i = 0; i < 12; i++) {
  let best = -1;
  let bx = 0;
  let by = 0;
  for (let y = box.y0; y <= box.y1; y++) {
    for (let x = box.x0; x <= box.x1; x++) {
      const v = smooth[y * w + x];
      if (v <= best) continue;
      if (picked.some((p) => Math.abs(p.x - x) < SUPPRESS && Math.abs(p.y - y) < SUPPRESS)) continue;
      // require a genuine local maximum, not a flat plateau edge
      const c = smooth[y * w + x];
      let isMax = true;
      for (let dy = -2; dy <= 2 && isMax; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
          if (smooth[(y + dy) * w + (x + dx)] > c) { isMax = false; break; }
        }
      }
      if (!isMax) continue;
      best = v;
      bx = x;
      by = y;
    }
  }
  if (best < 0) break;
  picked.push({ x: bx, y: by, v: best });
}

console.log(`${png}  (${w}x${h})  peaks in box ${box.x0},${box.y0},${box.x1},${box.y1}`);
for (const { x, y, v } of picked) {
  const [r, g, b] = at(x, y);
  console.log(`  (${x},${y})  L=${v.toFixed(1)}  rgb(${r},${g},${b})`);
}
void inBox;
