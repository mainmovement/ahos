/**
 * M-D6.4 QA — land-legibility statistics on a stage capture.
 *
 * `stage_luminance.mjs` answers "how hot is this spot"; this one answers the
 * opposite question, the one item 6 is about: at T1 there are a quarter as many
 * land dots over the same sphere, and the continents can fail to join up. The
 * 2550aae ramp was accepted as a PARTIAL win on exactly these numbers (T1: land
 * on 23.2% of the disc at a mean 40.6 lum, 4.84x over the dust, 27.1k
 * continent-core pixels above 25 lum), so they are the yardstick the cobe port
 * has to beat or match.
 *
 * "Land" here is the set of disc pixels clearly above the dust floor: the dust
 * field is a soft sprite at low opacity and its additive stacks stay near the
 * floor, while a land dot is a hard disc at a higher alpha, so a threshold on
 * the lit hemisphere separates them well enough for a comparison. The
 * terminator moves between captures, so the lit fraction is reported alongside
 * the counts rather than assumed constant.
 *
 * The default box is the *canvas band*, not the old globe box. M-D7's telemetry
 * strips shrank the canvas to x 15..1569, y 93..397, so the box this script and
 * `stage_luminance.mjs` inherited from M-D6.4 — 476,135,1109,731 — is 56% DOM
 * below the canvas, and DOM panels above L 25 were being counted as continent
 * core. The canvas is verifiable on any capture: its clear colour is #0B0709,
 * rgb(11,7,9), so probing a canvas corner reads exactly that. Measure the band,
 * not the disc — the band is the same from capture to capture, where a
 * tight disc box has to be re-found as the layout moves.
 *
 * Run:
 *   node scripts/land_legibility.mjs <png> [png ...] [--box x0,y0,x1,y1]
 *
 * Reads PNGs only. Never touches .env, tokens, or any authority surface.
 */
import sharp from "sharp";

/** The canvas band, verified by the #0B0709 clear colour at its corners. */
const DEFAULT_BOX = { x0: 15, y0: 93, x1: 1569, y1: 397 };
/** The 2550aae continent-core threshold, reused so the numbers compare. */
const CORE_LUM = 25;
/** The dust floor, measured on a dust-only capture; below this is body/night. */
const DUST_FLOOR_LUM = 8;

const luminance = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

const args = process.argv.slice(2);
if (!args.length) {
  console.error("usage: node scripts/land_legibility.mjs <png> [png ...] [--box x0,y0,x1,y1]");
  process.exit(2);
}

const boxArg = args.findIndex((a) => a === "--box");
let box = DEFAULT_BOX;
if (boxArg >= 0) {
  const [x0, y0, x1, y1] = args[boxArg + 1].split(",").map(Number);
  box = { x0, y0, x1, y1 };
}
const pngs = args.filter((a, i) => a !== "--box" && !(boxArg >= 0 && i === boxArg + 1));

for (const png of pngs) {
  const { data, info } = await sharp(png).raw().toBuffer({ resolveWithObject: true });
  const ch = info.channels;
  const at = (x, y) => {
    const o = (y * info.width + x) * ch;
    return [data[o], data[o + 1], data[o + 2]];
  };

  let lit = 0;          // above the dust floor at all: the lit hemisphere
  let core = 0;         // the continent-core threshold
  let coreSum = 0;      // luminance sum over core pixels
  const hist = new Map();
  for (let y = box.y0; y <= box.y1; y++) {
    for (let x = box.x0; x <= box.x1; x++) {
      const [r, g, b] = at(x, y);
      const L = luminance(r, g, b);
      if (L < DUST_FLOOR_LUM) continue;
      lit++;
      if (L >= CORE_LUM) {
        core++;
        coreSum += L;
        const band = Math.floor(L / 25) * 25;
        hist.set(band, (hist.get(band) ?? 0) + 1);
      }
    }
  }

  const litPct = (100 * lit) / ((box.x1 - box.x0) * (box.y1 - box.y0));
  const meanCore = core ? coreSum / core : 0;
  const bands = [...hist.entries()].sort((a, b) => a[0] - b[0]);

  console.log(`${png}  (${info.width}x${info.height})  box ${box.x0},${box.y0},${box.x1},${box.y1}`);
  console.log(`  lit pixels (L>=${DUST_FLOOR_LUM}):  ${lit}  (${litPct.toFixed(1)}% of the box)`);
  console.log(`  continent core (L>=${CORE_LUM}):    ${core}  mean L=${meanCore.toFixed(1)}`);
  console.log(`  core share of lit:                  ${(core ? (100 * core) / lit : 0).toFixed(1)}%`);
  console.log(`  bands: ${bands.map(([band, n]) => `${band}:${n}`).join(" ")}`);
}
