import { geoArea, geoBounds, geoCentroid, geoContains, geoPath } from "d3-geo";
import type { Feature, FeatureCollection, Geometry, Position } from "geojson";

export interface MapTargets {
  data: Float32Array;
  sampledPoints: number;
  iranPoints: number;
  featuresWithPaths: number;
}

function polygons(geometry: Geometry): Position[][] {
  if (geometry.type === "Polygon") return geometry.coordinates;
  if (geometry.type === "MultiPolygon") return geometry.coordinates.flat();
  return [];
}

function featureName(feature: Feature): string {
  const p = feature.properties as Record<string, unknown> | null;
  return String(p?.name ?? p?.NAME ?? p?.admin ?? p?.ADMIN ?? "");
}

function random01(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Sample = [number, number, number, number];

function project(lon: number, lat: number, iran: boolean): Sample {
  // Equal-angle display projection, clamped to avoid polar blow-up.
  const latitude = Math.max(-82, Math.min(82, lat));
  return [(lon / 180) * 2.2, (-latitude / 90) * 1.55, 0, iran ? 1 : 0];
}

/** Deterministically samples real country boundaries and polygon interiors. */
export function buildMapTargets(collection: FeatureCollection, textureSize: number): MapTargets {
  const count = textureSize * textureSize;
  const data = new Float32Array(count * 4);
  const valid = collection.features.filter((f): f is Feature<Geometry> => f.geometry !== null);
  const pathGenerator = geoPath(null);
  const features = valid.map((feature) => {
    const rings = polygons(feature.geometry);
    const vertices = rings.flat().filter((p) => p.length >= 2);
    const path = pathGenerator(feature);
    const centroid = geoCentroid(feature);
    const area = Math.max(geoArea(feature), 1e-8);
    return {
      feature,
      vertices,
      pathPresent: typeof path === "string" && path.length > 0,
      centroid,
      area,
      perimeterWeight: Math.max(vertices.length, 1),
      iran: /\biran\b/i.test(featureName(feature)),
    };
  }).filter((f) => f.vertices.length > 0);

  const totalArea = features.reduce((sum, f) => sum + f.area, 0) || 1;
  const totalPerimeter = features.reduce((sum, f) => sum + f.perimeterWeight, 0) || 1;
  const rng = random01(0xA4052026);
  const points: Sample[] = [];

  // Distribute boundary samples proportional to vertex density and interior samples
  // proportional to spherical country area. Both are derived from bundled geometry.
  const boundaryBudget = Math.floor(count * 0.42);
  const interiorBudget = count - boundaryBudget;
  for (const f of features) {
    const boundaryCount = Math.max(1, Math.round(boundaryBudget * f.perimeterWeight / totalPerimeter));
    for (let i = 0; i < boundaryCount; i++) {
      const p = f.vertices[Math.floor((i * f.vertices.length) / boundaryCount) % f.vertices.length];
      points.push(project(p[0], p[1], f.iran));
    }
    const fillCount = Math.max(0, Math.round(interiorBudget * f.area / totalArea));
    if (!fillCount) continue;
    const [[minLon, minLat], [maxLon, maxLat]] = geoBounds(f.feature);
    let accepted = 0;
    let tries = 0;
    const maxTries = Math.max(fillCount * 100, 100);
    while (accepted < fillCount && tries < maxTries) {
      const lon = minLon + rng() * (maxLon - minLon);
      const lat = minLat + rng() * (maxLat - minLat);
      tries++;
      if (geoContains(f.feature, [lon, lat])) {
        points.push(project(lon, lat, f.iran));
        accepted++;
      }
    }
    // Keep country representation anchored even for narrow / tiny polygons.
    if (accepted === 0 && Number.isFinite(f.centroid[0])) {
      points.push(project(f.centroid[0], f.centroid[1], f.iran));
    }
  }

  if (points.length === 0) throw new Error("Bundled GeoJSON produced no map samples");
  let iranPoints = 0;
  for (let i = 0; i < count; i++) {
    // Evenly resample the deterministic geometry-derived point cloud to texture size.
    const p = points[Math.floor((i * points.length) / count) % points.length];
    const o = i * 4;
    data[o] = p[0];
    data[o + 1] = p[1];
    data[o + 2] = p[2];
    data[o + 3] = p[3];
    if (p[3] > 0.5) iranPoints++;
  }
  return {
    data,
    sampledPoints: count,
    iranPoints,
    featuresWithPaths: features.filter((f) => f.pathPresent).length,
  };
}

export function particleTextureSize(quality: "low" | "medium" | "high"): number {
  return quality === "low" ? 64 : quality === "high" ? 256 : 128;
}
