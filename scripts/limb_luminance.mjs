/**
 * M-D6.4 QA — the atmosphere's limb, measured as a luminance profile.
 *
 * `stage_luminance.mjs` finds the hottest pixels anywhere in the globe box, which
 * answers "is anything overblown?" but not "is the edge a gradient or a painted
 * ring?" — and the latter is the whole question for a fresnel shell, because a
 * constant-brightness annulus and a genuine gradient can both peak at the same
 * value. This script walks one horizontal scan row across the globe and prints the
 * luminance at fixed offsets from each silhouette edge, so the shell's *shape* is
 * in the report and not just its height.
 *
 * Method, matching the M-D6.4 receipt: the edge is found on the scan row as the
 * outermost clearly-lit pixel of the globe's own contiguous lit run, the local
 * background is read 22 px *clear* of it (outside the shell, where nothing of the
 * globe can reach), and every number is that background subtracted. Reading the
 * background per file is what keeps two page loads comparable — the sun moves
 * between them and relights the dust, so an absolute value would carry that.
 *
 * Run:
 *   node scripts/limb_luminance.mjs <png> [png ...]           default row y = 433
 *   node scripts/limb_luminance.mjs <png> --row 400           another scan row
 *
 * Reads PNGs only. Never touches .env, tokens, or any authority surface.
 */
import sharp from "sharp";

const args = process.argv.slice(2);
const rowArg = args.findIndex((a) => a === "--row");
let row = 433;   // the M-D6.4 disc's vertical centre, per the receipt's measured box
if (rowArg >= 0) {
  row = Number(args[rowArg + 1]);
  args.splice(rowArg, 2);
}
const files = args.filter((a) => !a.startsWith("--"));
if (!files.length) {
  console.error("usage: node scripts/limb_luminance.mjs <png> [png ...] [--row y]");
  process.exit(2);
}

const luminance = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  return s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2;
};

// Offsets from the silhouette edge, in pixels. Negative is outward (the shell),
// positive is inward (over the body, which the shell draws on top of).
const OFFSETS = [-24, -20, -16, -12, -8, -4, -2, 0, 2, 4];

for (const file of files) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const ch = info.channels;
  const at = (x, y) => {
    const o = (y * info.width + x) * ch;
    return [data[o], data[o + 1], data[o + 2]];
  };
  if (row < 0 || row >= info.height) {
    console.log(`${file}: row ${row} out of range (${info.height} px tall)`);
    continue;
  }

  // Luminance along the whole scan row.
  const lum = new Array(info.width);
  for (let x = 0; x < info.width; x++) {
    const [r, g, b] = at(x, row);
    lum[x] = luminance(r, g, b);
  }

  // A background from both far ends of the row — outside the disc entirely, so it
  // is whatever the stage's own backdrop is at this height, not the globe.
  const farLeft = lum.slice(8, 120);
  const farRight = lum.slice(-120, -8);
  const bg = median([...farLeft, ...farRight]);

  // The globe's lit run: walk in from each edge of the frame and stop where the
  // row stops being clearly lit. The dust hugs the body, so the outermost lit
  // pixel is the shell's limb rather than the lacquer's silhouette — which is what
  // we want to measure, but it means "the silhouette" below is the shell's.
  const LIT = bg + 15;
  let left = 0;
  for (let x = 0; x < info.width; x++) {
    if (lum[x] > LIT) { left = x; break; }
  }
  let right = info.width - 1;
  for (let x = info.width - 1; x >= 0; x--) {
    if (lum[x] > LIT) { right = x; break; }
  }

  // The background 22 px clear of each edge, read over a 9 px neighbourhood so a
  // single bright speck of dust does not set it.
  const localBg = (edge, dir) => {
    const c = edge + dir * 22;
    const vals = [];
    for (let dx = -4; dx <= 4; dx++) {
      const x = c + dx;
      if (x >= 0 && x < info.width) vals.push(lum[x]);
    }
    return median(vals);
  };

  const leftBg = localBg(left, -1);
  const rightBg = localBg(right, +1);

  console.log(`${file}  row y = ${row}  (${info.width}x${info.height})`);
  console.log(`  backdrop ${bg.toFixed(1)} | lit run x ${left}..${right} (${right - left + 1} px)`);
  console.log(`  local background, 22 px clear: left ${leftBg.toFixed(1)}, right ${rightBg.toFixed(1)}`);

  for (const [name, edge, bgg, dir] of [["left", left, leftBg, -1], ["right", right, rightBg, +1]]) {
    const profile = OFFSETS.map((o) => {
      const x = edge + o * -dir;   // negative offsets go outward
      if (x < 0 || x >= info.width) return { o, v: null };
      return { o, v: lum[x] - bgg };
    });
    const valid = profile.filter((p) => p.v !== null);
    const peak = valid.reduce((a, b) => (b.v > a.v ? b : a));
    const inside = valid.filter((p) => p.o >= 0);
    const innermost = inside.length ? inside.reduce((a, b) => (b.v > a.v ? b : a)) : { o: null, v: null };
    console.log(
      `  ${name} edge x = ${edge} | peak above bg ${peak.v.toFixed(1)} at offset ${peak.o}`
      + ` | innermost (o=+4) ${innermost.v === null ? "n/a" : innermost.v.toFixed(1)}`
    );
    console.log("    offset (px, - = outward):  " + valid.map((p) => `${p.o}`.padStart(6)).join(""));
    console.log(
      "    luminance above local bg:  "
      + valid.map((p) => (p.v >= 0 ? " " : "") + Math.round(p.v).toString().padStart(5)).join("")
    );
    // A painted annulus is flat: the band stays near its peak across its width.
    // A fresnel shell falls off outward, so the outer samples should be well below
    // the peak. This ratio is the shape, in one number.
    const out12 = valid.find((p) => p.o === -12);
    if (out12 && peak.v > 0) {
      console.log(`    outer/peak ratio at o=-12: ${(out12.v / peak.v).toFixed(2)}  (1.0 = flat annulus, <1 = graded)`);
    }
  }
}
