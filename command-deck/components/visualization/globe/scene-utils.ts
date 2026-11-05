import * as THREE from "three";

/* Shared deterministic / procedural helpers for the command scenes.
   No Math.random and no wall clock anywhere — every variation derives
   from integer hashes so renders are reproducible. */

export function hash01(i: number): number {
  let h = (i * 2654435761) >>> 0;
  h ^= h >>> 13;
  h = (h * 1274126177) >>> 0;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

export function radialTexture(softness = 0.55): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 62);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(softness, "rgba(255,255,255,0.8)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 128, 128);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** soft ring sprite used by the projector platform */
export function platformGlowTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(128, 128, 20, 128, 128, 126);
    grad.addColorStop(0, "rgba(255,255,255,0.85)");
    grad.addColorStop(0.55, "rgba(255,255,255,0.18)");
    grad.addColorStop(0.85, "rgba(255,255,255,0.05)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const ringGeoCache = { inner: 0, outer: 0, geo: null as THREE.RingGeometry | null };
export function unitRing(): THREE.RingGeometry {
  if (!ringGeoCache.geo || ringGeoCache.inner !== 0.86 || ringGeoCache.outer !== 1) {
    ringGeoCache.inner = 0.86;
    ringGeoCache.outer = 1;
    ringGeoCache.geo = new THREE.RingGeometry(0.86, 1, 96);
  }
  return ringGeoCache.geo;
}

export function circlePoints(radius: number, segments = 160, y = 0): THREE.Vector3[] {
  return Array.from({ length: segments }, (_, i) => {
    const a = (i / segments) * Math.PI * 2;
    return new THREE.Vector3(Math.cos(a) * radius, y, Math.sin(a) * radius);
  });
}

/** lat/lon (degrees) → unit vector matching THREE.SphereGeometry equirect UVs */
export function latLonToVec(lat: number, lon: number): THREE.Vector3 {
  const phi = ((lon + 180) / 360) * Math.PI * 2;
  const theta = ((90 - lat) / 180) * Math.PI;
  return new THREE.Vector3(
    -Math.cos(phi) * Math.sin(theta),
    Math.cos(theta),
    Math.sin(phi) * Math.sin(theta),
  );
}

/* final grade pass: vignette + film grain + subtle chromatic aberration */
export const GRADE_SHADER = {
  uniforms: {
    tDiffuse: { value: null as THREE.Texture | null },
    uTime: { value: 0 },
    uAmount: { value: 1 },
  },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform float uAmount;
    varying vec2 vUv;
    float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7)) + uTime * 13.7) * 43758.5453); }
    void main(){
      vec2 c = vUv - 0.5;
      float r2 = dot(c, c);
      float ab = 0.0016 * r2 * 4.0 * uAmount;
      vec3 col;
      col.r = texture2D(tDiffuse, vUv + c * ab).r;
      col.g = texture2D(tDiffuse, vUv).g;
      col.b = texture2D(tDiffuse, vUv - c * ab).b;
      float vig = smoothstep(0.95, 0.28, length(c) * 1.25);
      col *= mix(1.0, vig, 0.42 * uAmount);
      col += (hash(vUv * vec2(1920.0, 1080.0)) - 0.5) * 0.028 * uAmount;
      gl_FragColor = vec4(col, 1.0);
    }`,
};

/** dispose a whole subtree of meshes/points/lines/sprites */
export function disposeObject(root: THREE.Object3D): void {
  root.traverse((obj) => {
    if (obj instanceof THREE.Mesh || obj instanceof THREE.Points || obj instanceof THREE.Line) {
      obj.geometry.dispose();
      const mat = obj.material as THREE.Material | THREE.Material[];
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
      else mat.dispose();
    }
    if (obj instanceof THREE.Sprite) obj.material.dispose();
  });
}
