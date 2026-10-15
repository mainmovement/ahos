/**
 * Day/night globe shader. The terminator comes from `sunDir` (world space),
 * computed from the real current time with the NOAA solar-position algorithm
 * (src/lib/astro/solar.ts).
 */
import * as THREE from "three";

export interface DayNightUniforms {
  [uniform: string]: THREE.IUniform;
  dayMap: THREE.IUniform<THREE.Texture | null>;
  nightMap: THREE.IUniform<THREE.Texture | null>;
  maskMap: THREE.IUniform<THREE.Texture | null>;
  sunDir: THREE.IUniform<THREE.Vector3>;
  nightGain: THREE.IUniform<number>;
  twilightColor: THREE.IUniform<THREE.Color>;
  rimColor: THREE.IUniform<THREE.Color>;
  ready: THREE.IUniform<number>;
}

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vPosW;
  void main() {
    vUv = uv;
    vNormalW = normalize(mat3(modelMatrix) * normal);
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vPosW = wp.xyz;
    gl_Position = projectionMatrix * viewMatrix * wp;
  }
`;

const fragmentShader = /* glsl */ `
  uniform sampler2D dayMap;
  uniform sampler2D nightMap;
  uniform sampler2D maskMap;
  uniform vec3 sunDir;
  uniform float nightGain;
  uniform vec3 twilightColor;
  uniform vec3 rimColor;
  uniform float ready;
  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vPosW;

  void main() {
    vec3 n = normalize(vNormalW);
    vec3 L = normalize(sunDir);
    vec3 V = normalize(cameraPosition - vPosW);
    float ndl = dot(n, L);

    vec3 day = texture2D(dayMap, vUv).rgb;
    vec3 night = texture2D(nightMap, vUv).rgb;
    float land = texture2D(maskMap, vUv).r;

    // Smooth terminator (≈ civil twilight width)
    float dayMix = smoothstep(-0.07, 0.17, ndl);

    // Day side: soft diffuse + ocean glint
    vec3 dayLit = day * (0.32 + 1.15 * max(ndl, 0.0));
    vec3 R = reflect(-L, n);
    float spec = pow(max(dot(R, V), 0.0), 64.0) * (1.0 - land);
    dayLit += vec3(1.0, 0.88, 0.66) * spec * 0.2;

    // Night side: city lights appear after sunset, faint gold coastlines stay readable
    float nightMix = 1.0 - smoothstep(-0.2, 0.05, ndl);
    vec3 nightSide = day * 0.38 + night * nightGain * nightMix;

    vec3 color = mix(nightSide, dayLit, dayMix);

    // Warm twilight band along the terminator
    float tw = exp(-pow(ndl / 0.12, 2.0));
    color += twilightColor * tw * 0.055;

    // Fresnel rim (atmospheric edge)
    float fres = pow(1.0 - max(dot(n, V), 0.0), 2.8);
    color += rimColor * fres * (0.22 + 0.4 * dayMix);

    // Fade in once textures are uploaded
    color = mix(vec3(0.012, 0.024, 0.05), color, ready);

    gl_FragColor = vec4(color, 1.0);
    #include <colorspace_fragment>
  }
`;

export function createDayNightMaterial(): THREE.ShaderMaterial & { uniforms: DayNightUniforms } {
  const uniforms: DayNightUniforms = {
    dayMap: { value: null },
    nightMap: { value: null },
    maskMap: { value: null },
    sunDir: { value: new THREE.Vector3(1, 0, 0) },
    nightGain: { value: 1.1 },
    twilightColor: { value: new THREE.Color("#f0b860") },
    rimColor: { value: new THREE.Color("#7fb8d8") },
    ready: { value: 0 },
  };
  return new THREE.ShaderMaterial({ uniforms, vertexShader, fragmentShader }) as THREE.ShaderMaterial & { uniforms: DayNightUniforms };
}
