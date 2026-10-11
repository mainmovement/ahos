/**
 * Minimal ambient typing for the two pre-approved geo packages (M-D6.3).
 *
 * Neither `world-atlas` nor `topojson-client` ships a `.d.ts` and there is no
 * `@types` package for either, so without this `tsc` fails the import with
 * TS7016. Only the shape the globe actually uses is declared — the full
 * TopoJSON/GeoJSON vocabularies are far larger, and typing them here would be
 * invented breadth this project does not need.
 */

/** A TopoJSON geometry object as `topojson-client`'s `feature()` accepts it. */
declare interface TopoJSONGeometryObject {
  type: string;
  arcs?: unknown;
  coordinates?: unknown;
  geometries?: TopoJSONGeometryObject[];
  properties?: Record<string, unknown> | null;
}

/** A TopoJSON topology, as loaded from `world-atlas`. */
declare interface TopoJSONTopology {
  type: "Topology";
  objects: Record<string, TopoJSONGeometryObject>;
  arcs: number[][][];
  transform?: { scale: [number, number]; translate: [number, number] };
  bbox?: number[];
}

declare module "topojson-client" {
  /**
   * Rebuilds a TopoJSON object as GeoJSON, applying the topology's quantized
   * transform along the way. For a single geometry object it returns one Feature.
   */
  export function feature(
    topology: TopoJSONTopology,
    object: TopoJSONGeometryObject,
  ): { type: "Feature"; geometry: unknown; properties: unknown };
}

declare module "world-atlas/land-110m.json" {
  const topology: TopoJSONTopology;
  export default topology;
}
