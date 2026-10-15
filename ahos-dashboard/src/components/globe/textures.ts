/**
 * Procedural globe textures (canvas 2D, fully offline):
 *   day   — navy ocean with latitude gradient, dark land, gold coastlines, graticule
 *   night — warm city-light clusters + inter-city "roads", clipped to land
 *   mask  — land (white) / ocean (black) for ocean specular
 * CPU canvases are cached per quality so remounting the globe is instant;
 * GPU textures are created per mount and disposed on unmount.
 */
import { geoEquirectangular, geoGraticule10, geoPath } from "d3-geo";
import type { Feature, Geometry } from "geojson";
import { CITY_LIGHTS } from "./city-lights";
import { loadCountries, loadLand, type LandDetail } from "./geo-data";

export interface GlobeCanvases {
  day: HTMLCanvasElement;
  night: HTMLCanvasElement;
  mask: HTMLCanvasElement;
}

const cache = new Map<string, Promise<GlobeCanvases>>();

const nextFrame = () => new Promise<void>((r) => requestAnimationFrame(() => r()));

function mulberry(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeCanvas(w: number, h: number): [HTMLCanvasElement, CanvasRenderingContext2D] {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d", { willReadFrequently: false });
  if (!ctx) throw new Error("2D canvas unavailable");
  return [c, ctx];
}

/** Low-frequency value noise canvas, upscaled with smoothing for organic blotches. */
function noiseCanvas(w: number, h: number, seed: number, alpha: number, rgb: [number, number, number]): HTMLCanvasElement {
  const [c, ctx] = makeCanvas(w, h);
  const img = ctx.createImageData(w, h);
  const r = mulberry(seed);
  for (let i = 0; i < w * h; i++) {
    const v = r();
    img.data[i * 4] = rgb[0];
    img.data[i * 4 + 1] = rgb[1];
    img.data[i * 4 + 2] = rgb[2];
    img.data[i * 4 + 3] = Math.round(v * alpha * 255);
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

export function generateGlobeCanvases(size: number, detail: LandDetail, lightsFactor: number): Promise<GlobeCanvases> {
  const key = `${size}:${detail}:${lightsFactor}`;
  let p = cache.get(key);
  if (!p) {
    p = build(size, detail, lightsFactor);
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return p;
}

async function build(W: number, detail: LandDetail, lightsFactor: number): Promise<GlobeCanvases> {
  const H = W / 2;
  const [land, countries] = await Promise.all([loadLand(detail), loadCountries()]);
  const k = W / 4096; // scale factor relative to the 4K reference
  const projection = geoEquirectangular()
    .scale(W / (2 * Math.PI))
    .translate([W / 2, H / 2])
    .precision(0);

  /* ------------------------------------------------------------ day */
  const [day, d] = makeCanvas(W, H);
  const pathD = geoPath(projection, d);
  // Ocean: latitude gradient (deeper navy towards the poles)
  const ocean = d.createLinearGradient(0, 0, 0, H);
  ocean.addColorStop(0, "#040a17");
  ocean.addColorStop(0.3, "#081631");
  ocean.addColorStop(0.5, "#0b1d3d");
  ocean.addColorStop(0.7, "#081631");
  ocean.addColorStop(1, "#040a17");
  d.fillStyle = ocean;
  d.fillRect(0, 0, W, H);
  // Subtle ocean variation
  d.globalAlpha = 0.5;
  d.imageSmoothingEnabled = true;
  d.drawImage(noiseCanvas(128, 64, 7, 0.22, [40, 90, 150]), 0, 0, W, H);
  d.globalAlpha = 1;

  // Graticule (15°)
  d.beginPath();
  pathD(geoGraticule10());
  d.strokeStyle = "rgba(230, 191, 95, 0.05)";
  d.lineWidth = 1.1 * k;
  d.stroke();

  // Land fill
  d.beginPath();
  pathD(land as Feature<Geometry>);
  const landFill = d.createLinearGradient(0, 0, 0, H);
  landFill.addColorStop(0, "#1a2232");
  landFill.addColorStop(0.5, "#202a3a");
  landFill.addColorStop(1, "#1a2232");
  d.fillStyle = landFill;
  d.fill();
  // Terrain texture clipped to land
  d.save();
  d.clip();
  d.globalAlpha = 0.55;
  d.drawImage(noiseCanvas(256, 128, 11, 0.35, [120, 110, 80]), 0, 0, W, H);
  d.globalAlpha = 0.35;
  d.drawImage(noiseCanvas(512, 256, 23, 0.25, [10, 14, 20]), 0, 0, W, H);
  d.restore();
  await nextFrame();

  // Country borders (very faint)
  d.beginPath();
  pathD(countries);
  d.strokeStyle = "rgba(230, 191, 95, 0.12)";
  d.lineWidth = 0.8 * k;
  d.stroke();

  // Gold coastline with soft glow
  d.beginPath();
  pathD(land as Feature<Geometry>);
  d.save();
  d.shadowColor = "rgba(240, 210, 126, 0.55)";
  d.shadowBlur = 6 * k;
  d.strokeStyle = "rgba(240, 210, 126, 0.55)";
  d.lineWidth = 1.5 * k;
  d.stroke();
  d.restore();
  d.strokeStyle = "rgba(255, 236, 180, 0.65)";
  d.lineWidth = 0.7 * k;
  d.stroke();
  await nextFrame();

  /* ----------------------------------------------------------- mask */
  const MW = Math.min(W, 2048);
  const [mask, m] = makeCanvas(MW, MW / 2);
  const projM = geoEquirectangular()
    .scale(MW / (2 * Math.PI))
    .translate([MW / 2, MW / 4])
    .precision(0);
  m.fillStyle = "#000";
  m.fillRect(0, 0, MW, MW / 2);
  m.beginPath();
  geoPath(projM, m)(land as Feature<Geometry>);
  m.fillStyle = "#fff";
  m.fill();

  /* ---------------------------------------------------------- night */
  const [night, n] = makeCanvas(W, H);
  n.fillStyle = "#000";
  n.fillRect(0, 0, W, H);
  const r = mulberry(1729);
  const gauss = () => {
    const u = Math.max(r(), 1e-9);
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r());
  };
  const px = (lng: number) => ((lng + 180) / 360) * W;
  const py = (lat: number) => ((90 - lat) / 180) * H;
  const degPx = W / 360;
  const palette = ["255, 214, 140", "255, 190, 110", "255, 236, 190", "255, 170, 90"];

  // Inter-city links ("roads") between nearby cities
  n.lineCap = "round";
  for (let i = 0; i < CITY_LIGHTS.length; i++) {
    const a = CITY_LIGHTS[i]!;
    if (a[2] < 0.8) continue;
    for (let j = i + 1; j < CITY_LIGHTS.length; j++) {
      const b = CITY_LIGHTS[j]!;
      if (b[2] < 0.8) continue;
      const dLat = a[0] - b[0];
      const dLng = (a[1] - b[1]) * Math.cos(((a[0] + b[0]) / 2) * (Math.PI / 180));
      const dist = Math.hypot(dLat, dLng);
      if (dist > 4.5 || dist < 0.3) continue;
      const f = Math.min(a[3] ?? 1, b[3] ?? 1) * lightsFactor;
      const steps = Math.ceil((dist * degPx) / (3 * k + 1));
      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        const lat = a[0] + (b[0] - a[0]) * t + gauss() * 0.06;
        const lng = a[1] + (b[1] - a[1]) * t + gauss() * 0.06;
        n.fillStyle = `rgba(${palette[s % 4]}, ${(0.1 + r() * 0.18) * f})`;
        const sz = (0.7 + r() * 0.9) * k * 1.5;
        n.fillRect(px(lng), py(lat), sz, sz);
      }
    }
  }
  await nextFrame();

  // City clusters
  for (const [lat, lng, pop, factor = 1] of CITY_LIGHTS) {
    const f = factor * lightsFactor;
    const sp = Math.sqrt(pop);
    const sigma = 0.1 + sp * 0.13; // degrees
    const cosLat = Math.max(0.2, Math.cos(lat * (Math.PI / 180)));
    // core glow (metros only — small towns stay as pinpoints)
    const cx = px(lng);
    const cy = py(lat);
    if (pop >= 0.6) {
      const glowR = sigma * 1.6 * degPx;
      const g = n.createRadialGradient(cx, cy, 0, cx, cy, glowR);
      g.addColorStop(0, `rgba(255, 220, 150, ${Math.min(0.7, 0.12 + sp * 0.1) * f})`);
      g.addColorStop(0.35, `rgba(255, 190, 110, ${0.09 * f})`);
      g.addColorStop(1, "rgba(255, 170, 90, 0)");
      n.fillStyle = g;
      n.fillRect(cx - glowR / cosLat, cy - glowR, (glowR * 2) / cosLat, glowR * 2);
    }
    // scattered lights
    const count = Math.round((5 + Math.pow(pop, 0.75) * 64) * f);
    for (let i = 0; i < count; i++) {
      const dy = gauss() * sigma;
      const dx = (gauss() * sigma) / cosLat;
      const dd = Math.hypot(dx * cosLat, dy) / sigma;
      const alpha = Math.max(0.06, 0.92 - dd * 0.38) * (0.4 + r() * 0.6);
      n.fillStyle = `rgba(${palette[i % 4]}, ${alpha})`;
      const sz = (0.55 + r() * (dd < 1 ? 1.3 : 0.8)) * k * 1.6;
      n.fillRect(px(lng + dx), py(lat + dy), sz, sz);
    }
  }
  // Clip lights to (slightly dilated) land so coastal cities survive.
  // The mask is rendered once and composited in a SINGLE destination-in step
  // (compositing fill and stroke separately would erase the interior).
  const [clip, c] = makeCanvas(W, H);
  c.beginPath();
  pathD.context(c)(land as Feature<Geometry>);
  c.fillStyle = "#fff";
  c.fill();
  c.lineWidth = 7 * k;
  c.strokeStyle = "#fff";
  c.stroke();
  pathD.context(d);
  n.globalCompositeOperation = "destination-in";
  n.drawImage(clip, 0, 0);
  n.globalCompositeOperation = "source-over";

  return { day, night, mask };
}
