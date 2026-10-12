"use client";

/**
 * M-D7 — the bottom telemetry strips: run log, gates, spend, ledger.
 *
 * Presentation only (AGENTS.md). Every value here is read from
 * `/api/command`'s snapshot — the app's own read model, served from its own
 * origin — and nothing is derived, scored or decided client-side. Where a value
 * has not arrived, or the fetch failed, the strip shows grey UNKNOWN rather than
 * a plausible substitute, because `UNKNOWN > fabricated` and a dashboard that
 * invents its own telemetry is worse than one that admits it did not load.
 *
 * Four cells, per the Dashi spec:
 *  - اجرا (run log): the engine's last cycle, its status, and the cycle count.
 *  - دروازه‌ها (gates): the snapshot's health dimensions, as TruthBadges. These
 *    are the *engine's* verdicts about itself, not a client-side re-check.
 *  - هزینه (spend): always 0. AHOS runs on free tiers and public data; the
 *    number is a constant because it is a fact about the build, and it is shown
 *    so nobody has to take "free" on faith.
 *  - دفتر (ledger): the paper positions the engine holds, and how many are open.
 *
 * The strip does not poll faster than the engine cycles: 30 s against a default
 * 70 s interval. It refreshes on mount, and a failed fetch leaves the last good
 * snapshot in place with a marker rather than blanking the strip — a stale
 * reading with its age on it is more honest than an empty box.
 */
import { useEffect, useState } from "react";

import { webApiFetch } from "@/web_api_client";
import { TruthBadge } from "@/TruthBadge";

const REFRESH_MS = 30_000;
const MAX_GATE_ROWS = 5;
const MAX_LEDGER_ROWS = 4;

/**
 * The slice of the snapshot these strips read. Named fields only — the full
 * payload is larger and most of it is the stage's, not the strips'.
 */
interface CommandSlice {
  state: {
    running: boolean | null;
    cycleCount: number | null;
    lastCycleAt: string | null;
    lastCycleStatus: string | null;
    intervalSec: number | null;
    lastError: string | null;
  } | null;
  health: { dimensions: { nameFa: string; status: string; evidenceFa: string }[] } | null;
  paper:
    | {
        symbol: string | null;
        status: string | null;
        side: string | null;
        entryPrice: number | null;
        lastPrice: number | null;
      }[]
    | null;
}

interface StripData {
  slice: CommandSlice | null;
  /** Wall-clock of the fetch that produced `slice`, so its age is visible. */
  fetchedAt: Date;
  /** The last fetch failed; `slice` is whatever the previous one left behind. */
  stale: boolean;
}

const PENDING: StripData = { slice: null, fetchedAt: new Date(0), stale: false };

/** Persian digits, so the strips match the shell's numerals. */
function fa(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "؟";
  return n.toLocaleString("fa-IR");
}

/** How long ago an ISO timestamp was, in Persian — "۱۲ دقیقه پیش". */
function faAgo(iso: string | null): string {
  if (!iso) return "UNKNOWN";
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return "UNKNOWN";
  const mins = Math.round((Date.now() - then) / 60_000);
  if (mins < 1) return "همین حالا";
  if (mins < 60) return `${fa(mins)} دقیقه پیش`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${fa(hours)} ساعت پیش`;
  return `${fa(Math.round(hours / 24))} روز پیش`;
}

export function TelemetryStrips() {
  const [data, setData] = useState<StripData>(PENDING);

  useEffect(() => {
    let cancelled = false;
    let alive = true;

    const load = async () => {
      try {
        const res = await webApiFetch("/api/command");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const slice = (await res.json()) as CommandSlice;
        if (!cancelled) setData({ slice, fetchedAt: new Date(), stale: false });
      } catch {
        // Keep the last reading and flag it. An unreachable API is not a reason
        // to erase what was true a minute ago.
        if (!cancelled) setData((prev) => ({ ...prev, stale: true, fetchedAt: new Date() }));
      }
    };

    void load();
    const timer = setInterval(() => {
      if (alive) void load();
    }, REFRESH_MS);
    return () => {
      cancelled = true;
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const { slice, fetchedAt, stale } = data;
  const state = slice?.state ?? null;
  const gates = slice?.health?.dimensions ?? null;
  const papers = slice?.paper ?? null;
  const open = papers ? papers.filter((p) => p.status === "OPEN").length : null;

  return (
    <section className="telemetry" dir="rtl" lang="fa" aria-label="نوارهای تله‌متری">
      <StripCell title="اجرا" hint={stale ? "غیر قابل دسترس — آخرین خوانت" : null}>
        {state ? (
          <>
            <p className="telemetry__line">
              <TruthBadge state={state.running ? "VERIFIED" : "UNKNOWN"} label={state.running ? "در حال اجرا" : "متوقف"} />
              <span className="telemetry__value">{fa(state.cycleCount)} چرخه</span>
            </p>
            <p className="telemetry__line telemetry__line--muted">
              آخرین چرخه {faAgo(state.lastCycleAt)}
              {state.lastCycleStatus ? ` — ${state.lastCycleStatus}` : ""}
            </p>
            {state.lastError ? (
              <p className="telemetry__line telemetry__line--err" title={state.lastError}>
                {state.lastError.slice(0, 90)}
              </p>
            ) : null}
          </>
        ) : (
          <UnknownLine label="اطلاعاتِ اجرا" />
        )}
      </StripCell>

      <StripCell title="دروازه‌ها">
        {gates && gates.length > 0 ? (
          <ul className="telemetry__gates">
            {gates.slice(0, MAX_GATE_ROWS).map((g) => (
              <li key={g.nameFa} className="telemetry__gate">
                <TruthBadge state={g.status} label={g.status} title={g.evidenceFa} />
                <span className="telemetry__gate-name">{g.nameFa}</span>
              </li>
            ))}
          </ul>
        ) : (
          <UnknownLine label="درگاه‌های سلامت" />
        )}
      </StripCell>

      <StripCell title="هزینه">
        {/* A constant, and shown as one: AHOS runs on free tiers and public data.
            Zero is a fact about the build, not a measurement that could go stale. */}
        <p className="telemetry__line">
          <TruthBadge state="VERIFIED" label="رایگان" />
          <span className="telemetry__value">۰</span>
        </p>
        <p className="telemetry__line telemetry__line--muted">
          منابعِ رایگان و دادهٔ عمومی — بدون سرویسِ پرداختی
        </p>
      </StripCell>

      <StripCell title="دفتر">
        {papers && papers.length > 0 ? (
          <>
            <p className="telemetry__line">
              <TruthBadge state={open ? "VERIFIED" : "UNKNOWN"} label={open ? "موقعیت باز" : "بدون موقعیت"} />
              <span className="telemetry__value">{fa(open)} از {fa(papers.length)}</span>
            </p>
            <ul className="telemetry__ledger">
              {papers.slice(0, MAX_LEDGER_ROWS).map((p, i) => (
                <li key={`${p.symbol ?? i}-${i}`} className="telemetry__ledger-row">
                  <bdi dir="ltr" className="telemetry__sym">{p.symbol ?? "؟"}</bdi>
                  <span className="telemetry__side">{p.side ?? "؟"}</span>
                  <span className="telemetry__status">{p.status ?? "؟"}</span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <UnknownLine label="موقعیت‌های کاغذی" />
        )}
      </StripCell>

      <p className="telemetry__age" aria-hidden="true">
        {fetchedAt.getTime() > 0 ? `به‌روزرسانی ${faAgo(fetchedAt.toISOString())}` : ""}
      </p>
    </section>
  );
}

function StripCell({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string | null;
  children: React.ReactNode;
}) {
  return (
    <div className="telemetry__cell">
      <h3 className="telemetry__cell-title">
        {title}
        {hint ? <span className="telemetry__stale">{hint}</span> : null}
      </h3>
      {children}
    </div>
  );
}

function UnknownLine({ label }: { label: string }) {
  return (
    <p className="telemetry__line telemetry__line--muted">
      <TruthBadge state="UNKNOWN" label="UNKNOWN" />
      <span className="telemetry__value">{label} بارگذاری نشد</span>
    </p>
  );
}
