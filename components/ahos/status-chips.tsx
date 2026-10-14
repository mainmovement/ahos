'use client';

import { useEffect, useState } from 'react';
import { webApiFetch } from '@/web_api_client';
import { faNum, type SoakReadModel } from '@/dashboard_snapshot';

/**
 * Top-bar status chips (spec: "status chips — PAPER ONLY, System Health,
 * Evidence Freshness, Uptime").
 *
 * Presentation only. Every value is read from `/api/command`'s snapshot and
 * nothing is derived client-side; a chip that has no reading shows a grey
 * UNKNOWN rather than a plausible substitute, per `UNKNOWN > fabricated`.
 * The PAPER ONLY chip is the exception: it is a constant because it is a fact
 * about the build (`executionMode` in the snapshot), not a measurement.
 */

const REFRESH_MS = 30_000;

type ChipTone = 'gold' | 'ok' | 'warn' | 'unknown';

interface ChipSlice {
  executionMode?: string | null;
  realTrading?: boolean | null;
  state: {
    running?: boolean | null;
    startedAt?: string | null;
    cycleCount?: number | null;
    lastCycleAt?: string | null;
    lastCycleStatus?: string | null;
    intervalSec?: number | null;
  } | null;
  soak?: SoakReadModel | null;
}

interface ChipData {
  slice: ChipSlice | null;
  stale: boolean;
}

const PENDING: ChipData = { slice: null, stale: false };

function minutesAgo(iso: string | null): number | null {
  if (!iso) return null;
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return null;
  return Math.max(0, Math.round((Date.now() - then) / 60_000));
}

/** A freshness verdict from the engine's own last cycle, or the soak's. */
function freshness(slice: ChipSlice): { label: string; tone: ChipTone } {
  const state = slice.state;
  const mins = minutesAgo(state?.lastCycleAt ?? null);
  if (mins === null) {
    const soakAt = slice.soak?.lastCycleAt ?? null;
    const soakMins = minutesAgo(soakAt);
    if (soakMins === null) return { label: 'UNKNOWN', tone: 'unknown' };
    return {
      label: soakMins < 60 ? `${faNum(soakMins)} دقیقه` : `${faNum(Math.round(soakMins / 60))} ساعت`,
      tone: slice.soak?.stale ? 'warn' : 'ok'
    };
  }
  const limit = 3 * (state?.intervalSec ?? 70) / 60;
  if (mins <= limit) return { label: `${faNum(mins)} دقیقه`, tone: 'ok' };
  return { label: `${faNum(mins)} دقیقه`, tone: 'warn' };
}

function health(slice: ChipSlice): { label: string; tone: ChipTone } {
  const state = slice.state;
  if (!state) return { label: 'UNKNOWN', tone: 'unknown' };
  if (state.running) return { label: 'RUNNING', tone: 'ok' };
  const mins = minutesAgo(state.lastCycleAt ?? null);
  if (mins === null) {
    // No engine cycle at all: the local paper soak is the runner that matters,
    // and it is presented as paper, never as engine health.
    return slice.soak?.status === 'AVAILABLE' && slice.soak.run?.running
      ? { label: 'SOAK LIVE', tone: 'ok' }
      : { label: 'IDLE', tone: 'unknown' };
  }
  const limit = 3 * (state.intervalSec ?? 70) / 60;
  if (mins > limit) return { label: 'STALE', tone: 'warn' };
  return state.lastCycleStatus === 'FAILED' ? { label: 'DEGRADED', tone: 'warn' } : { label: 'NOMINAL', tone: 'ok' };
}

/** Uptime from the engine's start, or the soak's cycle count when the engine is idle. */
function uptime(slice: ChipSlice): { label: string; tone: ChipTone } {
  const soak = slice.soak;
  if (!slice.state?.running && soak?.status === 'AVAILABLE' && soak.run) {
    const ok = soak.run.cyclesOk;
    if (ok !== null && ok !== undefined) return { label: `${faNum(ok)} چرخه`, tone: 'ok' };
  }
  const started = slice.state?.startedAt ?? null;
  const mins = minutesAgo(started ?? null);
  if (mins === null) return { label: 'UNKNOWN', tone: 'unknown' };
  const hours = mins / 60;
  if (hours < 1) return { label: `${faNum(mins)} دقیقه`, tone: 'ok' };
  if (hours < 48) return { label: `${faNum(Math.round(hours * 10) / 10)} ساعت`, tone: 'ok' };
  return { label: `${faNum(Math.round(hours / 24))} روز`, tone: 'ok' };
}

const TONE_CLASS: Record<ChipTone, string> = {
  gold: 'border-primary/45 bg-primary/10 text-primary',
  ok: 'border-[var(--ahos-status-verified)]/40 bg-[var(--ahos-status-verified)]/10 text-[var(--ahos-status-verified)]',
  warn: 'border-[var(--ahos-status-stale)]/45 bg-[var(--ahos-status-stale)]/10 text-[var(--ahos-status-stale)]',
  unknown: 'border-[var(--ahos-status-unknown)]/35 bg-[var(--ahos-status-unknown)]/10 text-[var(--ahos-status-unknown)]'
};

function Chip({
  label,
  value,
  tone,
  title
}: {
  label: string;
  value: string;
  tone: ChipTone;
  title?: string;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${TONE_CLASS[tone]}`}
    >
      <span className='opacity-70'>{label}</span>
      <span className='font-mono tabular-nums' dir='ltr'>{value}</span>
    </span>
  );
}

export function StatusChips() {
  const [data, setData] = useState<ChipData>(PENDING);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await webApiFetch('/api/command');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const slice = (await res.json()) as ChipSlice;
        if (!cancelled) setData({ slice, stale: false });
      } catch {
        if (!cancelled) setData((prev) => ({ ...prev, stale: true }));
      }
    };
    void load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const slice = data.slice;
  const paperOnly = slice ? slice.executionMode === 'PAPER_ONLY' || slice.realTrading === false : true;
  const h = slice ? health(slice) : { label: 'UNKNOWN', tone: 'unknown' as const };
  const f = slice ? freshness(slice) : { label: 'UNKNOWN', tone: 'unknown' as const };
  const u = slice ? uptime(slice) : { label: 'UNKNOWN', tone: 'unknown' as const };

  return (
    <div className='hidden items-center gap-1.5 lg:flex' dir='ltr'>
      <Chip
        label='Paper only'
        value={paperOnly ? 'ON' : 'UNKNOWN'}
        tone={paperOnly ? 'gold' : 'unknown'}
        title='executionMode — no real funds, no wallets, no live trading. Ever.'
      />
      <Chip label='Health' value={h.label} tone={h.tone} title='Engine cycle state from /api/command' />
      <Chip label='Evidence' value={f.label} tone={f.tone} title='Age of the last evidence cycle' />
      <Chip label='Uptime' value={u.label} tone={u.tone} title='Engine uptime, or the paper soak cycle count when the engine is idle' />
    </div>
  );
}
