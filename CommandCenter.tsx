"use client";

import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

type Dim = { nameFa: string; status: string; evidenceFa: string };
type Opp = {
  id: number;
  tokenKey: string;
  symbol: string;
  name: string | null;
  chain: string;
  address: string | null;
  decision: string;
  rankScore: number | null;
  confidence: string;
  securityStatus: string;
  evidenceCoverage: number | null;
  reasonsFa: string[] | null;
  risksFa: string[] | null;
  unknownsFa: string[] | null;
  invalidationFa: string | null;
  missingFa: string[] | null;
  councilVerdict: string | null;
  disagreement: boolean;
  payload: Record<string, unknown> | null;
};
type News = {
  id: number;
  source: string;
  sourceUrl: string | null;
  titleOriginal: string;
  titleFa: string | null;
  summaryFa: string | null;
  publishedAt: string | null;
  importance: string;
  category: string;
  sentiment: string;
};
type Provider = {
  provider: string;
  category: string;
  status: string;
  latencyMs: number | null;
  itemCount: number | null;
  messageFa: string | null;
};
type Snap = {
  generatedAt: string;
  state: {
    running: boolean;
    lastCycleAt: string | null;
    lastCycleStatus: string;
    cycleCount: number;
    lastError: string | null;
    intervalSec: number;
  };
  cycle: {
    id: number;
    status: string;
    durationMs: number | null;
    tokenCount: number | null;
    newsCount: number | null;
    opportunityCount: number | null;
    unknownShare: number | null;
    notesFa: string | null;
  } | null;
  market: {
    regime: string;
    fearGreed: number | null;
    fearGreedLabel: string | null;
    btcPrice: number | null;
    btcChange24h: number | null;
    ethPrice: number | null;
    ethChange24h: number | null;
    solPrice: number | null;
    solChange24h: number | null;
    totalMcap: number | null;
    btcDominance: number | null;
    defiTvl: number | null;
  } | null;
  opportunities: Opp[];
  news: News[];
  providers: Provider[];
  watchlist: Array<{ id: number; symbol: string; chain: string; thesisFa: string | null }>;
  paper: Array<{
    id: number;
    symbol: string;
    status: string;
    entryPrice: number | null;
    lastPrice: number | null;
    maxFavorable: number | null;
    maxAdverse: number | null;
  }>;
  lessons: Array<{ id: number; titleFa: string; bodyFa: string }>;
  findings: Array<{ id: number; titleFa: string; evidenceFa: string; severity: string }>;
  council: Array<{
    tokenKey: string;
    verdict: string;
    summaryFa: string;
    watchCount: number;
    rejectCount: number;
    abstainCount: number;
  }>;
  health: { dimensions: Dim[] };
  blocked: Array<{ item: string; status: string }>;
  teams: Array<{ id: string; fa: string; size: number }>;
};

type ChatMsg = { role: "user" | "assistant"; content: string };
type TabId = "dash" | "opp" | "news" | "council" | "watch" | "evo";

const TABS: ReadonlyArray<readonly [TabId, string]> = [
  ["dash", "داشبورد"],
  ["opp", "فرصت‌ها"],
  ["news", "اخبار فارسی"],
  ["council", "شورای ۱۰۰ نفره"],
  ["watch", "پایش / کاغذی"],
  ["evo", "تکامل و درس"],
] as const;

const QUICK_PROMPTS = [
  "امروز بازار چه خبر؟",
  "بهترین فرصت‌ها چیه؟",
  "اخبار سولانا",
  "سیستم کجاش لنگه؟",
  "شروع کن",
] as const;

const MAX_CHAT = 80;
const POLL_RUNNING_MS = 10_000;
const POLL_IDLE_MS = 25_000;

const faFmt = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 });
const faFmt0 = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 });
const faFmt6 = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 6 });

function faNum(n: number | null | undefined, d = 2) {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  if (d === 0) return faFmt0.format(n);
  if (d >= 6) return faFmt6.format(n);
  return faFmt.format(n);
}
function faUsd(n: number | null | undefined) {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  const a = Math.abs(n);
  if (a >= 1e12) return `${faNum(n / 1e12)} ت دلار`;
  if (a >= 1e9) return `${faNum(n / 1e9)} م‌م دلار`;
  if (a >= 1e6) return `${faNum(n / 1e6)} م دلار`;
  if (a >= 1e3) return `${faNum(n / 1e3)} ه دلار`;
  return `${faNum(n, n < 1 ? 6 : 2)} دلار`;
}
function faPct(n: number | null | undefined) {
  if (n == null || !Number.isFinite(n)) return "نامشخص";
  return `${n > 0 ? "+" : ""}${faNum(n)}٪`;
}

let sharedAudioCtx: AudioContext | null = null;
function beep(ok: boolean, enabled: boolean) {
  if (!enabled || typeof window === "undefined") return;
  try {
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!sharedAudioCtx) sharedAudioCtx = new Ctx();
    const ctx = sharedAudioCtx;
    if (ctx.state === "suspended") void ctx.resume();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "triangle";
    o.frequency.value = ok ? 880 : 220;
    g.gain.value = 0.04;
    o.connect(g);
    g.connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + 0.09);
  } catch {
    /* ignore */
  }
}

export default function CommandCenter() {
  const [snap, setSnap] = useState<Snap | null>(null);
  const [tab, setTab] = useState<TabId>("dash");
  const [chat, setChat] = useState<ChatMsg[]>([
    {
      role: "assistant",
      content:
        "سلام. من AHOS هستم — مثل یک همکار صریح. اگر داده نباشد می‌گویم UNKNOWN، حدس نمی‌زنم. یک‌بار «شروع پروژه» را بزن؛ خودم پشت‌سرهم جمع می‌کنم و وسط کار وای نمی‌ایستم. معامله واقعی خاموش است (فقط کاغذی).",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [sound, setSound] = useState(false);
  const [selected, setSelected] = useState<Opp | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);

  const chatRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<HTMLDivElement>(null);
  const soundRef = useRef(sound);
  const snapGenRef = useRef<string | null>(null);
  const loadAbortRef = useRef<AbortController | null>(null);
  const running = snap?.state.running ?? false;

  useEffect(() => {
    soundRef.current = sound;
  }, [sound]);

  const load = useCallback(async () => {
    loadAbortRef.current?.abort();
    const ac = new AbortController();
    loadAbortRef.current = ac;
    try {
      const res = await fetch("/api/command", { cache: "no-store", signal: ac.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as Snap;
      if (ac.signal.aborted) return;
      if (json.generatedAt && json.generatedAt === snapGenRef.current) return;
      snapGenRef.current = json.generatedAt ?? null;
      setSnap(json);
      setBootError(null);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setBootError(e instanceof Error ? e.message : "UNKNOWN");
    }
  }, []);

  useEffect(() => {
    void load();
    return () => loadAbortRef.current?.abort();
  }, [load]);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    const tick = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      void load();
    };

    const arm = () => {
      if (timer) clearInterval(timer);
      timer = setInterval(tick, running ? POLL_RUNNING_MS : POLL_IDLE_MS);
    };

    arm();

    const onVis = () => {
      if (document.visibilityState === "visible") {
        void load();
        arm();
      }
    };
    document.addEventListener("visibilitychange", onVis);
    return () => {
      if (timer) clearInterval(timer);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [load, running]);

  useEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [chat]);

  useEffect(() => {
    let raf = 0;
    const onMove = (e: MouseEvent) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const node = cursorRef.current;
        if (!node) return;
        node.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
      });
    };
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => {
      window.removeEventListener("mousemove", onMove);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  const act = useCallback(
    async (action: "start" | "stop" | "cycle") => {
      setBusy(action);
      try {
        const res = await fetch("/api/engine", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action }),
        });
        const json = (await res.json()) as { ok?: boolean };
        beep(Boolean(json.ok), soundRef.current);
        await load();
      } catch {
        beep(false, soundRef.current);
      } finally {
        setBusy(null);
      }
    },
    [load],
  );

  const send = useCallback(async () => {
    const message = draft.trim();
    if (!message) return;
    setDraft("");
    setChat((c) => {
      const next: ChatMsg[] = [...c, { role: "user", content: message }];
      return next.length > MAX_CHAT ? next.slice(next.length - MAX_CHAT) : next;
    });
    setBusy("chat");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const json = (await res.json()) as { reply?: string };
      setChat((c) => {
        const next: ChatMsg[] = [...c, { role: "assistant", content: json.reply || "UNKNOWN" }];
        return next.length > MAX_CHAT ? next.slice(next.length - MAX_CHAT) : next;
      });
      beep(true, soundRef.current);
      await load();
    } catch {
      setChat((c) => [
        ...c,
        { role: "assistant", content: "ارتباط قطع شد — DOWN. چیزی جعل نکردم." },
      ]);
      beep(false, soundRef.current);
    } finally {
      setBusy(null);
    }
  }, [draft, load]);

  const watch = useCallback(
    async (o: Opp) => {
      setBusy(`watch-${o.id}`);
      try {
        await fetch("/api/watch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tokenKey: o.tokenKey,
            symbol: o.symbol,
            chain: o.chain,
            address: o.address,
            thesisFa: "از داشبورد",
          }),
        });
        beep(true, soundRef.current);
        await load();
      } catch {
        beep(false, soundRef.current);
      } finally {
        setBusy(null);
      }
    },
    [load],
  );

  const paper = useCallback(
    async (o: Opp) => {
      setBusy(`paper-${o.id}`);
      try {
        const price = typeof o.payload?.priceUsd === "number" ? o.payload.priceUsd : null;
        await fetch("/api/paper", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tokenKey: o.tokenKey,
            symbol: o.symbol,
            chain: o.chain,
            address: o.address,
            entryPrice: price,
            thesisFa: "کاغذی از داشبورد",
          }),
        });
        beep(true, soundRef.current);
        await load();
      } catch {
        beep(false, soundRef.current);
      } finally {
        setBusy(null);
      }
    },
    [load],
  );

  const toggleSound = useCallback(() => setSound((s) => !s), []);
  const closeModal = useCallback(() => setSelected(null), []);

  const ticker = useMemo(() => {
    const bits = [
      `رژیم ${snap?.market?.regime ?? "UNKNOWN"}`,
      `BTC ${faUsd(snap?.market?.btcPrice)} ${faPct(snap?.market?.btcChange24h)}`,
      `ETH ${faUsd(snap?.market?.ethPrice)}`,
      `SOL ${faUsd(snap?.market?.solPrice)}`,
      `چرخه ${snap?.state.cycleCount ?? 0}`,
      `آخرین ${snap?.state.lastCycleStatus ?? "UNKNOWN"}`,
      "PAPER ONLY",
      "UNKNOWN > fabricated",
    ];
    return `${bits.join("   ·   ")}   ·   ${bits.join("   ·   ")}`;
  }, [snap]);

  const showAlarm =
    snap?.state.lastCycleStatus === "CODE_FAILURE" ||
    (snap?.state.lastError != null && snap.state.lastError.length > 0);

  const opps = useMemo(() => (snap?.opportunities ?? []).slice(0, 16), [snap?.opportunities]);
  const providers = useMemo(() => (snap?.providers ?? []).slice(0, 18), [snap?.providers]);
  const council = useMemo(() => (snap?.council ?? []).slice(0, 6), [snap?.council]);

  return (
    <div className="stage">
      <div className="stage-void" />
      <div className="stage-grid" />
      <div className="stage-vignette" />
      <div className="stage-scan" />
      <div ref={cursorRef} className="cursor-glow" style={{ left: 0, top: 0, willChange: "transform" }} />

      {showAlarm && (
        <div className="alarm-banner">
          هشدار سیستم
          <small>{snap?.state.lastError || "CODE_FAILURE — چرخه اخیر ناموفق"}</small>
        </div>
      )}

      <header className="relative z-10 mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4 px-4 py-5 md:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/15 ring-1 ring-cyan-300/40 font-[var(--font-orbitron)] text-cyan-200">
            AH
          </div>
          <div>
            <p className="m-0 font-[var(--font-orbitron)] text-[11px] tracking-[0.28em] text-cyan-300">
              AHOS COMMAND CENTER
            </p>
            <h1 className="m-0 text-xl font-semibold md:text-2xl">مرکز فرماندهی هوشمند فرصت‌های رمزارز</h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`rounded-full px-3 py-1 text-xs ${
              running ? "bg-emerald-400/20 text-emerald-200" : "bg-white/10 text-white/70"
            }`}
          >
            {running ? "در حال مشاهده خودکار" : "متوقف"}
          </span>
          <span className="rounded-full bg-amber-300/15 px-3 py-1 text-xs text-amber-200">
            فقط کاغذی — معامله واقعی خاموش
          </span>
          <Hud onClick={toggleSound} active={sound}>
            صدا {sound ? "روشن" : "خاموش"}
          </Hud>
        </div>
      </header>

      <div className="relative z-10 overflow-hidden border-y border-cyan-300/10 bg-black/30 py-2">
        <div className="ticker whitespace-nowrap text-sm text-cyan-100/80">{ticker}</div>
      </div>

      <main className="relative z-10 mx-auto grid max-w-[1500px] grid-cols-1 gap-5 px-4 py-6 lg:grid-cols-[1.15fr_0.85fr] md:px-8">
        <section className="scene enter-up">
          <div className="glass glass-holo relative overflow-hidden rounded-[28px] p-6 md:p-8">
            <div className="absolute -left-10 top-6 hidden h-44 w-44 float-y md:block">
              <div className="pulse-ring absolute inset-0 rounded-full border border-cyan-300/40" />
              <div className="orb-spin h-full w-full rounded-full bg-gradient-to-br from-cyan-400/40 via-fuchsia-500/30 to-amber-300/20 opacity-90" />
            </div>
            <div className="md:pr-40">
              <p className="m-0 text-sm text-cyan-100/80">
                مشاهده → شواهد → تحلیل → امتیاز چندعاملی → تصمیم‌یار → یادگیری. هیچ قیمت، خبر یا اطمینان جعلی ساخته
                نمی‌شود. یک‌بار شروع کن؛ تا توقف خودش ادامه می‌دهد.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Hud
                  className="is-primary min-w-[160px] text-base"
                  loading={busy === "start"}
                  onClick={() => void act("start")}
                >
                  شروع پروژه
                </Hud>
                <Hud loading={busy === "stop"} onClick={() => void act("stop")}>
                  توقف
                </Hud>
                <Hud loading={busy === "cycle"} onClick={() => void act("cycle")}>
                  یک چرخه فوری
                </Hud>
              </div>
              <p className="mt-4 text-sm text-white/70">
                آخرین چرخه: {snap?.state.lastCycleStatus ?? "UNKNOWN"} — تعداد {faNum(snap?.state.cycleCount, 0)} —
                توکن‌ها {faNum(snap?.cycle?.tokenCount, 0)} — اخبار {faNum(snap?.cycle?.newsCount, 0)}
                {snap?.state.lastError ? ` — خطا: ${snap.state.lastError}` : ""}
                {bootError ? ` — ارتباط: ${bootError}` : ""}
              </p>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
              <Metric label="بیت‌کوین" value={faUsd(snap?.market?.btcPrice)} sub={faPct(snap?.market?.btcChange24h)} />
              <Metric label="اتریوم" value={faUsd(snap?.market?.ethPrice)} sub={faPct(snap?.market?.ethChange24h)} />
              <Metric label="سولانا" value={faUsd(snap?.market?.solPrice)} sub={faPct(snap?.market?.solChange24h)} />
              <Metric
                label="ترس/طمع"
                value={faNum(snap?.market?.fearGreed, 0)}
                sub={snap?.market?.fearGreedLabel ?? "UNKNOWN"}
              />
            </div>
          </div>

          <nav className="mt-4 flex flex-wrap gap-2">
            {TABS.map(([id, label]) => (
              <Hud key={id} active={tab === id} onClick={() => setTab(id)}>
                {label}
              </Hud>
            ))}
          </nav>

          {tab === "dash" && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card title="سلامت سیستم">
                <div className="grid gap-2">
                  {(snap?.health?.dimensions || []).map((d) => (
                    <div
                      key={d.nameFa}
                      className="flex items-start justify-between gap-3 rounded-2xl bg-white/5 px-3 py-2"
                    >
                      <div>
                        <div className="text-sm">{d.nameFa}</div>
                        <div className="text-xs text-white/60">{d.evidenceFa}</div>
                      </div>
                      <StatusPill status={d.status} />
                    </div>
                  ))}
                  {!snap?.health?.dimensions?.length && <Empty text="هنوز ابعادی نیست — موتور را روشن کن." />}
                </div>
              </Card>
              <Card title="پروایدرها (صادقانه)">
                <div className="max-h-[360px] space-y-2 overflow-auto scroll-thin">
                  {providers.map((p, i) => (
                    <div
                      key={`${p.provider}-${i}`}
                      className="flex items-center justify-between gap-2 rounded-2xl bg-white/5 px-3 py-2 text-sm"
                    >
                      <div>
                        <div>
                          {p.provider} <span className="text-white/40">/{p.category}</span>
                        </div>
                        <div className="text-xs text-white/50">{p.messageFa}</div>
                      </div>
                      <StatusPill status={p.status} />
                    </div>
                  ))}
                  {(snap?.blocked || []).map((b) => (
                    <div key={b.item} className="flex justify-between rounded-2xl bg-rose-500/10 px-3 py-2 text-sm">
                      <span>{b.item}</span>
                      <StatusPill status={b.status} />
                    </div>
                  ))}
                  {!providers.length && <Empty text="بعد از اولین چرخه وضعیت واقعی پروایدر می‌آید." />}
                </div>
              </Card>
            </div>
          )}

          {tab === "opp" && (
            <div className="mt-4 grid gap-4">
              {opps.map((o) => (
                <article key={o.id} className="glass rounded-[24px] p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="m-0 text-lg">
                        {o.symbol} <span className="text-sm text-white/50">{o.chain}</span>
                      </h3>
                      <p className="m-0 text-xs text-white/50">
                        {o.name} · {o.tokenKey}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusPill status={o.decision} />
                      <StatusPill status={o.confidence} />
                      <StatusPill status={o.securityStatus} />
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-cyan-100/90">{(o.reasonsFa || [])[0]}</p>
                  <p className="text-sm text-rose-200/90">ریسک: {(o.risksFa || [])[0]}</p>
                  <p className="text-xs text-amber-200/80">
                    UNKNOWN: {(o.unknownsFa || []).join(" | ") || "—"}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Hud onClick={() => setSelected(o)}>چرا؟</Hud>
                    <Hud loading={busy === `watch-${o.id}`} onClick={() => void watch(o)}>
                      زیر نظر بگیر
                    </Hud>
                    <Hud loading={busy === `paper-${o.id}`} onClick={() => void paper(o)}>
                      خرید کاغذی
                    </Hud>
                  </div>
                </article>
              ))}
              {!opps.length && (
                <Empty text="فرصتی نیست. شروع را بزن تا DexScreener و GeckoTerminal خوانده شوند." />
              )}
            </div>
          )}

          {tab === "news" && (
            <div className="mt-4 grid gap-3">
              {(snap?.news || []).map((n) => (
                <article key={n.id} className="glass rounded-[22px] p-4">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-white/60">
                    <StatusPill status={n.importance} />
                    <span>{n.source}</span>
                    <span>{n.category}</span>
                    <span>{n.sentiment}</span>
                  </div>
                  <h3 className="mt-2 text-base">{n.titleFa || "ترجمه نامشخص"}</h3>
                  <p className="text-sm text-white/70">{n.summaryFa}</p>
                  <p className="text-xs text-white/40">{n.titleOriginal}</p>
                  {n.sourceUrl && (
                    <a className="text-xs text-cyan-300" href={n.sourceUrl} target="_blank" rel="noreferrer">
                      منبع اصلی
                    </a>
                  )}
                </article>
              ))}
              {!snap?.news?.length && (
                <Empty text="خبری جمع نشده. اگر RSSها DOWN باشند SOURCE_UNAVAILABLE می‌ماند." />
              )}
            </div>
          )}

          {tab === "council" && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card title="ده تیم × ده کارشناس">
                <div className="grid gap-2">
                  {(snap?.teams || []).map((t) => (
                    <div key={t.id} className="rounded-2xl bg-white/5 px-3 py-2 text-sm">
                      {t.fa} — {t.size} نقش مشورتی
                    </div>
                  ))}
                  {!snap?.teams?.length && <Empty text="متادیتای تیم‌ها بعد از اولین snapshot می‌آید." />}
                </div>
              </Card>
              <Card title="آخرین احکام">
                {council.map((c, i) => (
                  <div key={`${c.tokenKey}-${i}`} className="mb-2 rounded-2xl bg-white/5 p-3 text-sm">
                    <div className="flex justify-between gap-2">
                      <b>{c.tokenKey}</b>
                      <StatusPill status={c.verdict} />
                    </div>
                    <p className="m-0 mt-1 text-white/70">{c.summaryFa}</p>
                    <p className="m-0 text-xs text-white/50">
                      WATCH {c.watchCount} · REJECT {c.rejectCount} · ABSTAIN {c.abstainCount}
                    </p>
                  </div>
                ))}
                {!council.length && <Empty text="پس از چرخه، اختلاف نظر تیم‌ها اینجا می‌ماند." />}
              </Card>
            </div>
          )}

          {tab === "watch" && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card title="واچ‌لیست">
                {(snap?.watchlist || []).map((w) => (
                  <div key={w.id} className="mb-2 rounded-2xl bg-white/5 p-3 text-sm">
                    {w.symbol} / {w.chain}
                    <div className="text-white/60">{w.thesisFa}</div>
                  </div>
                ))}
                {!snap?.watchlist?.length && (
                  <Empty text="خالی است. از کارت فرصت یا چت بگو زیر نظر بگیر." />
                )}
              </Card>
              <Card title="موقعیت کاغذی">
                {(snap?.paper || []).map((p) => (
                  <div key={p.id} className="mb-2 rounded-2xl bg-white/5 p-3 text-sm">
                    {p.symbol} — {p.status}
                    <div className="text-white/60">
                      ورود {faUsd(p.entryPrice)} · الان {faUsd(p.lastPrice)} · MFE{" "}
                      {p.maxFavorable ?? "نامشخص"} · MAE {p.maxAdverse ?? "نامشخص"}
                    </div>
                  </div>
                ))}
                {!snap?.paper?.length && <Empty text="خرید واقعی وجود ندارد. فقط کاغذی." />}
              </Card>
            </div>
          )}

          {tab === "evo" && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card title="درس‌ها">
                {(snap?.lessons || []).map((l) => (
                  <div key={l.id} className="mb-2 rounded-2xl bg-white/5 p-3 text-sm">
                    <b>{l.titleFa}</b>
                    <div className="text-white/70">{l.bodyFa}</div>
                  </div>
                ))}
                {!snap?.lessons?.length && <Empty text="تا افق پیش‌بینی بسته نشود درس جعل نمی‌شود." />}
              </Card>
              <Card title="یافته‌ها">
                {(snap?.findings || []).map((f) => (
                  <div key={f.id} className="mb-2 rounded-2xl bg-white/5 p-3 text-sm">
                    <div className="flex justify-between">
                      <b>{f.titleFa}</b>
                      <StatusPill status={f.severity} />
                    </div>
                    <div className="text-white/70">{f.evidenceFa}</div>
                  </div>
                ))}
                {!snap?.findings?.length && <Empty text="یافته‌ای ثبت نشده." />}
              </Card>
            </div>
          )}
        </section>

        <aside className="glass flex min-h-[70vh] flex-col rounded-[28px] p-4 md:p-5 enter-up">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="m-0 text-lg">گفت‌وگو با AHOS</h2>
            <span className="text-xs text-white/50">رایگان · محلی · بدون confidence جعلی</span>
          </div>
          <div ref={chatRef} className="scroll-thin flex-1 space-y-3 overflow-auto pe-1">
            {chat.map((m, i) => (
              <div
                key={i}
                className={`max-w-[95%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm leading-7 ${
                  m.role === "user" ? "ms-auto bg-cyan-300/15" : "bg-white/8"
                }`}
              >
                {m.content}
              </div>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((q) => (
              <button key={q} type="button" className="hud-btn !px-3 !py-1 text-xs" onClick={() => setDraft(q)}>
                {q}
              </button>
            ))}
          </div>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="خودمانی بپرس؛ مثلاً این توکن را زیر نظر بگیر"
              className="flex-1 rounded-2xl border border-cyan-300/20 bg-black/40 px-4 py-3 text-sm outline-none ring-cyan-300/40 focus:ring"
            />
            <Hud loading={busy === "chat"} onClick={() => void send()}>
              بفرست
            </Hud>
          </form>
        </aside>
      </main>

      {selected && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4" onClick={closeModal}>
          <div
            className="glass max-h-[85vh] w-full max-w-2xl overflow-auto rounded-[28px] p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mt-0 text-2xl">{selected.symbol} — چرا این حکم؟</h3>
            <p>
              تصمیم {selected.decision} · اطمینان {selected.confidence} · شورا {selected.councilVerdict}
            </p>
            <h4>شواهد مثبت</h4>
            <ul>
              {(selected.reasonsFa || []).map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
            <h4>ریسک</h4>
            <ul>
              {(selected.risksFa || []).map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
            <h4>UNKNOWN</h4>
            <ul>
              {(selected.unknownsFa || []).map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
            <h4>داده کم</h4>
            <p>{(selected.missingFa || []).join("، ") || "—"}</p>
            <p>ابطال: {selected.invalidationFa}</p>
            <p className="text-amber-200">تصمیم نهایی با کاربر است. خرید واقعی انجام نمی‌شود.</p>
            <Hud onClick={closeModal}>بستن</Hud>
          </div>
        </div>
      )}
    </div>
  );
}

const Hud = memo(function Hud({
  children,
  onClick,
  loading,
  active,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  loading?: boolean;
  active?: boolean;
  className?: string;
}) {
  const [press, setPress] = useState(false);
  return (
    <button
      type="button"
      className={`hud-btn ${loading ? "is-loading" : ""} ${press ? "is-press" : ""} ${active ? "is-ok" : ""} ${className}`}
      onMouseDown={() => setPress(true)}
      onMouseUp={() => setPress(false)}
      onMouseLeave={() => setPress(false)}
      onClick={onClick}
      disabled={loading}
    >
      {loading ? "…" : children}
    </button>
  );
});

const Card = memo(function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="glass rounded-[24px] p-4">
      <h3 className="mt-0 mb-3 text-base">{title}</h3>
      {children}
    </section>
  );
});

const Metric = memo(function Metric({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="metric-tile">
      <div className="text-xs text-white/50">{label}</div>
      <div className="text-lg">{value}</div>
      <div className="text-xs text-cyan-200/80">{sub}</div>
    </div>
  );
});

const StatusPill = memo(function StatusPill({ status }: { status: string }) {
  const tone =
    status === "SUCCESS" || status === "OK" || status === "WATCH" || status === "HIGH"
      ? "bg-emerald-400/15 text-emerald-200"
      : status === "REJECT" ||
          status === "DOWN" ||
          status === "HONEYPOT" ||
          status === "DISABLED" ||
          status === "CODE_FAILURE"
        ? "bg-rose-400/15 text-rose-200"
        : status === "UNKNOWN" ||
            status === "NO_DATA" ||
            status === "INSUFFICIENT_EVIDENCE" ||
            status === "ABSTAIN"
          ? "bg-amber-400/15 text-amber-100"
          : "bg-white/10 text-white/80";
  return <span className={`rounded-full px-2 py-0.5 text-[11px] ${tone}`}>{status}</span>;
});

const Empty = memo(function Empty({ text }: { text: string }) {
  return <p className="m-0 text-sm text-white/55">{text}</p>;
});
