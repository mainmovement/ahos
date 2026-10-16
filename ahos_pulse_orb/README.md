# AHOS Pulse Orb

Self-contained Next.js 16 app (React 19, TypeScript strict, Tailwind 4) featuring the
`<PulseOrb />` calm-technology visualization component.

## Run

```bash
npm install
npm run dev      # http://0.0.0.0:3000
npm run build
npm run typecheck
```

Demo page: `/orb-demo`

## Props

```ts
<PulseOrb
  health={{ bpm: number; jitterMs: number; stale: boolean }}
  departments={[{ id; nameFa; rate; queue; lastDataAt; confidence; status }]}
  signals={[{ id; deptId; at; outcome; reason? }]}
  quality={"low" | "medium" | "high"}   // optional, default medium
  onMorph={(morphed: boolean) => void}  // optional
/>
```

## Performance notes

- GPGPU particles via `GPUComputationRenderer`, capped at 256x256 (~65k) half-float textures.
- Single draw call, additive blending. Pixel ratio capped at 1.5.
- Pauses when tab is hidden (`document.hidden`). Disposes all resources on unmount (React strict-mode safe).
- WebGL feature detection with 2D SVG fallback; `prefers-reduced-motion` supported.
- Not benchmarked on target hardware in this environment; reported honestly as unverified.

## Truthfulness

- Demo data is marked DEMO (banner on demo page).
- Missing data renders as UNKNOWN; no fabricated numbers.
- PAPER-ONLY watermark (gold edge hatching) is permanent.

## What could not be verified

- No headless browser available in this environment, so runtime screenshots and FPS benchmarking were not performed.
- WebGL/GPGPU runtime behavior is untested beyond TypeScript and production build.