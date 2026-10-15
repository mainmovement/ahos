/**
 * Local geodata loader (same-origin static files in /public/geo — no external
 * network). Natural Earth via world-atlas@2 (public domain data, ISC package).
 */
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Polygon } from "geojson";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";

export type LandDetail = "50m" | "110m";

const cache = new Map<string, Promise<unknown>>();

function load<T>(url: string, transform: (json: unknown) => T): Promise<T> {
  let p = cache.get(url) as Promise<T> | undefined;
  if (!p) {
    p = fetch(url, { cache: "force-cache" })
      .then((r) => {
        if (!r.ok) throw new Error(`geo ${url}: HTTP ${r.status}`);
        return r.json() as Promise<unknown>;
      })
      .then(transform);
    p.catch(() => cache.delete(url));
    cache.set(url, p);
  }
  return p;
}

export function loadLand(detail: LandDetail): Promise<Feature<Geometry>> {
  return load(`/geo/land-${detail}.json`, (json) => {
    const topo = json as Topology<{ land: GeometryCollection }>;
    const fc = feature(topo, topo.objects.land) as unknown as FeatureCollection<Geometry> | Feature<Geometry>;
    if ("features" in fc) {
      return { type: "Feature", properties: {}, geometry: { type: "GeometryCollection", geometries: fc.features.map((f) => f.geometry) } } as Feature<Geometry>;
    }
    return fc;
  });
}

export function loadCountries(): Promise<FeatureCollection<Geometry, { name?: string }>> {
  return load("/geo/countries-110m.json", (json) => {
    const topo = json as Topology<{ countries: GeometryCollection<{ name?: string }> }>;
    return feature(topo, topo.objects.countries) as unknown as FeatureCollection<Geometry, { name?: string }>;
  });
}

export type IranFeature = Feature<Polygon | MultiPolygon, { name: string; nameFa: string }>;

export function loadIran(): Promise<IranFeature> {
  return load("/geo/iran-50m.geo.json", (json) => {
    const fc = json as FeatureCollection<Polygon | MultiPolygon, { name: string; nameFa: string }>;
    const f = fc.features[0];
    if (!f) throw new Error("Iran feature missing");
    return f;
  });
}

/** Outer rings of a (Multi)Polygon as [lng, lat][] arrays. */
export function outerRings(f: IranFeature): [number, number][][] {
  const g = f.geometry;
  const polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
  return polys.map((poly) => (poly[0] ?? []).map((c) => [c[0]!, c[1]!] as [number, number]));
}
