import * as THREE from "three";
import { radialTexture, platformGlowTexture, unitRing, hash01 } from "./scene-utils";

/* Photoreal holographic Earth kit shared by both scenes:
   NASA Blue Marble day + Black Marble night + water-mask sun glint +
   drifting cloud shell + dual atmosphere + holo scan band + projector
   platform (light-well, trim rings, volumetric beam, rising embers).
   Textures are static, locally bundled files (see public/textures). */

export interface EarthPalette {
  atmosphere: number;
  sun: number;
  tint: number;
  tintStrength: number;
}

export interface EarthHologram {
  group: THREE.Group;
  globe: THREE.Group;
  update: (t: number, dt: number, globeRotX: number, globeRotY: number) => void;
  setPalette: (p: EarthPalette) => void;
  dispose: () => void;
}

export function createEarthHologram(
  renderer: THREE.WebGLRenderer,
  opts: {
    palette: EarthPalette;
    lightDir: THREE.Vector3;
    onFail: () => void;
    platform?: boolean; // projector platform + beam + embers
  },
): EarthHologram {
  const group = new THREE.Group();
  const globe = new THREE.Group();
  globe.rotation.z = 0.1;
  group.add(globe);

  const loader = new THREE.TextureLoader();
  loader.setCrossOrigin("anonymous");
  const dayTex = loader.load("/textures/earth-day-2048.jpg", undefined, undefined, () => opts.onFail());
  const nightTex = loader.load("/textures/earth-night-2048.jpg", undefined, undefined, () => opts.onFail());
  const waterTex = loader.load("/textures/earth-water-2048.png", undefined, undefined, () => opts.onFail());
  const cloudTex = loader.load("/textures/clouds-2048.png", undefined, undefined, () => opts.onFail());
  dayTex.colorSpace = THREE.SRGBColorSpace;
  nightTex.colorSpace = THREE.SRGBColorSpace;
  cloudTex.colorSpace = THREE.SRGBColorSpace;
  waterTex.colorSpace = THREE.NoColorSpace;
  for (const t of [dayTex, nightTex, waterTex, cloudTex]) {
    t.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  }

  const earthMat = new THREE.ShaderMaterial({
    uniforms: {
      uDay: { value: dayTex },
      uNight: { value: nightTex },
      uWater: { value: waterTex },
      uLightDir: { value: opts.lightDir.clone() },
      uAtmo: { value: new THREE.Color(opts.palette.atmosphere) },
      uTint: { value: new THREE.Color(opts.palette.tint) },
      uTintStrength: { value: opts.palette.tintStrength * 0.5 },
      uSun: { value: new THREE.Color(opts.palette.sun) },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vView;
      void main(){
        vUv = uv;
        vNormal = normalize(mat3(modelMatrix) * normal);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vView = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform sampler2D uDay;
      uniform sampler2D uNight;
      uniform sampler2D uWater;
      uniform vec3 uLightDir;
      uniform vec3 uAtmo;
      uniform vec3 uTint;
      uniform float uTintStrength;
      uniform vec3 uSun;
      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vView;
      void main(){
        vec3 N = normalize(vNormal);
        vec3 V = normalize(vView);
        vec3 L = normalize(uLightDir);
        float d = dot(N, L);
        float dayMix = smoothstep(-0.14, 0.28, d);

        vec3 day = texture2D(uDay, vUv).rgb;
        vec3 nightImg = texture2D(uNight, vUv).rgb;
        float water = texture2D(uWater, vUv).r;

        day = mix(day, day * (uTint * 0.5 + 0.72), uTintStrength);

        vec3 R = reflect(-L, N);
        float spec = pow(max(dot(R, V), 0.0), 42.0) * water * dayMix;
        day += uSun * spec * 0.55;

        float lights = dot(nightImg, vec3(0.35, 0.45, 0.2));
        vec3 city = vec3(1.0, 0.72, 0.34) * pow(lights, 1.35) * 1.5;
        vec3 night = vec3(0.012, 0.02, 0.045) + city;

        vec3 col = mix(night, day, dayMix);

        float fres = pow(1.0 - max(dot(N, V), 0.0), 2.6);
        col += uAtmo * fres * (0.35 + 0.45 * dayMix);

        float term = smoothstep(0.22, 0.0, abs(d)) * 0.14;
        col += vec3(0.9, 0.55, 0.25) * term;

        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(1, 96, 96), earthMat));

  const cloudMat = new THREE.MeshLambertMaterial({
    map: cloudTex,
    transparent: true,
    opacity: 0.34,
    depthWrite: false,
  });
  const clouds = new THREE.Mesh(new THREE.SphereGeometry(1.016, 72, 72), cloudMat);
  group.add(clouds);

  const scanMat = new THREE.MeshBasicMaterial({
    color: 0x7fd8e8,
    transparent: true,
    opacity: 0.22,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const scan = new THREE.Mesh(new THREE.TorusGeometry(1, 0.006, 8, 128), scanMat);
  scan.rotation.x = Math.PI / 2;
  group.add(scan);

  const atmosphereMat = new THREE.ShaderMaterial({
    uniforms: {
      uColor: { value: new THREE.Color(opts.palette.atmosphere) },
      uLightDir: { value: opts.lightDir.clone() },
    },
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vWorld;
      void main(){
        vNormal = normalize(mat3(modelMatrix) * normal);
        vWorld = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      varying vec3 vNormal;
      varying vec3 vWorld;
      uniform vec3 uColor;
      uniform vec3 uLightDir;
      void main(){
        float i = pow(0.72 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 3.2);
        float lit = 0.5 + 0.5 * dot(normalize(vWorld), normalize(uLightDir));
        gl_FragColor = vec4(uColor, 1.0) * i * (0.16 + 0.22 * lit);
      }`,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    transparent: true,
    depthWrite: false,
  });
  group.add(new THREE.Mesh(new THREE.SphereGeometry(1.12, 64, 64), atmosphereMat));

  const innerAtmoMat = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(opts.palette.atmosphere) } },
    vertexShader: `
      varying vec3 vNormal; varying vec3 vView;
      void main(){
        vNormal = normalize(normalMatrix * normal);
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vView = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying vec3 vNormal; varying vec3 vView; uniform vec3 uColor;
      void main(){
        float fres = pow(1.0 - max(dot(normalize(vNormal), normalize(vView)), 0.0), 3.4);
        gl_FragColor = vec4(uColor, fres * 0.22);
      }`,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  group.add(new THREE.Mesh(new THREE.SphereGeometry(1.035, 64, 64), innerAtmoMat));

  /* ------------- projector platform (optional) ------------- */
  const glowTexture = radialTexture(0.35);
  const wellTexture = platformGlowTexture();
  const disposables: Array<{ dispose: () => void }> = [glowTexture, wellTexture, dayTex, nightTex, waterTex, cloudTex];
  const pRings: Array<{ mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; speed: number }> = [];
  let pGlowMat: THREE.SpriteMaterial | null = null;
  let beamMat: THREE.ShaderMaterial | null = null;
  let emberGeo: THREE.BufferGeometry | null = null;
  const EMBERS = 70;
  let emberSeed: number[] = [];

  if (opts.platform !== false) {
    const platform = new THREE.Group();
    platform.position.y = -1.36;
    group.add(platform);

    const well = new THREE.Mesh(
      new THREE.CircleGeometry(1.18, 72),
      new THREE.MeshBasicMaterial({ map: wellTexture, color: 0xd4af37, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    well.rotation.x = -Math.PI / 2;
    platform.add(well);

    const P_RINGS = [
      { scale: 0.92, color: 0xd4af37, opacity: 0.3, speed: 0.24 },
      { scale: 0.66, color: 0x22d3ee, opacity: 0.4, speed: -0.36 },
      { scale: 1.3, color: 0x8b5cf6, opacity: 0.16, speed: 0.12 },
    ];
    P_RINGS.forEach((r) => {
      const mat = new THREE.MeshBasicMaterial({
        color: r.color, transparent: true, opacity: r.opacity, blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide, depthWrite: false,
      });
      const mesh = new THREE.Mesh(unitRing(), mat);
      mesh.rotation.x = Math.PI / 2;
      mesh.scale.setScalar(r.scale);
      platform.add(mesh);
      pRings.push({ mesh, mat, speed: r.speed });
    });

    pGlowMat = new THREE.SpriteMaterial({
      map: glowTexture, color: 0xd4af37, transparent: true, opacity: 0.16,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const pGlow = new THREE.Sprite(pGlowMat);
    pGlow.scale.setScalar(1.9);
    platform.add(pGlow);

    beamMat = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 }, uColor: { value: new THREE.Color(0x6fd8ec) } },
      vertexShader: `
        varying vec3 vNormal; varying vec3 vView; varying vec2 vUvB;
        void main(){
          vUvB = uv;
          vNormal = normalize(normalMatrix * normal);
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          vView = normalize(-mv.xyz);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader: `
        varying vec3 vNormal; varying vec3 vView; varying vec2 vUvB;
        uniform float uTime; uniform vec3 uColor;
        float hash(vec2 p){ return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); }
        void main(){
          float edge = pow(abs(dot(normalize(vNormal), normalize(vView))), 1.4);
          float fall = smoothstep(0.0, 0.42, vUvB.y) * smoothstep(1.0, 0.62, vUvB.y);
          float flick = 0.82 + 0.18 * sin(uTime * 2.1 + vUvB.y * 9.0)
                      + 0.06 * (hash(vec2(floor(uTime * 14.0), vUvB.y * 4.0)) - 0.5);
          float a = edge * fall * flick * 0.16;
          vec3 col = mix(uColor, vec3(1.0, 0.86, 0.5), (1.0 - vUvB.y) * 0.45);
          gl_FragColor = vec4(col, a);
        }`,
      transparent: true,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.06, 1.42, 64, 1, true), beamMat);
    beam.position.y = -0.66;
    group.add(beam);

    emberGeo = new THREE.BufferGeometry();
    const pos: number[] = [];
    emberSeed = [];
    for (let i = 0; i < EMBERS; i += 1) {
      pos.push(0, 0, 0);
      emberSeed.push(hash01(i * 71 + 3) * Math.PI * 2, 0.05 + hash01(i * 97 + 11) * 0.12, hash01(i * 131 + 7));
    }
    emberGeo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    const embers = new THREE.Points(
      emberGeo,
      new THREE.PointsMaterial({
        size: 0.035, map: glowTexture, color: 0xf3d27a, transparent: true, opacity: 0.85,
        blending: THREE.AdditiveBlending, depthWrite: false,
      }),
    );
    group.add(embers);
  }

  const update = (t: number, _dt: number, globeRotX: number, globeRotY: number) => {
    clouds.rotation.y = globeRotY * 1.12 + t * 0.004;
    clouds.rotation.x = globeRotX;
    const scanY = Math.sin(t * 0.3) * 0.92;
    scan.position.y = scanY;
    const sr = Math.sqrt(Math.max(0.02, 1 - scanY * scanY));
    scan.scale.setScalar(sr * 1.008);
    scanMat.opacity = 0.1 + (Math.sin(t * 1.7) * 0.5 + 0.5) * 0.12;

    pRings.forEach((r) => {
      r.mesh.rotation.z += _dt * r.speed;
    });
    if (pGlowMat) pGlowMat.opacity = 0.12 + (Math.sin(t * 1.4) * 0.5 + 0.5) * 0.05;
    if (beamMat) beamMat.uniforms.uTime.value = t;
    if (emberGeo) {
      const attr = emberGeo.getAttribute("position") as THREE.BufferAttribute;
      for (let i = 0; i < EMBERS; i += 1) {
        const phase = emberSeed[i * 3];
        const speed = emberSeed[i * 3 + 1];
        const seed = emberSeed[i * 3 + 2];
        const life = (t * speed + seed) % 1;
        const x = Math.cos(phase + life * 2.4) * (0.28 + life * 0.85);
        const z = Math.sin(phase + life * 2.4) * (0.28 + life * 0.85);
        attr.setXYZ(i, x, -1.34 + life * 1.15, z);
      }
      attr.needsUpdate = true;
    }
  };

  const setPalette = (p: EarthPalette) => {
    earthMat.uniforms.uAtmo.value.setHex(p.atmosphere);
    earthMat.uniforms.uSun.value.setHex(p.sun);
    earthMat.uniforms.uTint.value.setHex(p.tint);
    earthMat.uniforms.uTintStrength.value = p.tintStrength * 0.5;
    atmosphereMat.uniforms.uColor.value.setHex(p.atmosphere);
    innerAtmoMat.uniforms.uColor.value.setHex(p.atmosphere);
  };

  const dispose = () => {
    disposables.forEach((d) => d.dispose());
  };

  return { group, globe, update, setPalette, dispose };
}
