#!/usr/bin/env node
/**
 * Copies runtime assets out of node_modules into /public so the app never
 * needs the network at runtime:
 *   - fonts  : Vazirmatn (variable) + Inter (variable, latin subset)  -> public/fonts
 *   - geodata: Natural Earth via world-atlas (TopoJSON)                -> public/geo
 *   - iran   : refined Iran outline extracted from countries-50m       -> public/geo/iran-50m.geo.json
 *
 * Run with `npm run fonts:sync` (alias kept for discoverability).
 * The generated files are committed, so this only needs to run when the
 * upstream packages are upgraded.
 */
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { feature } from "topojson-client";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const nm = (...p) => join(root, "node_modules", ...p);
const pub = (...p) => join(root, "public", ...p);

mkdirSync(pub("fonts"), { recursive: true });
mkdirSync(pub("geo"), { recursive: true });

const copies = [
  [nm("vazirmatn", "fonts", "webfonts", "Vazirmatn[wght].woff2"), pub("fonts", "Vazirmatn-Variable.woff2")],
  [nm("vazirmatn", "OFL.txt"), pub("fonts", "OFL-Vazirmatn.txt")],
  [nm("@fontsource-variable", "inter", "files", "inter-latin-wght-normal.woff2"), pub("fonts", "Inter-Variable-latin.woff2")],
  [nm("@fontsource-variable", "inter", "LICENSE"), pub("fonts", "OFL-Inter.txt")],
  [nm("world-atlas", "land-50m.json"), pub("geo", "land-50m.json")],
  [nm("world-atlas", "land-110m.json"), pub("geo", "land-110m.json")],
  [nm("world-atlas", "countries-110m.json"), pub("geo", "countries-110m.json")],
  [nm("world-atlas", "LICENSE"), pub("geo", "LICENSE-world-atlas.txt")],
];

for (const [from, to] of copies) {
  copyFileSync(from, to);
  console.log("copied", to.replace(root, "."));
}

// Extract Iran (ISO 3166-1 numeric 364) from the 50m countries file.
const topo = JSON.parse(readFileSync(nm("world-atlas", "countries-50m.json"), "utf8"));
const countries = feature(topo, topo.objects.countries);
const iran = countries.features.find((f) => String(f.id) === "364");
if (!iran) throw new Error("Iran feature (364) not found in countries-50m.json");
const round = (n) => Math.round(n * 1e4) / 1e4;
const roundCoords = (c) => (typeof c[0] === "number" ? c.map(round) : c.map(roundCoords));
iran.geometry.coordinates = roundCoords(iran.geometry.coordinates);
iran.properties = { name: "Iran", nameFa: "ایران", iso: "IRN", isoNumeric: "364", source: "Natural Earth 1:50m via world-atlas@2" };
writeFileSync(pub("geo", "iran-50m.geo.json"), JSON.stringify({ type: "FeatureCollection", features: [iran] }));
console.log("wrote ./public/geo/iran-50m.geo.json");
