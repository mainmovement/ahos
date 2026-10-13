/**
 * M-D6.7 QA — the globe's glow blobs, found and measured rather than eyeballed.
 *
 * The M-D6.4 hunt removed the hot spots it could attribute — the clearcoat
 * specular (04da79f) and the land layer's additive stacking at the silhouette
 * (4f51c21) — but owner QA keeps reopening "there are still white/orange blobs".
 * Eyeballing a capture cannot settle it: a blob is a *local* bright region, and
 * the eye has no threshold, so this script supplies one.
 *
 * Method. The globe's lit disc is located by its bounding box of
 * above-background pixels. Inside that box only, luminance is thresholded (the
 * default 150 is below the cobe port's own accepted dense-coastline peak of
 * ~185 and above gold in full day, so what it flags is brighter than any
 * legitimate single-layer gold), the surviving pixels are connected-component
 * labelled 4-way, and each component is reported with its peak luminance, its
 * centroid and its size. Colour is classified, because the two complaints are
 * different colours: `white` is saturation (blue near red/green, which gold
 * never is) and `orange` is a warm shift with blue suppressed (gold is already
 * warm, so only a *further* shift counts).
 *
 * What this is not: it is not a verdict on beauty. A dense day-side coastline is
 * allowed to be bright; the atmosphere's limb is allowed to be bright. What is
 * not allowed is a compact region that outshines everything around it — which
 * is the shape of a blob, and the shape the eye keeps catching.
 *
 * Run:
 *   node scripts/globe_blobs.mjs <png> [png ...] [--threshold 150] [--min-px 12]
 *
 * Reads PNGs only. Never touches .env, tokens, or any authority surface.
 */
import sharp from "sharp";

const args = process.argv.slice(2);
let threshold = 150;
let minPx = 12;
{
  const t = args.findIndex((a) => a === "--threshold");
  if (t >= 0) {
    threshold = Number(args[t + 1]);
    args.splice(t, 2);
  }
  const m = args.findIndex((a) => a === "--min-px");
  if (m >= 0) {
    minPx = Number(args[m + 1]);
    args.splice(m, 2);
  }
}
const files = args.filter((a) => !a.startsWith("--"));
if (!files.length) {
  console.error("usage: node scripts/globe_blobs.mjs <png> [png ...] [--threshold N] [--min-px N]");
  process.exit(2);
}

const luminance = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

/**
 * Classify a blob's colour. Gold (#D4AF5A) is r > g > b with b well under g, so
 * the two complaints need distinct signatures: white means b has risen to meet
 * r and g (additive saturation), orange means the g/b spread has *widened*
 * past gold's (a warmer light source than the brand colour).
 */
function classify(r, g, b) {
  const rg = r - g;
  const gb = g - b;
  if (b > r - 22 && b > g - 22) return "white";
  if (rg > gb * 1.7 + 14) return "orange";
  return "gold";
}

for (const file of files) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const ch = info.channels;
  const W = info.width;
  const H = info.height;
  const px = (x, y) => {
    const o = (y * W + x) * ch;
    return [data[o], data[o + 1], data[o + 2]];
  };
  const lum = (x, y) => luminance(...px(x, y));

  // The page background, from a corner nothing renders into.
  const corner = [lum(3, 3), lum(W - 4, 3), lum(3, H - 4), lum(W - 4, H - 4)];
  const bg = corner.reduce((a, b) => a + b, 0) / corner.length;

  // The globe's own disc, not the whole lit page. The chrome is bright too — the
  // topbar and the telemetry strips — but they are wide and short while a globe
  // is as tall as it is wide, so the disc is the largest near-square lit
  // component that the page centres horizontally. The dust field is sparse at the
  // low tiers and the atmosphere's halo is faint, so the disc is sought at a
  // lower threshold than the blobs are measured at — anything tighter fragments
  // a T1 globe into dust and halo and finds no disc at all.
  const lit = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (lum(x, y) - bg > 15) lit[y * W + x] = 1;
    }
  }
  const seenBox = new Uint8Array(W * H);
  let best = null;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      if (!lit[y * W + x] || seenBox[y * W + x]) continue;
      const stack = [[x, y]];
      seenBox[y * W + x] = 1;
      let bx0 = x, by0 = y, bx1 = x, by1 = y;
      while (stack.length) {
        const [cx, cy] = stack.pop();
        bx0 = Math.min(bx0, cx);
        bx1 = Math.max(bx1, cx);
        by0 = Math.min(by0, cy);
        by1 = Math.max(by1, cy);
        for (const [nx, ny] of [[cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1]]) {
          if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
          const ni = ny * W + nx;
          if (!lit[ni] || seenBox[ni]) continue;
          seenBox[ni] = 1;
          stack.push([nx, ny]);
        }
      }
      const bw = bx1 - bx0 + 1;
      const bh = by1 - by0 + 1;
      const aspect = bw / bh;
      const midX = (bx0 + bx1) / 2;
      const centred = Math.abs(midX - W / 2) < W * 0.18;
      // A disc is near-square; the atmosphere's halo thins it slightly at the
      // limb, so allow down to 0.6. Anything wider than 1.5 is a strip.
      if (!centred || aspect < 0.6 || aspect > 1.5 || bw < 140) continue;
      if (!best || bw * bh > best.bw * best.bh) {
        best = { x0: bx0, y0: by0, x1: bx1, y1: by1, w: bw, h: bh };
      }
    }
  }
  if (!best) {
    console.log(`${file}: no globe disc found`);
    continue;
  }
  const x0 = best.x0, y0 = best.y0, x1 = best.x1, y1 = best.y1;

  // Connected components over the threshold, inside the globe box only. Outside
  // it, a bright pixel belongs to the chrome, not the globe.
  const seen = new Uint8Array((x1 - x0 + 1) * (y1 - y0 + 1));
  const blobs = [];
  for (let y = y0; y <= y1; y++) {
    for (let x = x0; x <= x1; x++) {
      const i = (y - y0) * (x1 - x0 + 1) + (x - x0);
      if (seen[i]) continue;
      if (lum(x, y) < threshold) continue;
      // 4-way flood fill.
      const stack = [[x, y]];
      seen[i] = 1;
      let n = 0, sx = 0, sy = 0, peak = 0;
      let cr = 0, cg = 0, cb = 0;
      while (stack.length) {
        const [cx, cy] = stack.pop();
        n++;
        sx += cx;
        sy += cy;
        const [pr, pg, pb] = px(cx, cy);
        cr += pr;
        cg += pg;
        cb += pb;
        const l = luminance(pr, pg, pb);
        if (l > peak) peak = l;
        const nb = [
          [cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1],
        ];
        for (const [nx, ny] of nb) {
          if (nx < x0 || nx > x1 || ny < y0 || ny > y1) continue;
          const ni = (ny - y0) * (x1 - x0 + 1) + (nx - x0);
          if (seen[ni]) continue;
          if (lum(nx, ny) < threshold) continue;
          seen[ni] = 1;
          stack.push([nx, ny]);
        }
      }
      if (n < minPx) continue;
      blobs.push({
        px: n,
        peak,
        mean: Math.round(luminance(cr / n, cg / n, cb / n)),
        cx: Math.round(sx / n),
        cy: Math.round(sy / n),
        kind: classify(Math.round(cr / n), Math.round(cg / n), Math.round(cb / n)),
      });
    }
  }
  blobs.sort((a, b) => b.peak - a.peak);

  const box = { x0, y0, x1, y1, w: x1 - x0 + 1, h: y1 - y0 + 1 };
  console.log(`${file}`);
  console.log(`  globe disc ${box.w}x${box.h} at (${x0},${y0})  bg L=${bg.toFixed(1)}  threshold ${threshold}`);
  if (!blobs.length) {
    console.log("  no blobs above threshold");
    continue;
  }
  for (const b of blobs.slice(0, 12)) {
    const relX = ((b.cx - x0) / box.w * 100).toFixed(0);
    const relY = ((b.cy - y0) / box.h * 100).toFixed(0);
    console.log(`  ${b.kind.padEnd(6)} peak L=${b.peak.toFixed(0).padStart(3)} mean L=${b.mean} ${b.px}px at (${b.cx},${b.cy}) = ${relX}%x ${relY}%y of the box`);
  }
  const kinds = [...new Set(blobs.map((b) => b.kind))];
  console.log(`  total ${blobs.length} blob(s): ${kinds.join(", ")}`);
}
