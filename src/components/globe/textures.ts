import * as THREE from "three";
import {
  countryRings,
  referenceCities,
  type CountryCollection,
} from "../../lib/geography";
export type GlobePalette = {
  ocean: string;
  land: string;
  line: string;
  night: string;
  light: string;
  gold: string;
  atmosphere: string;
};
export function makeEarthTextures(
  countries: CountryCollection,
  palette: GlobePalette,
  size: number,
) {
  const day = document.createElement("canvas");
  day.width = size;
  day.height = size / 2;
  const ctx = day.getContext("2d");
  if (!ctx) throw new Error("Canvas 2D unavailable");
  ctx.fillStyle = palette.ocean;
  ctx.fillRect(0, 0, day.width, day.height);
  const project = (lng: number, lat: number) => [
    ((lng + 180) / 360) * size,
    ((90 - lat) / 180) * (size / 2),
  ];
  countries.features.forEach((feature) => {
    ctx.beginPath();
    countryRings(feature).forEach((ring) =>
      ring.forEach(([lng, lat], i) => {
        const [x, y] = project(lng, lat);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }),
    );
    ctx.closePath();
    ctx.fillStyle =
      feature.properties.iso === "IRN" ? palette.gold : palette.land;
    ctx.globalAlpha = feature.properties.iso === "IRN" ? 0.75 : 1;
    ctx.fill("evenodd");
    ctx.globalAlpha = 1;
    ctx.strokeStyle = palette.line;
    ctx.lineWidth = size / 3000;
    ctx.stroke();
  });
  ctx.globalAlpha = 0.12;
  ctx.strokeStyle = palette.line;
  ctx.lineWidth = 0.5;
  for (let lng = -180; lng <= 180; lng += 15) {
    const [x] = project(lng, 0);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, size / 2);
    ctx.stroke();
  }
  for (let lat = -75; lat <= 75; lat += 15) {
    const [, y] = project(0, lat);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(size, y);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  // Stylized city lights, not a satellite photograph or an activity measurement.
  const night = document.createElement("canvas");
  night.width = size;
  night.height = size / 2;
  const n = night.getContext("2d");
  if (!n) throw new Error("Canvas 2D unavailable");
  n.fillStyle = palette.night;
  n.fillRect(0, 0, size, size / 2);
  referenceCities.forEach((city, index) => {
    const [cx, cy] = project(city.lng, city.lat);
    const glow = n.createRadialGradient(cx, cy, 0, cx, cy, size / 160);
    glow.addColorStop(0, palette.light);
    glow.addColorStop(1, palette.night);
    n.globalAlpha = 0.55;
    n.fillStyle = glow;
    n.fillRect(cx - size / 160, cy - size / 160, size / 80, size / 80);
    for (let j = 0; j < 30; j++) {
      const angle = j * 2.39996 + index;
      const radius = (Math.sqrt(j) * size) / 1900;
      n.globalAlpha = 0.3 + (j % 5) / 8;
      n.fillStyle = palette.light;
      n.fillRect(
        cx + Math.cos(angle) * radius,
        cy + Math.sin(angle) * radius,
        0.7 + size / 2600,
        0.7 + size / 2600,
      );
    }
  });
  n.globalAlpha = 1;
  const dayTexture = new THREE.CanvasTexture(day);
  const nightTexture = new THREE.CanvasTexture(night);
  dayTexture.anisotropy = 4;
  nightTexture.anisotropy = 4;
  return { dayTexture, nightTexture };
}
export function makeEarthMaterial(
  dayTexture: THREE.Texture,
  nightTexture: THREE.Texture,
) {
  return new THREE.ShaderMaterial({
    uniforms: {
      dayMap: { value: dayTexture },
      nightMap: { value: nightTexture },
      sunDirection: { value: new THREE.Vector3(1, 0, 0) },
    },
    vertexShader: `varying vec2 vUv; varying vec3 vWorldNormal; void main(){ vUv=uv; vWorldNormal=normalize(mat3(modelMatrix)*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `uniform sampler2D dayMap; uniform sampler2D nightMap; uniform vec3 sunDirection; varying vec2 vUv; varying vec3 vWorldNormal; void main(){ float solar=dot(normalize(vWorldNormal),normalize(sunDirection)); float daylight=smoothstep(-0.08,0.10,solar); vec3 day=texture2D(dayMap,vUv).rgb; vec3 night=texture2D(nightMap,vUv).rgb; vec3 surface=day*(0.32+daylight*(0.55+max(solar,0.0)*0.30)); surface+=night*(1.0-daylight)*1.6; gl_FragColor=vec4(surface,1.0); }`,
  });
}
