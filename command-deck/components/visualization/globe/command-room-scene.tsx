"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { clone as cloneSkinned } from "three/examples/jsm/utils/SkeletonUtils.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { AMBIENCE, SEASON_TINTS } from "@/lib/visualization/ambience";
import type { AmbiencePreset, SeasonPreset } from "@/lib/types";
import { createEarthHologram } from "./earth-hologram";
import { GRADE_SHADER, disposeObject, hash01, radialTexture } from "./scene-utils";
import { getMarketBus, type AssetId, type AssetQuote, type FeedStatus, type MarketSnapshot } from "@/lib/live/market-bus";
import {
  classifyWmo,
  computePortfolio,
  DEMO_HOLDINGS,
  fmtPct,
  fmtQty,
  fmtUsd,
  skyPhaseFromHour,
  tehranHour,
  tzClockParts,
  WALL_CLOCK_ZONES,
  type SkyPhase,
  type WeatherKind,
} from "@/lib/live/derive";
import { ROLE_ASSETS, type RoleId, type RoomTexts } from "@/lib/live/room-texts";

/* ------------------------------------------------------------------ */
/* palette + static config                                             */

const C = {
  bg: "#081221",
  panel: "#071019",
  dim: "rgba(170,200,232,0.78)",
  dimmer: "rgba(160,190,222,0.5)",
  green: "#3ee6a4",
  red: "#ff7d7d",
  amber: "#ffcf4d",
  gold: "#f2c94c",
  cyan: "#6fdcff",
  white: "#f2f7ff",
};

function font(weight: number, size: number): string {
  return `${weight} ${size}px Vazirmatn, "Segoe UI", Arial, sans-serif`;
}

function statusColor(status: FeedStatus): string {
  return status === "live" ? C.green : status === "stale" ? C.amber : "rgba(150,180,215,0.5)";
}

function hms(ms: number | null): string {
  return ms == null ? "--:--:--" : new Date(ms).toLocaleTimeString("en-GB");
}

function wrapLine(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (ctx.measureText(candidate).width > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

/** Desk → role mapping (the user's org chart: every person owns one job). */
const ROLE_DESKS: Array<{ role: RoleId; tint: number; accent: string }> = [
  { role: "gold", tint: 0xd4af37, accent: "#e8c352" },
  { role: "crypto", tint: 0x22d3ee, accent: "#59d3f2" },
  { role: "memecoin", tint: 0x34d399, accent: "#4ade80" },
  { role: "oil", tint: 0xf59e0b, accent: "#fbbf24" },
  { role: "eu", tint: 0x60a5fa, accent: "#7cb3ff" },
  { role: "us", tint: 0x818cf8, accent: "#a5b0ff" },
  { role: "asia", tint: 0xf472b6, accent: "#ff9dc9" },
  { role: "news", tint: 0x0ea5e9, accent: "#38bdf8" },
  { role: "whitehat", tint: 0x22c55e, accent: "#4ade80" },
  { role: "redteam", tint: 0xef4444, accent: "#f87171" },
  { role: "research", tint: 0xa78bfa, accent: "#c4b5fd" },
  { role: "liaison", tint: 0xeab308, accent: "#facc15" },
];

const GRID_TILES: AssetId[] = ["XAU", "WTI", "BTC", "DOGE", "DAX", "IXIC", "N225", "SSE"];

const PHASE_SKY: Record<SkyPhase, { top: number; bottom: number; sunI: number; stars: number; glow: number; sunColor: number; elev: number }> = {
  night: { top: 0x03050c, bottom: 0x0a1222, sunI: 0, stars: 1, glow: 1, sunColor: 0xffffff, elev: -0.25 },
  dawn: { top: 0x1b2a4e, bottom: 0xd08248, sunI: 0.9, stars: 0.12, glow: 0.5, sunColor: 0xffb066, elev: 0.1 },
  day: { top: 0x4a7ec2, bottom: 0xc9dcf0, sunI: 1, stars: 0, glow: 0.06, sunColor: 0xfff2d8, elev: 0.85 },
  dusk: { top: 0x251f40, bottom: 0xd8763e, sunI: 0.85, stars: 0.18, glow: 0.55, sunColor: 0xff8a4a, elev: 0.09 },
};

/* ------------------------------------------------------------------ */
/* canvas textures                                                     */

function floorTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.fillStyle = "#070b14";
    ctx.fillRect(0, 0, 1024, 1024);
    ctx.translate(512, 512);
    ctx.strokeStyle = "rgba(90,130,190,0.07)";
    ctx.lineWidth = 1;
    for (let i = -512; i <= 512; i += 32) {
      ctx.beginPath();
      ctx.moveTo(i, -512);
      ctx.lineTo(i, 512);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-512, i);
      ctx.lineTo(512, i);
      ctx.stroke();
    }
    for (const [r, color, w] of [
      [120, "rgba(212,175,55,0.30)", 3],
      [190, "rgba(34,211,238,0.16)", 2],
      [260, "rgba(90,130,190,0.12)", 2],
      [340, "rgba(212,175,55,0.14)", 2],
      [430, "rgba(90,130,190,0.10)", 2],
      [500, "rgba(212,175,55,0.20)", 3],
    ] as const) {
      ctx.strokeStyle = color;
      ctx.lineWidth = w;
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.strokeStyle = "rgba(90,130,190,0.06)";
    ctx.lineWidth = 1.5;
    for (let a = 0; a < 24; a += 1) {
      const ang = (a / 24) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(Math.cos(ang) * 120, Math.sin(ang) * 120);
      ctx.lineTo(Math.cos(ang) * 505, Math.sin(ang) * 505);
      ctx.stroke();
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

/** night-lit tower facade for the city outside the glass wall */
function buildingTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.fillStyle = "#131c2a";
    ctx.fillRect(0, 0, 64, 128);
    for (let iy = 0; iy < 14; iy += 1) {
      for (let ix = 0; ix < 6; ix += 1) {
        const lit = hash01(ix * 7 + iy * 13 + 3) > 0.52;
        ctx.fillStyle = lit
          ? `rgba(255,214,150,${(0.45 + hash01(ix * 3 + iy * 29) * 0.55).toFixed(2)})`
          : "rgba(34,46,66,0.9)";
        ctx.fillRect(4 + ix * 10, 5 + iy * 9, 6, 5);
      }
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** A redrawable canvas bound to a THREE texture (screens, boards, tablets). */
class LiveCanvas {
  readonly texture: THREE.CanvasTexture;
  private readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D | null;
  constructor(private readonly w: number, private readonly h: number) {
    this.canvas = document.createElement("canvas");
    this.canvas.width = w;
    this.canvas.height = h;
    this.ctx = this.canvas.getContext("2d");
    this.texture = new THREE.CanvasTexture(this.canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.anisotropy = 4;
  }
  draw(fn: (ctx: CanvasRenderingContext2D, w: number, h: number) => void): void {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.w, this.h);
    fn(this.ctx, this.w, this.h);
    this.texture.needsUpdate = true;
  }
  dispose(): void {
    this.texture.dispose();
  }
}

/* ------------------------------------------------------------------ */
/* screen painters (real data when live, honest blanks when not)       */

function paintHeader(ctx: CanvasRenderingContext2D, w: number, h: number, accent: string, title: string, rtl: boolean): void {
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "rgba(10,18,32,0.9)";
  ctx.fillRect(0, 0, w, h * 0.15);
  ctx.fillStyle = accent;
  ctx.globalAlpha = 0.28;
  ctx.fillRect(0, h * 0.15 - 3, w, 3);
  ctx.globalAlpha = 1;
  ctx.font = font(700, 32);
  ctx.fillStyle = C.white;
  ctx.direction = rtl ? "rtl" : "ltr";
  ctx.textAlign = rtl ? "right" : "left";
  ctx.textBaseline = "middle";
  ctx.fillText(title, rtl ? w - 22 : 22, h * 0.077);
  ctx.direction = "ltr";
}

function paintFooter(ctx: CanvasRenderingContext2D, w: number, h: number, status: FeedStatus, label: string, detail: string): void {
  ctx.fillStyle = "rgba(4,8,16,0.92)";
  ctx.fillRect(0, h * 0.9, w, h * 0.1);
  const y = h * 0.95;
  ctx.fillStyle = statusColor(status);
  ctx.beginPath();
  ctx.arc(22, y, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = font(700, 19);
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillStyle = statusColor(status);
  ctx.fillText(label, 38, y);
  ctx.font = font(500, 17);
  ctx.fillStyle = C.dimmer;
  ctx.fillText(detail, 190, y);
}

function drawSpark(ctx: CanvasRenderingContext2D, spark: number[], x: number, y: number, w: number, h: number, color: string): void {
  if (spark.length < 2) return;
  let min = Infinity;
  let max = -Infinity;
  for (const v of spark) {
    if (v < min) min = v;
    if (v > max) max = v;
  }
  const span = max - min || 1;
  ctx.strokeStyle = color;
  ctx.globalAlpha = 0.85;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  spark.forEach((v, i) => {
    const px = x + (i / (spark.length - 1)) * w;
    const py = y + h - ((v - min) / span) * h;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.globalAlpha = 1;
}

function drawBars(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, t: number, seed: number, color: string): void {
  const n = 12;
  for (let i = 0; i < n; i += 1) {
    const bh = h * (0.2 + 0.8 * Math.abs(Math.sin(t * 1.4 + i * 0.9 + seed)));
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.5;
    ctx.fillRect(x + (i * w) / n + 3, y + h - bh, w / n - 6, bh);
  }
  ctx.globalAlpha = 1;
}

function drawMarketConsole(
  lc: LiveCanvas,
  texts: RoomTexts,
  roleLabel: string,
  accent: string,
  quotes: AssetQuote[],
  t: number,
): void {
  lc.draw((ctx, w, h) => {
    const rtl = texts.locale === "fa";
    paintHeader(ctx, w, h, accent, roleLabel, rtl);
    const live = quotes.some((q) => q.status === "live");
    if (!live) {
      ctx.font = font(800, 72);
      ctx.fillStyle = C.dimmer;
      ctx.textAlign = "center";
      ctx.fillText("—", w / 2, h * 0.42);
      ctx.font = font(600, 26);
      ctx.fillStyle = C.amber;
      ctx.fillText(texts.market.offline, w / 2, h * 0.56);
      drawBars(ctx, 30, h * 0.62, w - 60, h * 0.2, t, 3, accent);
      paintFooter(ctx, w, h, "offline", texts.market.offline, texts.market.notConnected);
      return;
    }
    const rows = quotes.slice(0, 3);
    const rowH = (h * 0.72) / rows.length;
    rows.forEach((q, i) => {
      const top = h * 0.17 + i * rowH;
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.font = font(600, 26);
      ctx.fillStyle = C.dim;
      ctx.fillText(q.label, 24, top + 28);
      if (q.price != null) {
        ctx.font = font(800, 38);
        ctx.fillStyle = C.white;
        ctx.fillText(fmtUsd(q.price), 24, top + 66);
      }
      ctx.font = font(700, 27);
      ctx.fillStyle = (q.change24h ?? 0) >= 0 ? C.green : C.red;
      ctx.textAlign = "right";
      ctx.fillText(fmtPct(q.change24h), w - 24, top + 66);
      if (q.spark.length > 1) {
        drawSpark(ctx, q.spark, 24, top + 68, w - 48, rowH - 82, (q.change24h ?? 0) >= 0 ? C.green : C.red);
      } else {
        drawBars(ctx, 24, top + 68, w - 48, rowH - 84, t, i * 5, accent);
      }
      // live trade tape under the first asset
      if (i === 0 && q.tape.length > 0) {
        ctx.font = font(500, 19);
        ctx.textAlign = "left";
        ctx.fillStyle = C.dimmer;
        ctx.fillText(texts.market.tape, 24, top + rowH - 8);
        q.tape.slice(0, 2).forEach((tick, k) => {
          const tx = w / 2 + 10 + k * (w / 2 - 40);
          ctx.fillStyle = tick.buyerMaker ? C.red : C.green;
          ctx.fillRect(tx - 12, top + rowH - 20, 6, 6);
          ctx.fillStyle = C.dim;
          ctx.font = font(500, 16);
          ctx.textAlign = "left";
          ctx.fillText(`${fmtQty(tick.qty)} @ ${fmtUsd(tick.price)}`, tx, top + rowH - 8);
        });
      }
    });
    const primary = rows[0];
    paintFooter(
      ctx,
      w,
      h,
      primary.status,
      primary.status === "live" ? texts.market.live : texts.market.stale,
      `${primary.source ?? ""} · ${hms(primary.updatedAt)}`,
    );
  });
}

function drawInternalConsole(lc: LiveCanvas, texts: RoomTexts, roleLabel: string, accent: string, t: number): void {
  lc.draw((ctx, w, h) => {
    const rtl = texts.locale === "fa";
    paintHeader(ctx, w, h, accent, roleLabel, rtl);
    ctx.textAlign = "center";
    ctx.font = font(800, 42);
    ctx.fillStyle = C.gold;
    ctx.fillText(texts.market.sample, w / 2, h * 0.38);
    ctx.font = font(500, 20);
    ctx.fillStyle = C.dimmer;
    const notice = wrapLine(ctx, texts.panel.sampleNotice, w - 80).slice(0, 2);
    notice.forEach((line, i) => ctx.fillText(line, w / 2, h * 0.5 + i * 24));
    drawBars(ctx, 30, h * 0.6, w - 60, h * 0.22, t, 7, accent);
    ctx.strokeStyle = accent;
    ctx.globalAlpha = 0.4;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let x = 0; x <= w - 60; x += 6) {
      const y = h * 0.52 + Math.sin(x * 0.045 + t * 2.4) * 9 * Math.sin(x * 0.011 + t * 0.7);
      if (x === 0) ctx.moveTo(30 + x, y);
      else ctx.lineTo(30 + x, y);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;
    paintFooter(ctx, w, h, "stale", texts.market.sample, "AHOS · paper dataset 2026-10");
  });
}

function drawNewsConsole(lc: LiveCanvas, texts: RoomTexts, snap: MarketSnapshot, t: number): void {
  lc.draw((ctx, w, h) => {
    const rtl = texts.locale === "fa";
    paintHeader(ctx, w, h, "#38bdf8", texts.market.newsTitle, rtl);
    if (snap.news.status !== "live" || snap.news.items.length === 0) {
      ctx.textAlign = "center";
      ctx.font = font(600, 20);
      ctx.fillStyle = C.dimmer;
      const note = wrapLine(ctx, texts.market.offlineNews, w - 80).slice(0, 2);
      note.forEach((line, i) => ctx.fillText(line, w / 2, h * 0.42 + i * 26));
      drawBars(ctx, 30, h * 0.58, w - 60, h * 0.24, t, 11, "#38bdf8");
      paintFooter(ctx, w, h, "offline", texts.market.offline, texts.market.notConnected);
      return;
    }
    ctx.direction = rtl ? "rtl" : "ltr";
    ctx.textAlign = rtl ? "right" : "left";
    ctx.font = font(500, 21);
    ctx.fillStyle = C.white;
    let y = h * 0.24;
    for (const item of snap.news.items.slice(0, 4)) {
      const lines = wrapLine(ctx, item.title, w - 90).slice(0, 2);
      ctx.fillStyle = C.gold;
      ctx.fillRect(rtl ? w - 40 : 28, y - 12, 7, 7);
      lines.forEach((line, i) => ctx.fillText(line, rtl ? w - 56 : 46, y + i * 24));
      y += lines.length * 24 + 18;
    }
    ctx.direction = "ltr";
    paintFooter(ctx, w, h, "live", texts.market.live, `${snap.news.source ?? ""} · ${hms(snap.news.updatedAt)}`);
  });
}

function drawLiaisonConsole(lc: LiveCanvas, texts: RoomTexts, snap: MarketSnapshot, t: number): void {
  lc.draw((ctx, w, h) => {
    const rtl = texts.locale === "fa";
    paintHeader(ctx, w, h, "#facc15", texts.shortRoles.liaison, rtl);
    const totals = computePortfolio(snap.assets);
    ctx.textAlign = "center";
    if (totals.totalUsd == null) {
      ctx.font = font(800, 52);
      ctx.fillStyle = C.dimmer;
      ctx.fillText("—", w / 2, h * 0.42);
      ctx.font = font(600, 19);
      ctx.fillStyle = C.amber;
      ctx.fillText(texts.market.offline, w / 2, h * 0.56);
    } else {
      ctx.font = font(800, 52);
      ctx.fillStyle = C.gold;
      ctx.fillText(`$${fmtUsd(totals.totalUsd)}`, w / 2, h * 0.36);
      if (totals.pnlTodayUsd != null) {
        ctx.font = font(800, 36);
        ctx.fillStyle = totals.pnlTodayUsd >= 0 ? C.green : C.red;
        ctx.fillText(`${totals.pnlTodayUsd >= 0 ? "▲ +" : "▼ "}$${fmtUsd(totals.pnlTodayUsd)}`, w / 2, h * 0.52);
      }
      ctx.font = font(500, 16);
      ctx.fillStyle = C.dimmer;
      ctx.fillText(`${totals.liveAssets}/${totals.totalAssets} · ${texts.market.demoNote}`, w / 2, h * 0.64);
    }
    drawBars(ctx, 30, h * 0.68, w - 60, h * 0.14, t, 5, "#facc15");
    paintFooter(
      ctx,
      w,
      h,
      totals.totalUsd == null ? "offline" : "live",
      totals.totalUsd == null ? texts.market.offline : texts.market.live,
      texts.market.demoNote,
    );
  });
}

function drawPortfolioBoard(lc: LiveCanvas, texts: RoomTexts, snap: MarketSnapshot): void {
  lc.draw((ctx, w, h) => {
    ctx.fillStyle = C.panel;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(212,175,55,0.45)";
    ctx.lineWidth = 4;
    ctx.strokeRect(6, 6, w - 12, h - 12);
    const rtl = texts.locale === "fa";
    ctx.direction = rtl ? "rtl" : "ltr";
    ctx.textAlign = rtl ? "right" : "left";
    ctx.textBaseline = "alphabetic";
    ctx.font = font(700, 40);
    ctx.fillStyle = C.white;
    ctx.fillText(texts.market.portfolioTitle, rtl ? w - 36 : 36, 62);
    ctx.font = font(500, 22);
    ctx.fillStyle = C.dimmer;
    ctx.fillText(texts.market.demoNote, rtl ? w - 36 : 36, 100);
    ctx.direction = "ltr";

    const totals = computePortfolio(snap.assets);
    const cx = rtl ? w - 36 : 36;
    ctx.textAlign = rtl ? "right" : "left";
    if (totals.totalUsd == null) {
      ctx.font = font(900, 130);
      ctx.fillStyle = C.dimmer;
      ctx.fillText("—", cx, 260);
      ctx.font = font(600, 30);
      ctx.fillStyle = C.amber;
      ctx.fillText(texts.market.offline, cx, 320);
    } else {
      ctx.font = font(900, 122);
      ctx.fillStyle = C.gold;
      ctx.fillText(`$${fmtUsd(totals.totalUsd)}`, cx, 262);
      if (totals.pnlTodayUsd != null) {
        const pos = totals.pnlTodayUsd >= 0;
        ctx.font = font(800, 56);
        ctx.fillStyle = pos ? C.green : C.red;
        ctx.fillText(`${pos ? "▲ +" : "▼ −"}$${fmtUsd(Math.abs(totals.pnlTodayUsd))}`, cx, 350);
        ctx.font = font(500, 26);
        ctx.fillStyle = C.dim;
        ctx.fillText(texts.market.pnl, cx, 402);
      }
    }

    // holdings table (right side)
    const tableX = w / 2 + 40;
    const cellW = (w - tableX - 36) / 2;
    ctx.textAlign = "left";
    ctx.font = font(700, 26);
    ctx.fillStyle = C.dim;
    ctx.fillText(texts.market.holdings, tableX, 62);
    DEMO_ROWS.forEach((row, i) => {
      const col = i % 2;
      const rowIdx = Math.floor(i / 2);
      const x = tableX + col * cellW;
      const y = 110 + rowIdx * 92;
      const q = snap.assets[row.asset as AssetId];
      ctx.fillStyle = "rgba(12,20,36,0.85)";
      ctx.fillRect(x, y - 30, cellW - 22, 78);
      ctx.font = font(600, 21);
      ctx.fillStyle = C.dim;
      ctx.fillText(row.label, x + 16, y);
      if (q?.price != null) {
        ctx.font = font(700, 26);
        ctx.fillStyle = C.white;
        ctx.fillText(`$${fmtUsd(row.qty * q.price)}`, x + 16, y + 34);
        ctx.font = font(500, 17);
        ctx.fillStyle = C.dimmer;
        ctx.fillText(`${fmtQty(row.qty)} × ${fmtUsd(q.price)}`, x + 16, y + 56 - 22);
      } else {
        ctx.font = font(700, 26);
        ctx.fillStyle = C.dimmer;
        ctx.fillText("—", x + 16, y + 34);
      }
    });
    const anyLive = totals.liveAssets > 0;
    paintFooter(
      ctx,
      w,
      h,
      anyLive ? "live" : "offline",
      anyLive ? texts.market.live : texts.market.offline,
      anyLive ? `${totals.liveAssets}/${totals.totalAssets} · ${hms(Date.now())}` : texts.market.notConnected,
    );
  });
}

const DEMO_ROWS: Array<{ asset: string; qty: number; label: string }> = []; // filled at redraw time (locale-aware)

function drawMarketGrid(lc: LiveCanvas, texts: RoomTexts, snap: MarketSnapshot, t: number): void {
  lc.draw((ctx, w, h) => {
    ctx.fillStyle = C.panel;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(89,211,242,0.4)";
    ctx.lineWidth = 4;
    ctx.strokeRect(6, 6, w - 12, h - 12);
    const rtl = texts.locale === "fa";
    ctx.direction = rtl ? "rtl" : "ltr";
    ctx.textAlign = rtl ? "right" : "left";
    ctx.font = font(700, 36);
    ctx.fillStyle = C.white;
    ctx.fillText(texts.market.gridTitle, rtl ? w - 36 : 36, 58);
    ctx.direction = "ltr";
    const liveCount = GRID_TILES.filter((id) => snap.assets[id].status === "live").length;
    ctx.font = font(600, 24);
    ctx.fillStyle = liveCount > 0 ? C.green : C.amber;
    ctx.textAlign = "left";
    ctx.fillText(liveCount > 0 ? `● ${liveCount}/${GRID_TILES.length}` : `○ 0/${GRID_TILES.length}`, 36, 58);

    const tileW = (w - 80 - 3 * 24) / 4;
    const tileH = (h - 130 - 24) / 2;
    GRID_TILES.forEach((id, i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = 40 + col * (tileW + 24);
      const y = 96 + row * (tileH + 24);
      const q = snap.assets[id];
      const name = texts.market.assets[id];
      ctx.fillStyle = "rgba(10,18,32,0.9)";
      ctx.fillRect(x, y, tileW, tileH);
      ctx.strokeStyle = q.status === "live" ? "rgba(52,211,153,0.4)" : "rgba(150,180,215,0.16)";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, tileW, tileH);
      ctx.direction = rtl ? "rtl" : "ltr";
      ctx.textAlign = rtl ? "right" : "left";
      ctx.font = font(600, 22);
      ctx.fillStyle = C.dim;
      ctx.fillText(name, rtl ? x + tileW - 14 : x + 14, y + 32);
      ctx.direction = "ltr";
      if (q.status === "live" && q.price != null) {
        ctx.textAlign = "left";
        ctx.font = font(800, 38);
        ctx.fillStyle = C.white;
        ctx.fillText(fmtUsd(q.price), x + 14, y + 84);
        ctx.font = font(700, 24);
        ctx.fillStyle = (q.change24h ?? 0) >= 0 ? C.green : C.red;
        ctx.textAlign = "right";
        ctx.fillText(fmtPct(q.change24h), x + tileW - 14, y + 84);
        drawSpark(ctx, q.spark, x + 14, y + tileH - 56, tileW - 28, 40, (q.change24h ?? 0) >= 0 ? C.green : C.red);
      } else {
        ctx.textAlign = "center";
        ctx.font = font(700, 24);
        ctx.fillStyle = C.amber;
        ctx.fillText(texts.market.offline, x + tileW / 2, y + tileH / 2);
        drawBars(ctx, x + 14, y + tileH - 52, tileW - 28, 40, t, i * 3, "#59d3f2");
      }
    });
  });
}

function drawClockBoard(lc: LiveCanvas, texts: RoomTexts, now: Date): void {
  lc.draw((ctx, w, h) => {
    ctx.fillStyle = C.panel;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(89,211,242,0.5)";
    ctx.lineWidth = 4;
    ctx.strokeRect(6, 6, w - 12, h - 12);
    const rtl = texts.locale === "fa";
    ctx.direction = rtl ? "rtl" : "ltr";
    ctx.textAlign = rtl ? "right" : "left";
    ctx.font = font(700, 34);
    ctx.fillStyle = C.white;
    ctx.fillText(texts.market.clockTitle, rtl ? w - 30 : 30, 52);
    ctx.font = font(500, 20);
    ctx.fillStyle = C.dimmer;
    ctx.fillText(texts.market.clockNote, rtl ? w - 30 : 30, 86);
    ctx.direction = "ltr";
    const tileW = (w - 72 - 20) / 2;
    const tileH = (h - 116 - 20) / 2;
    WALL_CLOCK_ZONES.forEach((zone, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 36 + col * (tileW + 20);
      const y = 100 + row * (tileH + 20);
      const parts = tzClockParts(zone.tz, now);
      const isTehran = zone.id === "tehran";
      ctx.fillStyle = "rgba(10,18,32,0.9)";
      ctx.fillRect(x, y, tileW, tileH);
      ctx.strokeStyle = isTehran ? "rgba(212,175,55,0.55)" : "rgba(89,211,242,0.3)";
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, tileW, tileH);
      ctx.textAlign = "left";
      ctx.font = font(600, 24);
      ctx.fillStyle = isTehran ? C.gold : C.dim;
      ctx.fillText(texts.market.clocks[zone.id], x + 18, y + 34);
      ctx.font = font(800, 54);
      ctx.fillStyle = C.white;
      ctx.fillText(`${parts.h}:${parts.m}:${parts.s}`, x + 18, y + tileH - 22);
      ctx.font = font(400, 16);
      ctx.fillStyle = C.dimmer;
      ctx.textAlign = "right";
      ctx.fillText(zone.tz, x + tileW - 16, y + tileH - 22);
    });
  });
}

function drawTablet(lc: LiveCanvas, shortLabel: string, accent: string, quote: AssetQuote | null, t: number): void {
  lc.draw((ctx, w, h) => {
    ctx.fillStyle = "#050a12";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = accent;
    ctx.fillRect(0, 0, w, 8);
    if (quote?.status === "live" && quote.price != null) {
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.font = font(800, 40);
      ctx.fillStyle = C.white;
      ctx.fillText(fmtUsd(quote.price), 14, 62);
      ctx.font = font(700, 24);
      ctx.fillStyle = (quote.change24h ?? 0) >= 0 ? C.green : C.red;
      ctx.fillText(fmtPct(quote.change24h), 14, 88);
      drawSpark(ctx, quote.spark, 14, 100, w - 28, 52, accent);
      ctx.font = font(600, 19);
      ctx.fillStyle = statusColor(quote.status);
      ctx.fillText("● LIVE", 14, h - 12);
    } else {
      ctx.font = font(700, 26);
      ctx.fillStyle = C.dim;
      ctx.textAlign = "left";
      ctx.fillText(shortLabel, 14, 48);
      drawBars(ctx, 14, 60, w - 28, h - 84, t, 4, accent);
      ctx.font = font(600, 18);
      ctx.fillStyle = "rgba(160,190,222,0.6)";
      ctx.fillText("○ —", 14, h - 12);
    }
  });
}

/* ------------------------------------------------------------------ */

/**
 * AHOS operations room — cinematic 3D command floor:
 *  - 12 role consoles with LIVE public-market canvases (or honest offline),
 *  - rigged animated staff (open-source GLB humans) with real walk cycles,
 *  - a glass wall onto a procedurally built city driven by REAL weather
 *    (Open-Meteo, Dezful/Khuzestan) and the real Tehran clock,
 *  - sliding entrance doors with guards + commuter traffic,
 *  - wall boards: demo-portfolio × live prices, world market grid, 4-zone clock,
 *  - commander FPV camera mode. Data honesty: live values only from the named
 *    public sources; when offline, screens show blanks — never fake numbers.
 */
export default function CommandRoomScene({
  preset,
  season,
  view,
  texts,
  onRoleFocus,
  onFail,
}: {
  preset: AmbiencePreset;
  season: SeasonPreset;
  view: "room" | "fpv";
  texts: RoomTexts;
  onRoleFocus: (role: RoleId) => void;
  onFail: () => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const textsRef = useRef(texts);
  textsRef.current = texts;
  const viewRef = useRef<"room" | "fpv">(view);
  viewRef.current = view;
  const roleFocusRef = useRef(onRoleFocus);
  roleFocusRef.current = onRoleFocus;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let disposed = false;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    } catch {
      onFail();
      return;
    }
    if (!renderer.getContext()) {
      onFail();
      return;
    }

    const amb = AMBIENCE[preset].three;
    const seasonSpec = SEASON_TINTS[season];
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0x04060d, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x05070d, 0.014);
    const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 160);
    let targetFov = 46;

    const liveCanvases: LiveCanvas[] = [];

    /* ---------------- lights ---------------- */
    scene.add(new THREE.AmbientLight(0x8fa3c8, 1.25));
    scene.add(new THREE.HemisphereLight(0x33415e, 0x05070c, 1.2));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.6);
    keyLight.position.set(3, 6, 2);
    const rimLight = new THREE.DirectionalLight(amb.rim, 0.8);
    rimLight.position.set(-5, 3, -6);
    const holoLight = new THREE.PointLight(0x7fd8e8, 18, 9, 2);
    holoLight.position.set(0, 2.4, 0);
    const spotDesks = new THREE.SpotLight(0xbfd4ff, 120, 18, 0.95, 0.5, 1.5);
    spotDesks.position.set(0, 4.5, 4.5);
    spotDesks.target.position.set(0, 0.9, 3.4);
    const spotPodium = new THREE.SpotLight(0xd4af37, 55, 12, 0.75, 0.55, 1.5);
    spotPodium.position.set(0, 4.5, -3.4);
    spotPodium.target.position.set(0, 1.2, 0);
    const windowSun = new THREE.DirectionalLight(0xffe0b8, 0.0);
    windowSun.position.set(26, 13, 0);
    windowSun.target.position.set(0, 1, 0);
    const deskRingLights: THREE.PointLight[] = [];
    for (const [lx, lz] of [[3.9, 3.9], [-3.9, 3.9], [3.9, -3.9], [-3.9, -3.9]]) {
      const pl = new THREE.PointLight(0xbfd4ff, 46, 13, 1.8);
      pl.position.set(lx, 3.9, lz);
      deskRingLights.push(pl);
    }
    const citySpill = new THREE.PointLight(0x9fc4ff, 0, 15, 1.7);
    citySpill.position.set(8.6, 2.6, 0);
    scene.add(keyLight, rimLight, holoLight, spotDesks, spotDesks.target, spotPodium, spotPodium.target, windowSun, windowSun.target, citySpill, ...deskRingLights);

    const LIGHT_DIR = new THREE.Vector3(2.4, 3.2, 2.6).normalize();

    /* ---------------- holographic Earth on the podium ---------------- */
    const holo = createEarthHologram(renderer, {
      palette: {
        atmosphere: amb.atmosphere,
        sun: amb.key,
        tint: seasonSpec.tint,
        tintStrength: seasonSpec.strength,
      },
      lightDir: LIGHT_DIR,
      onFail,
      platform: true,
    });
    holo.group.position.set(0, 2.28, 0);
    holo.group.scale.setScalar(0.86);
    scene.add(holo.group);

    /* ---------------- floor / dais / ceiling ---------------- */
    const floorTex = floorTexture();
    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(11.4, 72),
      new THREE.MeshStandardMaterial({
        map: floorTex,
        color: 0xbfd2e8,
        metalness: 0.45,
        roughness: 0.3,
        emissive: 0x0a1424,
        emissiveMap: floorTex,
        emissiveIntensity: 0.6,
      }),
    );
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const dark = new THREE.MeshStandardMaterial({ color: 0x0b1120, metalness: 0.55, roughness: 0.5 });
    const darker = new THREE.MeshStandardMaterial({ color: 0x070c16, metalness: 0.4, roughness: 0.6 });
    const goldMat = new THREE.MeshStandardMaterial({
      color: 0x2a2415, metalness: 0.7, roughness: 0.35, emissive: 0xd4af37, emissiveIntensity: 0.55,
    });

    const dais = new THREE.Mesh(new THREE.CylinderGeometry(2.25, 2.45, 0.16, 64), dark);
    dais.position.y = 0.08;
    scene.add(dais);
    const daisTrim = new THREE.Mesh(new THREE.TorusGeometry(2.25, 0.02, 8, 96), goldMat);
    daisTrim.rotation.x = Math.PI / 2;
    daisTrim.position.y = 0.17;
    scene.add(daisTrim);
    const innerRing = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.012, 8, 96), new THREE.MeshStandardMaterial({
      color: 0x103038, emissive: 0x22d3ee, emissiveIntensity: 0.8, metalness: 0.4, roughness: 0.4,
    }));
    innerRing.rotation.x = Math.PI / 2;
    innerRing.position.y = 0.012;
    scene.add(innerRing);

    const column = new THREE.Mesh(
      new THREE.CylinderGeometry(0.34, 0.5, 1.35, 32, 1, true),
      new THREE.MeshBasicMaterial({
        color: 0x6fd8ec, transparent: true, opacity: 0.06, blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide, depthWrite: false,
      }),
    );
    column.position.y = 0.85;
    scene.add(column);

    const ceiling = new THREE.Mesh(new THREE.CircleGeometry(11.4, 48), darker);
    ceiling.rotation.x = Math.PI / 2;
    ceiling.position.y = 4.9;
    scene.add(ceiling);
    const truss = new THREE.Mesh(new THREE.TorusGeometry(6.4, 0.07, 8, 96), dark);
    truss.rotation.x = Math.PI / 2;
    truss.position.y = 4.8;
    scene.add(truss);
    const lightStripMat = new THREE.MeshStandardMaterial({
      color: 0x0d1522, emissive: 0x9fc0ff, emissiveIntensity: 0.3, metalness: 0.2, roughness: 0.4,
    });
    for (let i = 0; i < 3; i += 1) {
      const strip = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.06, 0.26), lightStripMat);
      strip.position.set(0, 4.86, -3.4 + i * 3.4);
      scene.add(strip);
    }

    /* ---------------- walls (with a real window band + door gap) ---------------- */
    const wallRadius = 9.9;
    const sideWallMat = new THREE.MeshStandardMaterial({ color: 0x080d18, metalness: 0.3, roughness: 0.7, side: THREE.BackSide });
    const addWallSeg = (thetaStart: number, len: number, height: number, y: number, radius: number, mat: THREE.Material) => {
      const seg = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, height, 48, 1, true, thetaStart, len), mat);
      seg.position.y = y;
      scene.add(seg);
      return seg;
    };
    // +X window band: glass between parapet and header
    const WIN_START = Math.PI / 2 - 0.5;
    const WIN_LEN = 1.0;
    const glass = new THREE.Mesh(
      new THREE.CylinderGeometry(10.55, 10.55, 3.0, 48, 1, true, WIN_START, WIN_LEN),
      new THREE.MeshBasicMaterial({ color: 0x9cc8ff, transparent: true, opacity: 0.09, side: THREE.DoubleSide, depthWrite: false }),
    );
    glass.position.y = 2.4;
    scene.add(glass);
    addWallSeg(WIN_START - 0.05, WIN_LEN + 0.1, 0.95, 0.475, 10.6, sideWallMat); // parapet
    addWallSeg(WIN_START - 0.05, WIN_LEN + 0.1, 1.05, 4.37, 10.6, sideWallMat); // header
    const mullionMat = new THREE.MeshStandardMaterial({ color: 0x111a2a, metalness: 0.6, roughness: 0.4 });
    for (let i = 0; i <= 8; i += 1) {
      const a = WIN_START + (i / 8) * WIN_LEN;
      const mullion = new THREE.Mesh(new THREE.BoxGeometry(0.09, 3.0, 0.12), mullionMat);
      mullion.position.set(Math.sin(a) * 10.5, 2.4, Math.cos(a) * 10.5);
      mullion.rotation.y = a;
      scene.add(mullion);
    }
    for (const ry of [0.95, 3.9]) {
      const rail = new THREE.Mesh(
        new THREE.CylinderGeometry(10.5, 10.5, 0.12, 48, 1, true, WIN_START, WIN_LEN),
        mullionMat,
      );
      rail.position.y = ry;
      scene.add(rail);
    }
    // remaining solid walls
    addWallSeg(WIN_START + WIN_LEN, Math.PI - 0.55 - (WIN_START + WIN_LEN), 4.9, 2.45, 10.6, sideWallMat);
    // -X side: solid up to the door gap, then solid to +Z
    const DOOR_CENTER = (3 * Math.PI) / 2;
    const DOOR_HALF = 0.092; // ≈1.9 m opening
    addWallSeg(Math.PI + 0.55, DOOR_CENTER - DOOR_HALF - (Math.PI + 0.55), 4.9, 2.45, 10.6, sideWallMat);
    addWallSeg(DOOR_CENTER + DOOR_HALF, Math.PI * 2 - (DOOR_CENTER + DOOR_HALF), 4.9, 2.45, 10.6, sideWallMat);
    const stripMat = new THREE.MeshStandardMaterial({
      color: 0x0d1522, emissive: 0x22d3ee, emissiveIntensity: 0.9, metalness: 0.3, roughness: 0.4,
    });
    for (const angleDeg of [96, 130, 233, 262, 300]) {
      const a = (angleDeg * Math.PI) / 180;
      const pilaster = new THREE.Mesh(new THREE.BoxGeometry(0.1, 3.2, 0.34), stripMat);
      pilaster.position.set(Math.sin(a) * 10.45, 2.0, Math.cos(a) * 10.45);
      pilaster.rotation.y = a + Math.PI;
      scene.add(pilaster);
    }

    /* ---------------- the city outside the glass ---------------- */
    const cityGroup = new THREE.Group();
    scene.add(cityGroup);
    const cityTextures: THREE.Texture[] = [];
    const cityGround = new THREE.Mesh(
      new THREE.PlaneGeometry(140, 100),
      new THREE.MeshStandardMaterial({ color: 0x0a0f1a, roughness: 0.95, metalness: 0.1 }),
    );
    cityGround.rotation.x = -Math.PI / 2;
    cityGround.position.set(30, -0.03, 0);
    cityGroup.add(cityGround);

    const bTex = buildingTexture();
    cityTextures.push(bTex);
    const bMat = new THREE.MeshStandardMaterial({
      color: 0x93a7c2, map: bTex, emissive: 0xffc98a, emissiveMap: bTex, emissiveIntensity: 0.12, roughness: 0.85, metalness: 0.2,
    });
    const bGeo = new THREE.BoxGeometry(1, 1, 1);
    bGeo.translate(0, 0.5, 0);
    const BUILDINGS = 130;
    const towers = new THREE.InstancedMesh(bGeo, bMat, BUILDINGS);
    const mtx = new THREE.Matrix4();
    const qt = new THREE.Quaternion();
    const vp = new THREE.Vector3();
    const vs = new THREE.Vector3();
    for (let i = 0; i < BUILDINGS; i += 1) {
      const az = -1.35 + (i / BUILDINGS) * 2.7 + (hash01(i * 17 + 2) - 0.5) * 0.1;
      const radius = 16.5 + hash01(i * 7 + 1) * 26;
      const h = 2.4 + Math.pow(hash01(i * 13 + 5), 1.6) * 17;
      const bw = 1.7 + hash01(i * 23 + 9) * 2.6;
      const bd = 1.7 + hash01(i * 31 + 4) * 2.6;
      vp.set(Math.cos(az) * radius, 0, Math.sin(az) * radius);
      vs.set(bw, h, bd);
      mtx.compose(vp, qt, vs);
      towers.setMatrixAt(i, mtx);
    }
    towers.instanceMatrix.needsUpdate = true;
    cityGroup.add(towers);

    const river = new THREE.Mesh(
      new THREE.PlaneGeometry(40, 3.6),
      new THREE.MeshStandardMaterial({ color: 0x0a1c33, metalness: 0.7, roughness: 0.25, emissive: 0x0e2c50, emissiveIntensity: 0.5 }),
    );
    river.rotation.x = -Math.PI / 2;
    river.rotation.z = 0.4;
    river.position.set(28, 0.02, 9);
    cityGroup.add(river);
    const bridge = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.5, 7.5), dark);
    bridge.rotation.y = -0.4;
    bridge.position.set(28, 0.5, 9);
    cityGroup.add(bridge);

    // sky dome
    const skyUniforms = {
      uTop: { value: new THREE.Color(0x0a1424) },
      uBottom: { value: new THREE.Color(0x1d3a5c) },
      uSunDir: { value: new THREE.Vector3(0.8, 0.6, -0.3).normalize() },
      uSunI: { value: 0 },
      uSunColor: { value: new THREE.Color(0xfff2d8) },
    };
    const skyMat = new THREE.ShaderMaterial({
      uniforms: skyUniforms,
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
      vertexShader: `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `
        uniform vec3 uTop; uniform vec3 uBottom; uniform vec3 uSunDir; uniform float uSunI; uniform vec3 uSunColor;
        varying vec3 vDir;
        void main(){
          vec3 d = normalize(vDir);
          float hh = clamp(d.y * 0.5 + 0.5, 0.0, 1.0);
          vec3 col = mix(uBottom, uTop, pow(hh, 0.75));
          float s = max(dot(d, uSunDir), 0.0);
          col += uSunColor * (pow(s, 90.0) * 1.5 + pow(s, 7.0) * 0.25) * uSunI;
          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    const skyDome = new THREE.Mesh(new THREE.SphereGeometry(70, 32, 16), skyMat);
    skyDome.position.set(20, 0, 0);
    cityGroup.add(skyDome);

    // stars
    const starGeo = new THREE.BufferGeometry();
    const starPos = new Float32Array(320 * 3);
    for (let i = 0; i < 320; i += 1) {
      const az = hash01(i * 3 + 1) * Math.PI * 2;
      const el = 0.12 + hash01(i * 11 + 7) * 1.35;
      const r = 64;
      starPos[i * 3] = 20 + Math.cos(el) * Math.cos(az) * r;
      starPos[i * 3 + 1] = Math.sin(el) * r;
      starPos[i * 3 + 2] = Math.cos(el) * Math.sin(az) * r;
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xcfe0ff, size: 0.5, transparent: true, opacity: 0, sizeAttenuation: true, depthWrite: false, fog: false });
    const stars = new THREE.Points(starGeo, starMat);
    cityGroup.add(stars);

    // sun + moon sprites
    const sunTex = radialTexture(0.4);
    const moonTex = radialTexture(0.25);
    cityTextures.push(sunTex, moonTex);
    const sunSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: sunTex, color: 0xffedc8, transparent: true, opacity: 0.9, depthWrite: false, fog: false }));
    sunSprite.scale.setScalar(11);
    cityGroup.add(sunSprite);
    const moonSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: moonTex, color: 0xd8e4ff, transparent: true, opacity: 0, depthWrite: false, fog: false }));
    moonSprite.scale.setScalar(5.5);
    moonSprite.position.set(-14, 30, 22);
    cityGroup.add(moonSprite);

    // clouds
    const cloudTex = radialTexture(0.75);
    cityTextures.push(cloudTex);
    const clouds: THREE.Sprite[] = [];
    for (let i = 0; i < 12; i += 1) {
      const cloud = new THREE.Sprite(new THREE.SpriteMaterial({ map: cloudTex, color: 0xb8c4d8, transparent: true, opacity: 0.16, depthWrite: false, fog: false }));
      cloud.position.set(14 + hash01(i * 7 + 2) * 34, 17 + hash01(i * 13 + 3) * 9, -22 + hash01(i * 5 + 8) * 44);
      cloud.scale.set(10 + hash01(i * 17) * 12, 3.4 + hash01(i * 23) * 3, 1);
      clouds.push(cloud);
      cityGroup.add(cloud);
    }

    // rain + snow particle systems
    const makeFall = (count: number, size: number, color: number, opacity: number) => {
      const geo = new THREE.BufferGeometry();
      const pos = new Float32Array(count * 3);
      const vel = new Float32Array(count);
      for (let i = 0; i < count; i += 1) {
        pos[i * 3] = 12 + hash01(i * 3 + 1) * 36;
        pos[i * 3 + 1] = hash01(i * 7 + 2) * 16;
        pos[i * 3 + 2] = -24 + hash01(i * 11 + 3) * 48;
        vel[i] = 0.7 + hash01(i * 13 + 5) * 0.6;
      }
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      const mat = new THREE.PointsMaterial({ color, size, transparent: true, opacity, depthWrite: false });
      const pts = new THREE.Points(geo, mat);
      pts.visible = false;
      cityGroup.add(pts);
      return { pts, pos, vel, count, geo };
    };
    const rain = makeFall(500, 0.16, 0xa8c8e8, 0.55);
    const snow = makeFall(360, 0.26, 0xffffff, 0.85);

    // moving car lights on two roads
    const carGeo = new THREE.BufferGeometry();
    const CARS = 14;
    const carPos = new Float32Array(CARS * 3);
    const carVel = new Float32Array(CARS);
    for (let i = 0; i < CARS; i += 1) {
      carPos[i * 3] = 13 + hash01(i * 5 + 1) * 30;
      carPos[i * 3 + 1] = 0.35;
      carPos[i * 3 + 2] = i % 2 === 0 ? -5 : 18;
      carVel[i] = (2.4 + hash01(i * 9 + 2) * 3) * (i % 2 === 0 ? 1 : -1);
    }
    carGeo.setAttribute("position", new THREE.BufferAttribute(carPos, 3));
    const carMat = new THREE.PointsMaterial({ color: 0xffe8b0, size: 0.34, transparent: true, opacity: 0.5, depthWrite: false });
    const cars = new THREE.Points(carGeo, carMat);
    cityGroup.add(cars);

    /* sky/city driver state (lerped toward live weather + real clock) */
    const skyState = {
      top: new THREE.Color(0x0a1424),
      bottom: new THREE.Color(0x1d3a5c),
      sunColor: new THREE.Color(0xfff2d8),
      sunI: 0,
      stars: 0,
      glow: 0.15,
      elev: 0.5,
    };
    const tmpTop = new THREE.Color();
    const tmpBottom = new THREE.Color();
    const tmpSun = new THREE.Color();
    const grayBottom = new THREE.Color(0x5a6474);
    const heatBottom = new THREE.Color(0xd8a05a);
    const coldBottom = new THREE.Color(0x9cc0e0);

    const cityUpdate = (dt: number, t: number) => {
      const bus = getMarketBus();
      const wx = bus.getSnapshot().weather;
      const liveWeather = wx.status === "live";
      const hour = tehranHour();
      let phase: SkyPhase = skyPhaseFromHour(hour);
      if (liveWeather && wx.isDay != null) {
        if (wx.isDay && phase === "night") phase = "day";
        if (!wx.isDay && phase === "day") phase = "night";
      }
      const kind: WeatherKind = liveWeather ? classifyWmo(wx.code) : "cloudy";
      const spec = PHASE_SKY[phase];
      const overcast = kind === "rain" || kind === "snow" || kind === "cloudy" ? 0.4 : kind === "fog" ? 0.5 : kind === "partly" ? 0.8 : 1;
      tmpTop.setHex(spec.top);
      tmpBottom.setHex(spec.bottom);
      if (overcast < 1) tmpBottom.lerp(grayBottom, (1 - overcast) * 0.8);
      if (wx.temperature != null && wx.temperature >= 36) tmpBottom.lerp(heatBottom, 0.3);
      if (wx.temperature != null && wx.temperature <= 5) tmpBottom.lerp(coldBottom, 0.3);
      tmpSun.setHex(spec.sunColor);
      const k = 1 - Math.exp(-dt * 1.3);
      skyState.top.lerp(tmpTop, k);
      skyState.bottom.lerp(tmpBottom, k);
      skyState.sunColor.lerp(tmpSun, k);
      skyState.sunI += (spec.sunI * overcast - skyState.sunI) * k;
      skyState.stars += (spec.stars * (kind === "clear" ? 1 : 0.35) - skyState.stars) * k;
      skyState.glow += (spec.glow + (kind === "rain" || kind === "snow" ? 0.15 : 0) - skyState.glow) * k;
      skyState.elev += (spec.elev - skyState.elev) * k;

      const sunDir = new THREE.Vector3(Math.cos(skyState.elev) * 0.92, Math.sin(skyState.elev), Math.cos(skyState.elev) * -0.38).normalize();
      skyUniforms.uTop.value.copy(skyState.top);
      skyUniforms.uBottom.value.copy(skyState.bottom);
      skyUniforms.uSunDir.value.copy(sunDir);
      skyUniforms.uSunI.value = skyState.sunI;
      skyUniforms.uSunColor.value.copy(skyState.sunColor);
      sunSprite.position.copy(sunDir).multiplyScalar(58).add(skyDome.position);
      (sunSprite.material as THREE.SpriteMaterial).opacity = Math.max(skyState.sunI * 0.95, 0);
      (moonSprite.material as THREE.SpriteMaterial).opacity = skyState.stars * 0.85;
      starMat.opacity = skyState.stars * 0.9;
      bMat.emissiveIntensity = 0.1 + skyState.glow * 1.15;
      (cars.material as THREE.PointsMaterial).opacity = 0.18 + skyState.glow * 0.5;
      windowSun.intensity = skyState.sunI * 1.35;
      windowSun.color.copy(skyState.sunColor);
      citySpill.intensity = skyState.glow * 11;

      // particle motion
      const moveFall = (sys: typeof rain, speed: number, sway: number) => {
        if (!sys.pts.visible) return;
        for (let i = 0; i < sys.count; i += 1) {
          sys.pos[i * 3 + 1] -= speed * sys.vel[i] * dt;
          if (sway > 0) sys.pos[i * 3] += Math.sin(t * 1.7 + i) * sway * dt;
          if (sys.pos[i * 3 + 1] < 0) {
            sys.pos[i * 3 + 1] = 16;
            sys.pos[i * 3] = 12 + hash01(i * 3 + 1 + Math.floor(t)) * 36;
          }
        }
        sys.geo.attributes.position.needsUpdate = true;
      };
      rain.pts.visible = kind === "rain";
      snow.pts.visible = kind === "snow";
      moveFall(rain, 17, 1.2);
      moveFall(snow, 1.7, 0.9);

      for (let i = 0; i < clouds.length; i += 1) {
        const cloud = clouds[i];
        cloud.position.x += dt * (0.14 + hash01(i * 7) * 0.12);
        if (cloud.position.x > 52) cloud.position.x = 8;
        (cloud.material as THREE.SpriteMaterial).opacity = kind === "clear" ? 0.14 : kind === "partly" ? 0.3 : 0.5;
      }
      for (let i = 0; i < CARS; i += 1) {
        carPos[i * 3] += carVel[i] * dt;
        if (carPos[i * 3] > 46) carPos[i * 3] = 12;
        if (carPos[i * 3] < 10) carPos[i * 3] = 46;
      }
      carGeo.attributes.position.needsUpdate = true;
    };

    /* ---------------- sliding entrance door (−X wall) ---------------- */
    const doorGroup = new THREE.Group();
    doorGroup.position.set(Math.sin(DOOR_CENTER) * 10.52, 0, Math.cos(DOOR_CENTER) * 10.52);
    doorGroup.lookAt(0, 0, 0);
    scene.add(doorGroup);
    const doorPanelMat = new THREE.MeshStandardMaterial({ color: 0x0d1524, metalness: 0.65, roughness: 0.35 });
    const doorEdgeMat = new THREE.MeshStandardMaterial({ color: 0x0d1522, emissive: 0x22d3ee, emissiveIntensity: 1.2, metalness: 0.3, roughness: 0.4 });
    const doorPanels: THREE.Mesh[] = [];
    for (const side of [-1, 1]) {
      const panel = new THREE.Mesh(new THREE.BoxGeometry(0.94, 2.5, 0.07), doorPanelMat);
      panel.position.set(side * 0.475, 1.28, 0);
      doorGroup.add(panel);
      doorPanels.push(panel);
      const edge = new THREE.Mesh(new THREE.BoxGeometry(0.045, 2.4, 0.1), doorEdgeMat);
      edge.position.set(-side * 0.44, 0, 0.02);
      panel.add(edge);
    }
    const doorHeader = new THREE.Mesh(new THREE.BoxGeometry(2.15, 0.28, 0.2), dark);
    doorHeader.position.set(0, 2.66, 0);
    doorGroup.add(doorHeader);
    for (const side of [-1, 1]) {
      const jamb = new THREE.Mesh(new THREE.BoxGeometry(0.17, 2.62, 0.2), dark);
      jamb.position.set(side * 1.02, 1.31, 0);
      doorGroup.add(jamb);
    }
    const doorSpill = new THREE.PointLight(0xffd9a0, 0, 9, 1.6);
    doorSpill.position.set(0, 2.2, -1.2);
    doorGroup.add(doorSpill);
    const doorGlowMat = new THREE.MeshBasicMaterial({ color: 0xffd9a0, transparent: true, opacity: 0, depthWrite: false });
    const doorGlow = new THREE.Mesh(new THREE.CircleGeometry(1.4, 24), doorGlowMat);
    doorGlow.rotation.x = -Math.PI / 2;
    doorGlow.position.set(0, 0.02, -0.9);
    doorGroup.add(doorGlow);

    const DOOR_PERIOD = 34;
    const DOOR_OPEN_AT = 14;
    const DOOR_HOLD = 4.2;
    let doorPos = 0;

    /* ---------------- video wall: earth + portfolio + market grid ---------------- */
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin("anonymous");
    const wallMap = loader.load("/textures/earth-day-2048.jpg", undefined, undefined, () => onFail());
    wallMap.colorSpace = THREE.SRGBColorSpace;
    const mapPanel = new THREE.Mesh(
      new THREE.CylinderGeometry(wallRadius, wallRadius, 2.6, 48, 1, true, Math.PI - 0.62, 1.24),
      new THREE.MeshBasicMaterial({ map: wallMap, color: new THREE.Color(1.0, 1.28, 1.7), side: THREE.BackSide, fog: false }),
    );
    mapPanel.position.y = 2.55;
    scene.add(mapPanel);
    const mapFrame = new THREE.Mesh(
      new THREE.CylinderGeometry(wallRadius + 0.02, wallRadius + 0.02, 2.76, 48, 1, true, Math.PI - 0.68, 1.36),
      new THREE.MeshStandardMaterial({ color: 0x0a0f1a, metalness: 0.6, roughness: 0.4, emissive: 0xd4af37, emissiveIntensity: 0.3, side: THREE.BackSide }),
    );
    mapFrame.position.y = 2.55;
    scene.add(mapFrame);
    const wallWash = new THREE.PointLight(0x8fd4ff, 26, 16, 1.8);
    wallWash.position.set(0, 3.1, -6.5);
    scene.add(wallWash);

    const portfolioCanvas = new LiveCanvas(2048, 560);
    const gridCanvas = new LiveCanvas(2048, 560);
    const clockCanvas = new LiveCanvas(1024, 560);
    liveCanvases.push(portfolioCanvas, gridCanvas, clockCanvas);
    const portfolioPanel = new THREE.Mesh(
      new THREE.CylinderGeometry(wallRadius, wallRadius, 2.2, 32, 1, true, Math.PI + 0.68, 0.82),
      new THREE.MeshBasicMaterial({ map: portfolioCanvas.texture, side: THREE.BackSide, fog: false }),
    );
    portfolioPanel.position.y = 2.45;
    scene.add(portfolioPanel);
    const gridPanel = new THREE.Mesh(
      new THREE.CylinderGeometry(wallRadius, wallRadius, 2.2, 32, 1, true, Math.PI - 0.68, -0.82),
      new THREE.MeshBasicMaterial({ map: gridCanvas.texture, side: THREE.BackSide, fog: false }),
    );
    gridPanel.position.y = 2.45;
    scene.add(gridPanel);
    for (const side of [-1, 1]) {
      const frame = new THREE.Mesh(
        new THREE.CylinderGeometry(wallRadius + 0.02, wallRadius + 0.02, 2.34, 32, 1, true, Math.PI + side * 0.63, side * 0.92),
        new THREE.MeshStandardMaterial({ color: 0x0a0f1a, metalness: 0.6, roughness: 0.4, emissive: 0x22d3ee, emissiveIntensity: 0.14, side: THREE.BackSide }),
      );
      frame.position.y = 2.45;
      scene.add(frame);
    }
    // physical world-clock board on the −X wall
    const clockAngle = 5.45;
    const clockBoard = new THREE.Mesh(new THREE.BoxGeometry(2.5, 1.42, 0.08), new THREE.MeshBasicMaterial({ map: clockCanvas.texture, fog: false }));
    clockBoard.position.set(Math.sin(clockAngle) * 10.3, 3.35, Math.cos(clockAngle) * 10.3);
    clockBoard.rotation.y = clockAngle + Math.PI;
    scene.add(clockBoard);
    const clockBoardFrame = new THREE.Mesh(new THREE.BoxGeometry(2.62, 1.54, 0.05), darker);
    clockBoardFrame.position.copy(clockBoard.position);
    clockBoardFrame.rotation.y = clockBoard.rotation.y;
    clockBoardFrame.translateZ(-0.03);
    scene.add(clockBoardFrame);

    /* ---------------- console ring: 12 role desks ---------------- */
    const DESKS = ROLE_DESKS.length;
    const DESK_R = 5.3;
    const deskGroup = new THREE.Group();
    scene.add(deskGroup);
    const consoleCanvases: LiveCanvas[] = [];
    const tabletCanvases: LiveCanvas[] = [];
    const tabletMeshes: THREE.Mesh[] = [];
    const tabletRoles = new Map<string, RoleId>();
    const deskAngles: number[] = [];

    const buildFigure = (seated: boolean, suit: number, goldTrim: boolean): THREE.Group => {
      const fig = new THREE.Group();
      const suitMat = new THREE.MeshStandardMaterial({ color: suit, metalness: 0.1, roughness: 0.85 });
      const headMat = new THREE.MeshStandardMaterial({ color: 0x10151f, metalness: 0.2, roughness: 0.7 });
      const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.165, seated ? 0.34 : 0.44, 4, 12), suitMat);
      torso.position.y = seated ? 0.98 : 1.06;
      fig.add(torso);
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.125, 16, 12), headMat);
      head.position.y = seated ? 1.38 : 1.5;
      fig.add(head);
      if (goldTrim) {
        const trim = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.014, 6, 24), goldMat);
        trim.rotation.x = Math.PI / 2;
        trim.position.y = seated ? 1.16 : 1.26;
        fig.add(trim);
      }
      if (!seated) {
        const legGeo = new THREE.BoxGeometry(0.09, 0.52, 0.11);
        const legL = new THREE.Mesh(legGeo, suitMat);
        const legR = new THREE.Mesh(legGeo, suitMat);
        legL.position.set(-0.08, 0.3, 0);
        legR.position.set(0.08, 0.3, 0);
        fig.add(legL, legR);
        fig.userData.legs = [legL, legR];
      }
      return fig;
    };

    for (let i = 0; i < DESKS; i += 1) {
      const spec = ROLE_DESKS[i];
      const a = (i / DESKS) * Math.PI * 2 + Math.PI / DESKS;
      deskAngles.push(a);
      const x = Math.sin(a) * DESK_R;
      const z = Math.cos(a) * DESK_R;

      const desk = new THREE.Group();
      desk.position.set(x, 0, z);
      desk.rotation.y = a + Math.PI;
      const body = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.1, 0.78), dark);
      body.position.y = 1.02;
      desk.add(body);
      const skirt = new THREE.Mesh(new THREE.BoxGeometry(1.72, 0.5, 0.12), darker);
      skirt.position.set(0, 0.75, 0.3);
      desk.add(skirt);
      const glowStrip = new THREE.Mesh(
        new THREE.BoxGeometry(1.64, 0.045, 0.02),
        new THREE.MeshStandardMaterial({ color: 0x0d1522, emissive: spec.tint, emissiveIntensity: 2.4, metalness: 0.3, roughness: 0.4 }),
      );
      glowStrip.position.set(0, 0.985, -0.4);
      desk.add(glowStrip);
      for (const sx of [-0.78, 0.78]) {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.0, 0.66), darker);
        leg.position.set(sx, 0.5, 0);
        desk.add(leg);
      }

      const consoleCanvas = new LiveCanvas(640, 400);
      liveCanvases.push(consoleCanvas);
      consoleCanvases.push(consoleCanvas);
      const screen = new THREE.Mesh(
        new THREE.PlaneGeometry(1.52, 0.86),
        new THREE.MeshBasicMaterial({ map: consoleCanvas.texture, fog: false }),
      );
      screen.position.set(0, 1.42, 0.18);
      screen.rotation.set(-0.32, 0, 0);
      desk.add(screen);
      const screenFrame = new THREE.Mesh(new THREE.BoxGeometry(1.62, 0.96, 0.05), darker);
      screenFrame.position.set(0, 1.42, 0.14);
      screenFrame.rotation.set(-0.32, 0, 0);
      desk.add(screenFrame);

      // touch tablet on the console
      const tabletCanvas = new LiveCanvas(320, 220);
      liveCanvases.push(tabletCanvas);
      tabletCanvases.push(tabletCanvas);
      const tablet = new THREE.Mesh(
        new THREE.PlaneGeometry(0.5, 0.34),
        new THREE.MeshBasicMaterial({ map: tabletCanvas.texture, fog: false }),
      );
      tablet.position.set(0.62, 1.15, -0.02);
      tablet.rotation.set(-1.05, 0, 0);
      desk.add(tablet);
      tabletMeshes.push(tablet);
      tabletRoles.set(tablet.uuid, spec.role);
      const tabletFrame = new THREE.Mesh(new THREE.BoxGeometry(0.56, 0.39, 0.02), darker);
      tabletFrame.position.set(0.62, 1.14, -0.01);
      tabletFrame.rotation.set(-1.05, 0, 0);
      desk.add(tabletFrame);

      // chair
      const chair = new THREE.Group();
      chair.position.set(0, 0, -0.72);
      const seat = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.07, 0.46), darker);
      seat.position.y = 0.6;
      const backrest = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.56, 0.07), darker);
      backrest.position.set(0, 0.9, 0.22);
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.58, 10), dark);
      pole.position.y = 0.31;
      const base = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.3, 0.05, 16), dark);
      base.position.y = 0.025;
      chair.add(seat, backrest, pole, base);
      desk.add(chair);

      // procedural stand-in seated operator (replaced by a rigged human once loaded)
      const suitTint = i === 9 ? 0x5a2626 : i === 8 ? 0x24402c : [0x2b3c5e, 0x354a70, 0x253550, 0x41587f][i % 4];
      const fig = buildFigure(true, suitTint, i % 5 === 0);
      fig.position.set(0, 0, -0.78);
      fig.rotation.y = 0;
      desk.add(fig);
      desk.userData.staff = fig;
      deskGroup.add(desk);
    }

    /* walking staff (procedural stand-ins) + commander */
    const walkers: Array<{ fig: THREE.Group; radius: number; speed: number; phase: number; dir: 1 | -1 }> = [];
    const WALKER_SPECS: Array<{ radius: number; speed: number; suit: number; gold: boolean }> = [
      { radius: 6.7, speed: -0.18, suit: 0x354a70, gold: false },
      { radius: 3.95, speed: 0.3, suit: 0x2b3c5e, gold: true },
      { radius: 7.6, speed: 0.16, suit: 0x41587f, gold: false },
    ];
    WALKER_SPECS.forEach((spec, i) => {
      const fig = buildFigure(false, spec.suit, spec.gold);
      scene.add(fig);
      walkers.push({ fig, radius: spec.radius, speed: spec.speed, phase: hash01(i * 53 + 3) * Math.PI * 2, dir: spec.speed >= 0 ? 1 : -1 });
    });
    const commander = buildFigure(false, 0x0d1526, true);
    commander.scale.setScalar(1.06);
    commander.position.set(1.85, 0, 4.35);
    commander.rotation.y = Math.PI - 0.4;
    scene.add(commander);
    const commanderRing = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.02, 8, 48), goldMat);
    commanderRing.rotation.x = Math.PI / 2;
    commanderRing.position.set(1.85, 0.02, 4.35);
    scene.add(commanderRing);
    // liaison officer + journalist + two door guards (procedural stand-ins)
    const liaison = buildFigure(false, 0x3a3050, true);
    liaison.position.set(2.85, 0, 5.2);
    liaison.lookAt(0, 0, 0);
    scene.add(liaison);
    const journalist = buildFigure(false, 0x24404a, false);
    journalist.position.set(Math.sin(deskAngles[7]) * 6.6, 0, Math.cos(deskAngles[7]) * 6.6);
    journalist.lookAt(0, 0, 0);
    const cameraProp = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.16, 0.36), dark);
    cameraProp.position.set(0.14, 1.28, 0.24);
    journalist.add(cameraProp);
    scene.add(journalist);
    const guards: THREE.Group[] = [];
    for (const gz of [-1.2, 1.2]) {
      const guard = buildFigure(false, 0x1a2438, false);
      guard.position.set(-8.65, 0, gz);
      guard.lookAt(0, 0, 0);
      scene.add(guard);
      guards.push(guard);
    }

    /* ---------------- rigged human cast (open-source GLB) ---------------- */
    interface WalkerEntry { fig: THREE.Group; radius: number; speed: number; phase: number; dir: 1 | -1 }
    const mixers: THREE.AnimationMixer[] = [];
    const glbWalkers: WalkerEntry[] = [];
    let glbCommander: THREE.Object3D | null = null;
    let glbCommuter: { root: THREE.Object3D; mixer: THREE.AnimationMixer; walk: THREE.AnimationAction | null; idle: THREE.AnimationAction | null } | null = null;
    let proceduralStaffVisible = true;

    const tintObject = (root: THREE.Object3D, tint: number) => {
      const color = new THREE.Color(tint);
      root.traverse((node) => {
        const mesh = node as THREE.Mesh;
        if (!mesh.isMesh) return;
        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        const cloned = mats.map((m) => {
          const c = m.clone();
          if ("color" in c) {
            (c as THREE.MeshStandardMaterial).color = color;
          }
          if ("emissive" in c) {
            (c as THREE.MeshStandardMaterial).emissive = new THREE.Color(0x161c26);
            (c as THREE.MeshStandardMaterial).emissiveIntensity = 0.55;
          }
          return c;
        });
        mesh.material = Array.isArray(mesh.material) ? cloned : cloned[0];
      });
    };

    const pickClip = (clips: THREE.AnimationClip[], re: RegExp): THREE.AnimationClip | null =>
      clips.find((c) => re.test(c.name)) ?? null;

    const standHeight = (root: THREE.Object3D): number => {
      const box = new THREE.Box3().setFromObject(root);
      return Math.max(box.max.y - box.min.y, 0.5);
    };

    const spawnHuman = (
      base: { scene: THREE.Object3D; clips: THREE.AnimationClip[]; height: number },
      opts: { tint: number; scale: number; clip: "idle" | "walk" },
    ): { root: THREE.Group; mixer: THREE.AnimationMixer | null; walk: THREE.AnimationAction | null; idle: THREE.AnimationAction | null } => {
      const root = new THREE.Group();
      const instance = cloneSkinned(base.scene);
      tintObject(instance, opts.tint);
      instance.scale.setScalar((1.72 / base.height) * opts.scale);
      root.add(instance);
      let mixer: THREE.AnimationMixer | null = null;
      let walk: THREE.AnimationAction | null = null;
      let idle: THREE.AnimationAction | null = null;
      const idleClip = pickClip(base.clips, /idle/i) ?? pickClip(base.clips, /walk/i) ?? base.clips[0] ?? null;
      const walkClip = pickClip(base.clips, /walk/i) ?? pickClip(base.clips, /run/i) ?? idleClip;
      if (idleClip || walkClip) {
        mixer = new THREE.AnimationMixer(instance);
        if (idleClip) {
          idle = mixer.clipAction(idleClip);
          idle.play();
        }
        if (walkClip && opts.clip === "walk") {
          walk = mixer.clipAction(walkClip);
          walk.play();
          if (idle) idle.stop();
        }
        if (mixer) mixers.push(mixer);
      }
      return { root, mixer, walk, idle };
    };

    void (async () => {
      const loader2 = new GLTFLoader();
      const loadBase = (file: string) =>
        new Promise<{ scene: THREE.Object3D; clips: THREE.AnimationClip[]; height: number } | null>((resolve) => {
          loader2.load(
            `/models/humans/${file}`,
            (gltf) => {
              try {
                const height = standHeight(gltf.scene);
                resolve({ scene: gltf.scene, clips: gltf.animations ?? [], height });
              } catch {
                resolve(null);
              }
            },
            undefined,
            () => resolve(null),
          );
        });
      const bases = await Promise.all([
        loadBase("Soldier.glb"),
        loadBase("Michelle.glb"),
        loadBase("kira.glb"),
        loadBase("rpm.glb"),
      ]);
      if (disposed) return;
      const [soldier, michelle, kira, rpm] = bases;
      if (!soldier && !michelle && !kira && !rpm) return; // procedural stand-ins remain

      proceduralStaffVisible = false;
      const hideProcedural = (obj: THREE.Object3D | undefined | null) => {
        if (obj) obj.visible = false;
      };

      // seated staff — one rigged human per role desk
      const SEATED_BASE_CYCLE = [michelle, soldier, kira, rpm];
      const SEATED_TINTS = [0xffffff, 0xe8ecf4, 0xf4ead8, 0xd8e4f2];
      deskGroup.children.forEach((deskObj, i) => {
        const base = SEATED_BASE_CYCLE[i % 4];
        if (!base) {
          return;
        }
        hideProcedural((deskObj as THREE.Group).userData.staff as THREE.Object3D | undefined);
        const tint = i === 8 ? 0xcfe6d8 : i === 9 ? 0xf0c0b8 : i === 10 ? 0xd8ccf4 : i === 11 ? 0xf2e2c4 : SEATED_TINTS[i % 4];
        const human = spawnHuman(base, { tint, scale: 0.97 + hash01(i * 29 + 3) * 0.08, clip: "idle" });
        human.root.position.set(0, 0, -0.78);
        deskObj.add(human.root);
      });

      // walking staff with real walk cycles
      const WALK_BASES: Array<{ base: typeof soldier; radius: number; speed: number; tint: number }> = [
        { base: soldier, radius: 6.7, speed: -0.18, tint: 0xe8ecf4 },
        { base: michelle, radius: 3.95, speed: 0.3, tint: 0xffffff },
        { base: kira, radius: 7.6, speed: 0.16, tint: 0xe0e8f4 },
      ];
      WALK_BASES.forEach((entry, i) => {
        if (!entry.base) {
          walkers[i].fig.visible = proceduralStaffVisible;
          glbWalkers.push(walkers[i]);
          return;
        }
        hideProcedural(walkers[i].fig);
        const human = spawnHuman(entry.base, { tint: entry.tint, scale: 1, clip: "walk" });
        if (human.walk) human.walk.timeScale = 0.82;
        human.root.position.y = 0.02;
        scene.add(human.root);
        glbWalkers.push({
          fig: human.root,
          radius: entry.radius,
          speed: entry.speed,
          phase: hash01(i * 53 + 3) * Math.PI * 2,
          dir: entry.speed >= 0 ? 1 : -1,
        });
      });

      // door guards — uniformed, at attention
      const guardBase = soldier ?? rpm;
      if (guardBase) {
        for (const gz of [-1.2, 1.2]) {
          hideProcedural(guards[gz < 0 ? 0 : 1]);
          const human = spawnHuman(guardBase, { tint: gz < 0 ? 0x8fa8cc : 0xc098a8, scale: 1.02, clip: "idle" });
          human.root.position.set(-8.65, 0, gz);
          human.root.lookAt(0, 0, 0);
          scene.add(human.root);
        }
      }

      // commander — the user's avatar at the podium
      const cmdBase = rpm ?? soldier;
      if (cmdBase) {
        hideProcedural(commander);
        const human = spawnHuman(cmdBase, { tint: 0xfff0dc, scale: 1.06, clip: "idle" });
        human.root.position.set(1.85, 0, 4.35);
        human.root.rotation.y = Math.PI - 0.4;
        scene.add(human.root);
        glbCommander = human.root;
      }

      // briefing officer beside the commander
      const liaisonBase = michelle ?? kira;
      if (liaisonBase) {
        hideProcedural(liaison);
        const human = spawnHuman(liaisonBase, { tint: 0xf2e2c4, scale: 1, clip: "idle" });
        human.root.position.set(2.85, 0, 5.2);
        human.root.lookAt(0, 0, 0);
        scene.add(human.root);
      }

      // field journalist with a camera rig near the news desk
      const newsBase = kira ?? michelle;
      if (newsBase) {
        hideProcedural(journalist);
        const human = spawnHuman(newsBase, { tint: 0xd8e8f0, scale: 1, clip: "idle" });
        human.root.position.set(Math.sin(deskAngles[7]) * 6.6, 0, Math.cos(deskAngles[7]) * 6.6);
        human.root.lookAt(0, 0, 0);
        const cam = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.16, 0.36), dark);
        cam.position.set(0.14, 1.28, 0.24);
        human.root.add(cam);
        scene.add(human.root);
      }

      // commuter who enters through the sliding door
      const commuterBase = soldier ?? michelle;
      if (commuterBase) {
        const human = spawnHuman(commuterBase, { tint: 0xd8d8e0, scale: 1, clip: "walk" });
        if (human.walk) human.walk.timeScale = 0.9;
        human.root.visible = false;
        scene.add(human.root);
        glbCommuter = { root: human.root, mixer: human.mixer ?? new THREE.AnimationMixer(human.root), walk: human.walk, idle: human.idle };
      }
    })();

    /* ---------------- floating role chips (clickable) ---------------- */
    const chipLayer = document.createElement("div");
    chipLayer.setAttribute("aria-hidden", "true");
    chipLayer.style.cssText = "position:absolute;inset:0;overflow:hidden;pointer-events:none;";
    container.appendChild(chipLayer);
    interface Chip { el: HTMLButtonElement; pos: THREE.Vector3; role: RoleId | "commander" }
    const chips: Chip[] = ROLE_DESKS.map((spec, i) => {
      const el = document.createElement("button");
      el.type = "button";
      el.className = "scene-chip";
      el.dataset.roleChip = spec.role;
      el.style.opacity = "0";
      el.style.pointerEvents = "auto";
      el.style.cursor = "pointer";
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        roleFocusRef.current(spec.role);
      });
      chipLayer.appendChild(el);
      const a = deskAngles[i];
      return { el, pos: new THREE.Vector3(Math.sin(a) * DESK_R, 2.06, Math.cos(a) * DESK_R), role: spec.role };
    });
    const commanderChipEl = document.createElement("button");
    commanderChipEl.type = "button";
    commanderChipEl.className = "scene-chip";
    commanderChipEl.dataset.roleChip = "commander";
    commanderChipEl.style.opacity = "0";
    commanderChipEl.style.pointerEvents = "auto";
    commanderChipEl.style.cursor = "pointer";
    commanderChipEl.style.borderColor = "rgba(212,175,55,0.6)";
    commanderChipEl.addEventListener("click", (ev) => {
      ev.stopPropagation();
      roleFocusRef.current("liaison");
    });
    chipLayer.appendChild(commanderChipEl);
    const commanderChip = { el: commanderChipEl, pos: new THREE.Vector3(1.85, 2.12, 4.35), role: "commander" as const };
    chips.push(commanderChip);

    let appliedLocale = "";

    const refreshChipLabels = () => {
      const t = textsRef.current;
      if (t.locale === appliedLocale) return;
      appliedLocale = t.locale;
      for (const chip of chips) {
        const label = chip.role === "commander" ? t.roles.commander : t.shortRoles[chip.role];
        chip.el.textContent = label;
      }
    };
    refreshChipLabels();

    /* ---------------- data → canvas redraws ---------------- */
    const redrawConsoles = () => {
      const t = textsRef.current;
      const snap = getMarketBus().getSnapshot();
      const now = Date.now();
      DEMO_ROWS.length = 0;
      for (const holding of DEMO_HOLDINGS) {
        DEMO_ROWS.push({ asset: holding.asset, qty: holding.qty, label: t.market.assets[holding.asset as AssetId] });
      }
      ROLE_DESKS.forEach((spec, i) => {
        const roleLabel = t.roles[spec.role];
        if (spec.role === "news") {
          drawNewsConsole(consoleCanvases[i], t, snap, now / 1000);
        } else if (spec.role === "liaison") {
          drawLiaisonConsole(consoleCanvases[i], t, snap, now / 1000);
        } else if (ROLE_ASSETS[spec.role].length > 0) {
          drawMarketConsole(consoleCanvases[i], t, roleLabel, spec.accent, ROLE_ASSETS[spec.role].map((id) => snap.assets[id]), now / 1000);
        } else {
          drawInternalConsole(consoleCanvases[i], t, roleLabel, spec.accent, now / 1000);
        }
        const primary = ROLE_ASSETS[spec.role].length > 0 ? snap.assets[ROLE_ASSETS[spec.role][0]] : null;
        drawTablet(tabletCanvases[i], t.shortRoles[spec.role], spec.accent, primary, now / 1000);
      });
      drawPortfolioBoard(portfolioCanvas, t, snap);
      drawMarketGrid(gridCanvas, t, snap, now / 1000);
    };
    const redrawClock = () => {
      drawClockBoard(clockCanvas, textsRef.current, new Date());
    };
    redrawConsoles();
    redrawClock();

    /* ---------------- post FX ---------------- */
    let composer: EffectComposer | null = null;
    let bloomPass: UnrealBloomPass | null = null;
    let gradePass: ShaderPass | null = null;
    try {
      composer = new EffectComposer(renderer);
      composer.setPixelRatio(dpr);
      composer.addPass(new RenderPass(scene, camera));
      bloomPass = new UnrealBloomPass(new THREE.Vector2(1, 1), Math.min(amb.bloom, 0.5), 0.5, 0.62);
      composer.addPass(bloomPass);
      gradePass = new ShaderPass(GRADE_SHADER);
      composer.addPass(gradePass);
    } catch {
      composer = null;
    }

    /* ---------------- camera: orbit room ↔ commander FPV ---------------- */
    let yaw = 0;
    let targetYaw = 0;
    let fpvYaw = 0;
    let fpvYawT = 0;
    let fpvPitch = 0;
    let fpvPitchT = 0;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let downX = 0;
    let downY = 0;
    let downTime = 0;
    const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);
    const raycaster = new THREE.Raycaster();
    const onPointerDown = (e: PointerEvent) => {
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      downX = e.clientX;
      downY = e.clientY;
      downTime = performance.now();
      container.style.cursor = "grabbing";
    };
    const onPointerUp = (e: PointerEvent) => {
      dragging = false;
      container.style.cursor = "grab";
      const moved = Math.hypot(e.clientX - downX, e.clientY - downY);
      if (moved < 6 && performance.now() - downTime < 400) {
        const rect = container.getBoundingClientRect();
        const ndc = new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          -((e.clientY - rect.top) / rect.height) * 2 + 1,
        );
        raycaster.setFromCamera(ndc, camera);
        const hits = raycaster.intersectObjects(tabletMeshes, false);
        if (hits.length > 0) {
          const role = tabletRoles.get(hits[0].object.uuid);
          if (role) roleFocusRef.current(role);
        }
      }
    };
    const onPointerMove = (e: PointerEvent) => {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      if (viewRef.current === "fpv") {
        fpvYawT = clamp(fpvYawT + dx * 0.0026, -1.5, 1.5);
        fpvPitchT = clamp(fpvPitchT + dy * 0.0022, -0.45, 0.55);
      } else {
        targetYaw += dx * 0.0032;
      }
    };
    container.style.cursor = "grab";
    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    container.addEventListener("pointermove", onPointerMove);

    const resize = () => {
      const w = container.clientWidth || 1;
      const h = container.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      composer?.setSize(w, h);
      bloomPass?.setSize(w, h);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const applyPreset = (p: AmbiencePreset, s: SeasonPreset) => {
      const a = AMBIENCE[p].three;
      const sea = SEASON_TINTS[s];
      rimLight.color.setHex(a.rim);
      holoLight.color.setHex(a.atmosphere);
      scene.fog?.color.setHex(a.skyTop);
      renderer.setClearColor(a.skyTop, 1);
      holo.setPalette({ atmosphere: a.atmosphere, sun: a.key, tint: sea.tint, tintStrength: sea.strength });
      if (bloomPass) bloomPass.strength = Math.min(a.bloom, 0.5);
    };
    applyPreset(preset, season);

    const busUnsubscribe = getMarketBus().subscribe(() => {
      dataDirty = true;
    });
    let dataDirty = true;
    let lastSecondDraw = 0;

    let raf = 0;
    let running = true;
    let lastFrame = performance.now();
    let elapsed = 0;
    let holoSpin = 0;
    const onVisibility = () => {
      running = document.visibilityState === "visible";
      if (running) lastFrame = performance.now();
    };
    document.addEventListener("visibilitychange", onVisibility);

    camera.position.set(0, 3.15, 8.6);
    camera.lookAt(0, 1.15, 0);

    const tmpWorld = new THREE.Vector3();
    const tmpVec = new THREE.Vector3();
    const tmpRight = new THREE.Vector3();
    const tmpLookAt = new THREE.Vector3();
    const eyeTarget = new THREE.Vector3();
    const lookTarget = new THREE.Vector3();
    const lookDir = new THREE.Vector3();
    const camMtx = new THREE.Matrix4();
    const targetQuat = new THREE.Quaternion();
    const UP = new THREE.Vector3(0, 1, 0);

    const COMMUTER_PATH = [new THREE.Vector3(-9.35, 0, 0.05), new THREE.Vector3(-6.8, 0, 1.15), new THREE.Vector3(-4.5, 0, 2.55)];
    let commuterState: "hidden" | "in" | "idle" | "out" = "hidden";
    let commuterProgress = 0;
    let commuterIdleLeft = 0;

    const animate = () => {
      raf = requestAnimationFrame(animate);
      if (!running || disposed) return;
      const nowMs = performance.now();
      const dt = Math.min((nowMs - lastFrame) / 1000, 0.05);
      lastFrame = nowMs;
      elapsed += dt;
      const t = elapsed;

      holoSpin += dt * 0.05;
      holo.update(t, dt, 0, holoSpin);
      holoLight.intensity = 13 + Math.sin(t * 1.4) * 2;
      (column.material as THREE.MeshBasicMaterial).opacity = 0.08 + (Math.sin(t * 1.1) * 0.5 + 0.5) * 0.03;

      cityUpdate(dt, t);

      // door cycle
      const cycle = t % DOOR_PERIOD;
      const doorTarget = cycle >= DOOR_OPEN_AT && cycle <= DOOR_OPEN_AT + DOOR_HOLD ? 1 : 0;
      doorPos += (doorTarget - doorPos) * Math.min(1, dt * 3.2);
      doorPanels[0].position.x = -(0.475 + doorPos * 1.06);
      doorPanels[1].position.x = 0.475 + doorPos * 1.06;
      doorSpill.intensity = doorPos * 26;
      doorGlowMat.opacity = doorPos * 0.13;
      (doorEdgeMat as THREE.MeshStandardMaterial).emissiveIntensity = 0.7 + doorPos * 1.1;

      // commuter through the door
      if (glbCommuter) {
        const cm = glbCommuter;
        if (commuterState === "hidden" && doorPos > 0.85 && cycle > DOOR_OPEN_AT + 0.4 && cycle < DOOR_OPEN_AT + DOOR_HOLD) {
          commuterState = "in";

          commuterProgress = 0;
          cm.root.visible = true;
          cm.root.position.copy(COMMUTER_PATH[0]);
        }
        if (commuterState === "in" || commuterState === "out") {
          const path = commuterState === "in" ? COMMUTER_PATH : [...COMMUTER_PATH].reverse();
          commuterProgress += dt * 1.15;
          let remaining = commuterProgress;
          let placed = false;
          for (let s = 0; s < path.length - 1; s += 1) {
            const from = path[s];
            const to = path[s + 1];
            const segLen = from.distanceTo(to);
            if (remaining <= segLen) {
              cm.root.position.lerpVectors(from, to, remaining / segLen);
              const dir = to.clone().sub(from).normalize();
              cm.root.rotation.y = Math.atan2(dir.x, dir.z);
              placed = true;
              break;
            }
            remaining -= segLen;
          }
          if (!placed) {
            if (commuterState === "in") {
              commuterState = "idle";
              commuterIdleLeft = 4.5;
              if (cm.walk) cm.walk.stop();
              if (cm.idle) cm.idle.play();
              const dirOut = cm.root.position.clone().sub(COMMUTER_PATH[1]).normalize();
              cm.root.rotation.y = Math.atan2(dirOut.x, dirOut.z);
            } else {
              commuterState = "hidden";
              cm.root.visible = false;
              if (cm.walk) cm.walk.play();
              if (cm.idle) cm.idle.stop();
            }
          }
        } else if (commuterState === "idle") {
          commuterIdleLeft -= dt;
          cm.root.position.y = Math.sin(t * 1.2) * 0.006;
          if (commuterIdleLeft <= 0) {
            commuterState = "out";
            commuterProgress = 0;
            if (cm.idle) cm.idle.stop();
            if (cm.walk) cm.walk.play();
          }
        }
        cm.mixer.update(dt);
      }

      // walkers (procedural or rigged)
      if (proceduralStaffVisible) {
        for (const walker of walkers) {
          const ang = walker.phase + t * walker.speed;
          const x = Math.sin(ang) * walker.radius;
          const z = Math.cos(ang) * walker.radius;
          walker.fig.position.set(x, Math.abs(Math.sin(t * 5 + walker.phase)) * 0.025, z);
          walker.fig.rotation.y = Math.atan2(walker.dir * Math.cos(ang), -walker.dir * Math.sin(ang));
          const legs = walker.fig.userData.legs as THREE.Mesh[] | undefined;
          if (legs) {
            const stride = Math.sin(t * 6.2 + walker.phase) * 0.5;
            legs[0].rotation.x = stride;
            legs[1].rotation.x = -stride;
          }
        }
      } else {
        for (const walker of glbWalkers) {
          const ang = walker.phase + t * walker.speed;
          walker.fig.position.set(Math.sin(ang) * walker.radius, 0.02, Math.cos(ang) * walker.radius);
          walker.fig.rotation.y = Math.atan2(walker.dir * Math.cos(ang), -walker.dir * Math.sin(ang));
        }
      }
      for (const mixer of mixers) mixer.update(dt);

      // commander: subtle oversight sway (rigged or procedural)
      const cmdRoot = glbCommander ?? commander;
      cmdRoot.position.y = Math.sin(t * 1.1) * 0.008;
      if (!glbCommander) cmdRoot.rotation.y = Math.PI + 0.28 + Math.sin(t * 0.35) * 0.06;
      else cmdRoot.rotation.y = Math.PI - 0.4 + Math.sin(t * 0.35) * 0.05;

      // canvas redraw cadence
      const secondTick = Math.floor(elapsed);
      if (secondTick !== lastSecondDraw) {
        lastSecondDraw = secondTick;
        redrawClock();
        if (dataDirty || secondTick % 10 === 0) {
          dataDirty = false;
          redrawConsoles();
        }
        refreshChipLabels();
      }

      // camera
      if (viewRef.current === "fpv") {
        targetFov = 64;
        fpvYaw += (fpvYawT - fpvYaw) * 0.08;
        fpvPitch += (fpvPitchT - fpvPitch) * 0.08;
        eyeTarget.set(1.2, 1.7 + Math.sin(t * 0.9) * 0.008, 3.35);
        eyeTarget.x += Math.sin(t * 0.8) * 0.006;
        eyeTarget.y += Math.sin(t * 1.3) * 0.005;
        lookTarget.set(0, 2.0, 0);
        lookDir.copy(lookTarget).sub(eyeTarget).normalize();
        lookDir.applyAxisAngle(UP, fpvYaw);
        tmpRight.crossVectors(lookDir, UP).normalize();
        lookDir.applyAxisAngle(tmpRight, -fpvPitch).normalize();
        camMtx.lookAt(eyeTarget, tmpLookAt.copy(eyeTarget).add(lookDir), UP);
        targetQuat.setFromRotationMatrix(camMtx);
        camera.position.lerp(eyeTarget, 0.1);
        camera.quaternion.slerp(targetQuat, 0.1);
      } else {
        targetFov = 50;
        yaw += (targetYaw - yaw) * 0.06;
        const camAng = yaw + Math.sin(t * 0.045) * 0.16;
        const camR = 8.75 + Math.sin(t * 0.06) * 0.32;
        eyeTarget.set(Math.sin(camAng) * camR, 3.55 + Math.sin(t * 0.1) * 0.1, Math.cos(camAng) * camR);
        camera.position.lerp(eyeTarget, 0.12);
        lookTarget.set(0, 1.5, 0);
        camMtx.lookAt(camera.position, lookTarget, UP);
        targetQuat.setFromRotationMatrix(camMtx);
        camera.quaternion.slerp(targetQuat, 0.12);
      }
      if (Math.abs(camera.fov - targetFov) > 0.05) {
        camera.fov += (targetFov - camera.fov) * 0.08;
        camera.updateProjectionMatrix();
      }

      // role chips projection
      const rect = container.getBoundingClientRect();
      for (const chip of chips) {
        tmpWorld.copy(chip.pos);
        if (chip.role === "commander" && glbCommander) tmpWorld.set(glbCommander.position.x, 2.12, glbCommander.position.z);
        tmpVec.copy(tmpWorld).project(camera);
        const x = Math.min(Math.max((tmpVec.x * 0.5 + 0.5) * rect.width, 36), rect.width - 36);
        const y = Math.min(Math.max((-tmpVec.y * 0.5 + 0.5) * rect.height, 40), rect.height - 26);
        chip.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -130%)`;
        const dist = camera.position.distanceTo(tmpWorld);
        chip.el.style.opacity = tmpVec.z < 1 && dist < 14 ? String(Math.max(0.35, 1 - dist / 16)) : "0";
      }

      if (gradePass) gradePass.uniforms.uTime.value = t % 10;
      if (composer) composer.render();
      else renderer.render(scene, camera);
    };
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      busUnsubscribe();
      ro.disconnect();
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      container.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("visibilitychange", onVisibility);
      chipLayer.remove();
      composer?.dispose();
      holo.dispose();
      for (const lc of liveCanvases) lc.dispose();
      for (const tex of cityTextures) tex.dispose();
      disposeObject(scene);
      floorTex.dispose();
      wallMap.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset, season]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full cursor-grab active:cursor-grabbing"
      role="img"
      aria-label="Simulated three-dimensional operations room with live public market screens — decorative visualization"
    />
  );
}
