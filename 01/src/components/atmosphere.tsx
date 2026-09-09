"use client";

import { useEffect, useRef, useState } from "react";
import {
  Cloud, CloudFog, CloudLightning, CloudRain, CloudSnow,
  Moon, Sun, Thermometer, Wind,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* AHOS Dynamic Environment Engine                                     */
/* location → timezone → hour → season → weather → living visuals      */
/* ------------------------------------------------------------------ */

type Cond = "clear" | "clouds" | "rain" | "storm" | "snow" | "fog";

type EnvState = {
  hour: number;          // decimal hour in resolved timezone
  tz: string;
  city: string;
  tempC: number | null;
  cond: Cond;
  isDay: boolean;
  season: "spring" | "summer" | "autumn" | "winter";
};

type Palette = { a: number[]; b: number[]; p: number[]; star: boolean };

const STOPS: { h: number; pal: Palette }[] = [
  { h: 0,    pal: { a: [16, 38, 60],  b: [10, 46, 48],  p: [126, 224, 200], star: true } },
  { h: 4,    pal: { a: [14, 30, 55],  b: [12, 52, 50],  p: [126, 224, 200], star: true } },
  { h: 5.5,  pal: { a: [64, 38, 78],  b: [120, 70, 38], p: [252, 211, 137], star: false } },
  { h: 7,    pal: { a: [92, 62, 48],  b: [30, 84, 74],  p: [252, 211, 137], star: false } },
  { h: 9,    pal: { a: [24, 72, 88],  b: [18, 80, 70],  p: [150, 240, 215], star: false } },
  { h: 12,   pal: { a: [28, 84, 92],  b: [16, 88, 76],  p: [167, 243, 228], star: false } },
  { h: 15,   pal: { a: [26, 74, 84],  b: [30, 88, 60],  p: [167, 243, 228], star: false } },
  { h: 17.5, pal: { a: [72, 62, 44],  b: [46, 74, 60],  p: [252, 211, 137], star: false } },
  { h: 19.5, pal: { a: [92, 48, 44],  b: [58, 40, 76],  p: [252, 190, 120], star: false } },
  { h: 21,   pal: { a: [38, 32, 70],  b: [14, 42, 58],  p: [150, 205, 230], star: true } },
  { h: 24,   pal: { a: [16, 38, 60],  b: [10, 46, 48],  p: [126, 224, 200], star: true } },
];

function paletteAt(hour: number): Palette {
  let i = 0;
  while (i < STOPS.length - 2 && hour >= STOPS[i + 1].h) i++;
  const s0 = STOPS[i], s1 = STOPS[i + 1];
  const t = Math.min(1, Math.max(0, (hour - s0.h) / (s1.h - s0.h)));
  const mix = (x: number[], y: number[]) => x.map((v, k) => v + (y[k] - v) * t);
  return {
    a: mix(s0.pal.a, s1.pal.a),
    b: mix(s0.pal.b, s1.pal.b),
    p: mix(s0.pal.p, s1.pal.p),
    star: hour < 7 ? s0.pal.star : s1.pal.star,
  };
}

function seasonOf(month: number): EnvState["season"] {
  if (month >= 3 && month < 6) return "spring";
  if (month >= 6 && month < 9) return "summer";
  if (month >= 9 && month < 12) return "autumn";
  return "winter";
}

function condOf(code: number): Cond {
  if (code === 0 || code === 1) return "clear";
  if (code === 2 || code === 3) return "clouds";
  if (code === 45 || code === 48) return "fog";
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return "rain";
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "snow";
  if (code >= 95) return "storm";
  return "clouds";
}

const SEASON_TINT: Record<EnvState["season"], number[]> = {
  spring: [150, 240, 200], summer: [252, 220, 140], autumn: [252, 176, 110], winter: [170, 215, 255],
};

function localHour(tz: string): number {
  try {
    const parts = new Intl.DateTimeFormat("en-GB", {
      timeZone: tz, hour12: false, hour: "numeric", minute: "numeric",
    }).formatToParts(new Date());
    const h = Number(parts.find((p) => p.type === "hour")?.value ?? "12") % 24;
    const m = Number(parts.find((p) => p.type === "minute")?.value ?? "0");
    return h + m / 60;
  } catch {
    return new Date().getHours() + new Date().getMinutes() / 60;
  }
}

type Strings = {
  engine: string;
  fallback: string;
  seasons: Record<EnvState["season"], string>;
  cond: Record<Cond, string>;
  day: string;
  night: string;
};

export default function Atmosphere({ locale, strings }: { locale: "fa" | "en"; strings: Strings }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const envRef = useRef<EnvState>({
    hour: 20.5, tz: "Asia/Tehran", city: "Tehran", tempC: null,
    cond: "clear", isDay: false, season: seasonOf(new Date().getMonth() + 1),
  });
  const [env, setEnv] = useState<EnvState>(envRef.current);
  const [geoFallback, setGeoFallback] = useState(true);

  /* — environment acquisition — */
  useEffect(() => {
    let cancelled = false;
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Tehran";

    async function loadWeather(lat: number, lon: number, explicitTz?: string) {
      try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,is_day&timezone=auto`;
        const res = await fetch(url);
        const j = await res.json();
        if (cancelled) return;
        const z: string = explicitTz ?? j.timezone ?? tz;
        const now = new Date();
        const monthInZone = Number(
          new Intl.DateTimeFormat("en-US", { timeZone: z, month: "numeric" }).format(now),
        );
        envRef.current = {
          ...envRef.current,
          tz: z,
          city: decodeURIComponent(z.split("/").pop() ?? z).replace(/_/g, " "),
          tempC: typeof j.current?.temperature_2m === "number" ? Math.round(j.current.temperature_2m) : null,
          cond: condOf(Number(j.current?.weather_code ?? 1)),
          isDay: j.current?.is_day !== 0,
          season: seasonOf(monthInZone),
          hour: localHour(z),
        };
      } catch {
        if (cancelled) return;
        envRef.current = { ...envRef.current, tz, hour: localHour(tz) };
      }
      if (!cancelled) setEnv({ ...envRef.current });
    }

    const fallbackLoad = () => loadWeather(35.6892, 51.389, "Asia/Tehran");

    if (typeof navigator !== "undefined" && navigator.geolocation) {
      const timer = setTimeout(fallbackLoad, 4000);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          clearTimeout(timer);
          setGeoFallback(false);
          void loadWeather(pos.coords.latitude, pos.coords.longitude);
        },
        () => { clearTimeout(timer); void fallbackLoad(); },
        { timeout: 3500, maximumAge: 900_000 },
      );
    } else {
      void fallbackLoad();
    }

    const clock = setInterval(() => {
      envRef.current = { ...envRef.current, hour: localHour(envRef.current.tz) };
      if (!cancelled) setEnv({ ...envRef.current });
    }, 30_000);

    return () => { cancelled = true; clearInterval(clock); };
  }, []);

  /* — living cv — */
  useEffect(() => {
    const cv = canvasRef.current as HTMLCanvasElement;
    if (!cv) return;
    const g2d = cv.getContext("2d") as CanvasRenderingContext2D;
    if (!g2d) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, dpr = 1, raf = 0, last = performance.now(), t = 0;
    let visible = true;

    type Spore = { x: number; y: number; vx: number; vy: number; r: number; ph: number; tint: boolean };
    type Drop = { x: number; y: number; v: number; len: number };
    type Flake = { x: number; y: number; v: number; r: number; ph: number };
    type Star = { x: number; y: number; r: number; ph: number };

    let spores: Spore[] = [];
    let drops: Drop[] = [];
    let flakes: Flake[] = [];
    let stars: Star[] = [];

    function build() {
      const n = Math.min(130, Math.floor((w * h) / 16000));
      spores = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 9, vy: (Math.random() - 0.5) * 7 - 2,
        r: 0.7 + Math.random() * 1.9, ph: Math.random() * Math.PI * 2,
        tint: Math.random() < 0.3,
      }));
      drops = Array.from({ length: 90 }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        v: 420 + Math.random() * 300, len: 10 + Math.random() * 16,
      }));
      flakes = Array.from({ length: 80 }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        v: 22 + Math.random() * 30, r: 1 + Math.random() * 2.2, ph: Math.random() * Math.PI * 2,
      }));
      stars = Array.from({ length: 110 }, () => ({
        x: Math.random() * w, y: Math.random() * h * 0.7,
        r: Math.random() * 1.1 + 0.2, ph: Math.random() * Math.PI * 2,
      }));
    }

    function resize() {
      dpr = Math.min(2, window.devicePixelRatio || 1);
      w = window.innerWidth; h = window.innerHeight;
      cv.width = Math.floor(w * dpr);
      cv.height = Math.floor(h * dpr);
      cv.style.width = `${w}px`;
      cv.style.height = `${h}px`;
      g2d.setTransform(dpr, 0, 0, dpr, 0, 0);
      build();
    }

    const rgba = (c: number[], a: number) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;

    function frame(now: number) {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      t += dt;
      const env = envRef.current;
      const pal = paletteAt(env.hour);
      const seasonTint = SEASON_TINT[env.season];

      g2d.clearRect(0, 0, w, h);

      /* aurora blobs */
      const blobs = [
        { x: 0.22 + Math.sin(t * 0.05) * 0.06, y: 0.2 + Math.cos(t * 0.04) * 0.05, r: 0.62, c: pal.a, a: 0.16 },
        { x: 0.78 + Math.cos(t * 0.043) * 0.07, y: 0.34 + Math.sin(t * 0.036) * 0.06, r: 0.58, c: pal.b, a: 0.14 },
        { x: 0.5 + Math.sin(t * 0.03 + 2) * 0.08, y: 0.85, r: 0.5, c: pal.b, a: 0.1 },
      ];
      for (const b of blobs) {
        const gx = b.x * w, gy = b.y * h, gr = b.r * Math.max(w, h) * 0.6;
        const g = g2d.createRadialGradient(gx, gy, 0, gx, gy, gr);
        g.addColorStop(0, rgba(b.c, b.a));
        g.addColorStop(1, rgba(b.c, 0));
        g2d.fillStyle = g;
        g2d.fillRect(0, 0, w, h);
      }

      /* star field at night */
      if (pal.star) {
        for (const s of stars) {
          const tw = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 1.4 + s.ph));
          g2d.fillStyle = `rgba(220,240,255,${0.5 * tw})`;
          g2d.beginPath(); g2d.arc(s.x, s.y, s.r, 0, Math.PI * 2); g2d.fill();
        }
      }

      /* spores + filaments */
      const pc = pal.p;
      for (const s of spores) {
        s.x += (s.vx + Math.sin(t * 0.6 + s.ph) * 6) * dt;
        s.y += s.vy * dt;
        if (s.x < -20) s.x = w + 20; if (s.x > w + 20) s.x = -20;
        if (s.y < -20) s.y = h + 20; if (s.y > h + 20) s.y = -20;
      }
      g2d.lineWidth = 0.6;
      for (let i = 0; i < spores.length; i++) {
        const a = spores[i];
        for (let j = i + 1; j < i + 5 && j < spores.length; j++) {
          const b = spores[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 8100) {
            const al = (1 - d2 / 8100) * 0.14;
            g2d.strokeStyle = rgba(pc, al);
            g2d.beginPath(); g2d.moveTo(a.x, a.y); g2d.lineTo(b.x, b.y); g2d.stroke();
          }
        }
      }
      for (const s of spores) {
        const pulse = 0.5 + 0.5 * Math.sin(t * 1.2 + s.ph);
        const c = s.tint ? seasonTint : pc;
        g2d.fillStyle = rgba(c, 0.25 + 0.45 * pulse);
        g2d.beginPath(); g2d.arc(s.x, s.y, s.r * (0.8 + 0.4 * pulse), 0, Math.PI * 2); g2d.fill();
      }

      /* weather overlays */
      if (env.cond === "rain" || env.cond === "storm") {
        g2d.strokeStyle = "rgba(160,205,235,0.28)";
        g2d.lineWidth = 1;
        for (const d of drops) {
          d.y += d.v * dt; d.x += d.v * 0.12 * dt;
          if (d.y > h + 30) { d.y = -30; d.x = Math.random() * w; }
          g2d.beginPath(); g2d.moveTo(d.x, d.y); g2d.lineTo(d.x - d.len * 0.12, d.y + d.len); g2d.stroke();
        }
        if (env.cond === "storm" && Math.random() < 0.004) {
          g2d.fillStyle = "rgba(190,215,255,0.10)";
          g2d.fillRect(0, 0, w, h);
        }
      } else if (env.cond === "snow") {
        for (const f of flakes) {
          f.y += f.v * dt; f.x += Math.sin(t + f.ph) * 14 * dt;
          if (f.y > h + 10) { f.y = -10; f.x = Math.random() * w; }
          g2d.fillStyle = "rgba(240,248,255,0.65)";
          g2d.beginPath(); g2d.arc(f.x, f.y, f.r, 0, Math.PI * 2); g2d.fill();
        }
      } else if (env.cond === "fog") {
        for (let i = 0; i < 3; i++) {
          const gy = h * (0.35 + i * 0.18) + Math.sin(t * 0.15 + i) * 12;
          const g = g2d.createLinearGradient(0, gy - 40, 0, gy + 40);
          g.addColorStop(0, "rgba(170,190,185,0)");
          g.addColorStop(0.5, "rgba(170,190,185,0.05)");
          g.addColorStop(1, "rgba(170,190,185,0)");
          g2d.fillStyle = g;
          g2d.fillRect(0, gy - 40, w, 80);
        }
      }

      if (!reduced) raf = requestAnimationFrame(frame);
    }

    const io = new IntersectionObserver((es) => { visible = es[0].isIntersecting; });
    io.observe(cv);

    resize();
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(frame);

    const visHandler = () => {
      if (document.hidden) cancelAnimationFrame(raf);
      else { last = performance.now(); raf = requestAnimationFrame(frame); }
    };
    document.addEventListener("visibilitychange", visHandler);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", visHandler);
      io.disconnect();
    };
    void visible;
  }, []);

  const clock = new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", {
    hour: "2-digit", minute: "2-digit", timeZone: env.tz,
  }).format(new Date());

  const CondIcon =
    env.cond === "rain" ? CloudRain : env.cond === "snow" ? CloudSnow :
    env.cond === "storm" ? CloudLightning : env.cond === "fog" ? CloudFog :
    env.cond === "clouds" ? Cloud : env.isDay ? Sun : Moon;

  const num = (n: number) =>
    new Intl.NumberFormat(locale === "fa" ? "fa-IR" : "en-US").format(n);

  return (
    <>
      <canvas
        ref={canvasRef}
        aria-hidden
        className="pointer-events-none fixed inset-0 z-0"
      />
      {/* environment engine chip */}
      <div className="glass fixed bottom-4 start-4 z-40 flex items-center gap-2.5 rounded-full px-3.5 py-2 text-[11px] text-mist shadow-2xl">
        <span className="relative flex size-2">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-jade-400 opacity-40" />
          <span className="relative inline-flex size-2 rounded-full bg-jade-400" />
        </span>
        <CondIcon className="size-3.5 text-ice" />
        <span className="text-frost/90">{strings.cond[env.cond]}</span>
        {env.tempC !== null && (
          <span className="num inline-flex items-center gap-0.5 text-frost/80">
            <Thermometer className="size-3 text-mist" />
            {num(env.tempC)}°
          </span>
        )}
        <span className="h-3 w-px bg-white/10" />
        <span className="num text-frost/90" suppressHydrationWarning>{clock}</span>
        <span className="hidden items-center gap-1 sm:inline-flex">
          <Wind className="size-3 text-mist" />
          {strings.seasons[env.season]} · {env.isDay ? strings.day : strings.night}
        </span>
        <span className="hidden h-3 w-px bg-white/10 md:block" />
        <span className="hidden max-w-40 truncate text-mist/80 md:block" title={env.tz}>
          {geoFallback ? strings.fallback : env.city}
        </span>
        <span className="sr-only">{strings.engine}</span>
      </div>
    </>
  );
}
