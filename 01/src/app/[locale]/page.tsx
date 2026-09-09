import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowDown, Fingerprint, FlaskConical, Newspaper, Quote, ScrollText,
  ShieldAlert, Sparkles, Trophy, Waves,
} from "lucide-react";
import { getOverview, getTickerItems, type AlertRow, type Stance } from "@/lib/engine";
import { getDict, isLocale, type Dict, type Locale } from "@/lib/dict";
import { fmtInt, timeAgo } from "@/lib/format";
import Reveal from "@/components/reveal";
import Counter from "@/components/counter";
import Ticker from "@/components/ticker";
import { Radar, ScoreRing, Sparkline } from "@/components/charts";
import TreeCanvas from "@/components/tree-canvas";
import { Badge, Kicker, Monogram, Panel, SectionHead } from "@/components/primitives";
import { TeamCard } from "@/components/team";
import {
  CHAIN_LABEL, DECISION_TONE, IDENTITY_TONE, PROVIDER_TONE, TONE,
  cx, type Tone,
} from "@/lib/ui";

export const dynamic = "force-dynamic";

const ALERT_ICON: Record<string, typeof Trophy> = {
  OPPORTUNITY: Trophy, SECURITY: ShieldAlert, IDENTITY: Fingerprint,
  WHALE: Waves, PAPER: FlaskConical, DAILY: ScrollText, NEWS: Newspaper,
};
const SEV_TONE: Record<string, Tone> = {
  CRITICAL: "rose", HIGH: "amber", MEDIUM: "sky", LOW: "zinc", INFO: "cyan",
};

function gateTone(v: string): Tone {
  return v === "PASS" ? "jade" : v === "WARN" || v === "INCOMPLETE" ? "amber" : "rose";
}

/* ============================ page ============================ */

export default async function Dashboard({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const loc: Locale = locale;
  const dict = getDict(loc);
  const fa = loc === "fa";
  const [ov, tickerItems] = await Promise.all([getOverview(), getTickerItems()]);
  const gateDict = dict.gate as Record<string, string>;

  return (
    <div className="relative">
      {/* ============================ HERO ============================ */}
      <section className="relative flex min-h-[calc(100svh-84px)] items-center overflow-hidden">
        <div className="bg-grid pointer-events-none absolute inset-0" />
        <div className="pointer-events-none absolute inset-0 grid place-items-center">
          <span className="outline-word select-none text-[26vw] font-black leading-none tracking-tighter opacity-70">
            {fa ? "اهوس" : "AHOS"}
          </span>
        </div>

        <div className="relative z-10 mx-auto w-full max-w-7xl px-5 py-16">
          <div className="grid items-center gap-14 lg:grid-cols-[1.15fr_0.85fr]">
            {/* copy */}
            <div>
              <Reveal>
                <div className="flex flex-wrap items-center gap-3">
                  <Kicker>{dict.hero.kicker}</Kicker>
                  <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-mist">
                    {dict.common.demo}
                  </span>
                </div>
              </Reveal>
              <Reveal delay={90}>
                <h1 className="mt-7 text-[13vw] font-black leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
                  <span className="text-frost">{dict.hero.titleA}</span>
                  <br />
                  <span className="text-grad-gold">{dict.hero.titleB}</span>
                </h1>
              </Reveal>
              <Reveal delay={180}>
                <p className="mt-6 max-w-xl text-[15px] leading-8 text-mist">{dict.hero.sub}</p>
              </Reveal>
              <Reveal delay={260}>
                <div className="mt-9 flex flex-wrap items-center gap-4">
                  <Link
                    href={`/${loc}/opportunities`}
                    className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-gradient-to-l from-jade-500 to-jade-400 px-7 py-3.5 text-sm font-extrabold text-abyss-950 shadow-[0_18px_44px_-16px_rgba(16,185,129,0.7)] transition-transform hover:scale-[1.03]"
                  >
                    <span className="shimmer-line pointer-events-none absolute inset-0" />
                    {dict.hero.ctaPrimary}
                  </Link>
                  <Link
                    href={`/${loc}/council`}
                    className="rounded-full border border-white/12 bg-white/5 px-7 py-3.5 text-sm font-bold text-frost/90 backdrop-blur transition hover:border-gild-400/40 hover:text-gild-300"
                  >
                    {dict.hero.ctaSecondary}
                  </Link>
                </div>
              </Reveal>
              <Reveal delay={340}>
                <div className="mt-12 grid max-w-xl grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { v: ov.stats.tracked, f: "int" as const, l: dict.hero.stats.tracked },
                    { v: ov.decisionsCount, f: "int" as const, l: dict.hero.stats.decisions },
                    { v: ov.stats.paperPnl, f: "usd" as const, l: dict.hero.stats.paperPnl },
                    { v: ov.stats.winRate ?? 0, f: "pctPlain" as const, l: dict.hero.stats.winRate },
                  ].map((s) => (
                    <div key={s.l} className="glass-soft rounded-2xl px-4 py-3">
                      <Counter
                        locale={loc}
                        value={s.v}
                        format={s.f}
                        className="num block text-xl font-black text-frost"
                      />
                      <span className="mt-1 block text-[10px] leading-4 text-mist">{s.l}</span>
                    </div>
                  ))}
                </div>
              </Reveal>
            </div>

            {/* golden fruit card */}
            <Reveal delay={220} className="hidden lg:block">
              {ov.golden && ov.golden.scores ? (
                <div className="a-floaty relative mx-auto w-full max-w-sm">
                  <div className="absolute -inset-6 rounded-[2.2rem] bg-gradient-to-b from-gild-400/12 via-transparent to-transparent blur-xl" />
                  <div className="glass gold-hair a-glow-gold relative rounded-[1.8rem] p-6">
                    <div className="flex items-center justify-between">
                      <Kicker tone="gold">{dict.golden.kicker}</Kicker>
                      <Sparkles className="size-4 text-gild-300" />
                    </div>
                    <div className="mt-5 flex items-center gap-4">
                      <Monogram symbol={ov.golden.token.symbol} seed={ov.golden.token.slug} size={56} />
                      <div>
                        <div className="text-lg font-black text-frost">
                          {fa ? ov.golden.token.nameFa : ov.golden.token.name}
                        </div>
                        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-mist">
                          <span className="num">{ov.golden.token.symbol}</span>
                          <span>·</span>
                          <span>{CHAIN_LABEL[ov.golden.token.chain]}</span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-6 flex items-center justify-between gap-4">
                      <ScoreRing
                        value={ov.golden.scores.opportunity}
                        size={118}
                        tone="gold"
                        label={dict.scores.opportunity}
                      />
                      <div className="grow space-y-2">
                        <Badge
                          label={dict.decision[ov.golden.decision!.kind]}
                          tone={DECISION_TONE[ov.golden.decision!.kind]}
                          pulse
                        />
                        <div className="text-[11px] text-mist">
                          {dict.golden.confidence}:{" "}
                          <span className="num font-bold text-frost">{ov.golden.scores.confidence}</span>
                        </div>
                        <Sparkline data={ov.golden.token.sparkline} w={130} h={38} />
                      </div>
                    </div>
                    <div className="mt-5 grid grid-cols-2 gap-1.5">
                      {Object.entries(ov.golden.decision!.gateSnapshot).map(([k, v]) => (
                        <span
                          key={k}
                          className={cx(
                            "rounded-lg border px-2.5 py-1.5 text-center text-[10px] font-semibold",
                            TONE[gateTone(v)].border, TONE[gateTone(v)].bg, TONE[gateTone(v)].text,
                          )}
                        >
                          {(dict.dossier.gates as Record<string, string>)[k] ?? k} · {gateDict[v] ?? v}
                        </span>
                      ))}
                    </div>
                    <Link
                      href={`/${loc}/token/${ov.golden.token.slug}`}
                      className="mt-5 block rounded-xl bg-gild-400/15 py-3 text-center text-[12px] font-extrabold text-gild-300 transition hover:bg-gild-400/25"
                    >
                      {dict.golden.viewDossier}
                    </Link>
                  </div>
                </div>
              ) : null}
            </Reveal>
          </div>

          {/* scroll cue */}
          <div className="pointer-events-none absolute bottom-5 start-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-mist/70 rtl:translate-x-1/2">
            <div className="h-8 w-px overflow-hidden bg-white/10">
              <div className="a-cue h-full w-px bg-jade-400" />
            </div>
            <ArrowDown className="size-3.5" />
          </div>
        </div>
      </section>

      {/* market tape */}
      <Ticker items={tickerItems} locale={loc} />

      {/* ============================ philosophy ============================ */}
      <section className="mx-auto max-w-4xl px-5 py-24 text-center">
        <Reveal>
          <Quote className="mx-auto size-8 text-gild-400/70" />
          <p className="mt-6 text-xl font-bold leading-relaxed text-frost/90 sm:text-2xl sm:leading-relaxed">
            {dict.philo.quote}
          </p>
          <p className="mt-4 text-xs tracking-wide text-mist">{dict.philo.author}</p>
        </Reveal>
      </section>

      {/* ============================ funnel ============================ */}
      <section className="mx-auto max-w-7xl px-5 py-10">
        <Reveal>
          <SectionHead
            kicker={dict.funnel.kicker}
            title={<span className="text-grad-jade">{dict.funnel.title}</span>}
            sub={dict.funnel.sub}
          />
        </Reveal>
        <Reveal delay={120}>
          <Panel hover={false} className="relative overflow-hidden !p-8">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_120%_at_50%_0%,rgba(52,211,153,0.06),transparent)]" />
            <div className="relative space-y-3.5">
              {ov.funnel.stages.map((v, i) => {
                const max = ov.funnel.stages[0];
                const wPct = Math.max(7, Math.min(100, (Math.log10(v + 1) / Math.log10(max + 1)) * 100));
                const last = i === ov.funnel.stages.length - 1;
                return (
                  <div key={i} className="flex items-center gap-4">
                    <span className="w-20 shrink-0 text-end text-[11px] text-mist sm:w-28 sm:text-xs">
                      {dict.funnel.stages[i]}
                    </span>
                    <div className="relative h-9 grow">
                      <div
                        className={cx(
                          "bar-grow flex h-full items-center justify-end rounded-xl pe-3",
                          last
                            ? "bg-gradient-to-r from-gild-500/70 to-gild-300/90 shadow-[0_0_26px_-6px_rgba(245,183,63,0.6)]"
                            : "bg-gradient-to-r from-jade-500/25 to-jade-400/45",
                        )}
                        style={{ width: `${wPct}%`, animationDelay: `${i * 120}ms` }}
                      >
                        <span className={cx("num text-[11px] font-black", last ? "text-abyss-950" : "text-frost/90")}>
                          {fmtInt(loc, v)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="relative mt-6 flex flex-wrap items-center justify-between gap-3 text-[11px] text-mist">
              <span>{dict.funnel.note}</span>
              <span className="font-semibold text-vio">{dict.funnel.skip}</span>
            </div>
          </Panel>
        </Reveal>
      </section>

      {/* ============================ golden dossier preview ============================ */}
      {ov.golden && ov.golden.scores && ov.golden.decision ? (
        <section className="mx-auto max-w-7xl px-5 py-16">
          <Reveal>
            <SectionHead
              kicker={dict.golden.kicker}
              tone="gold"
              title={
                <span>
                  {fa ? ov.golden.token.nameFa : ov.golden.token.name}{" "}
                  <span className="text-grad-gold num">{ov.golden.token.symbol}</span>
                </span>
              }
              sub={fa ? ov.golden.token.summaryFa : ov.golden.token.summaryEn}
              href={`/${loc}/token/${ov.golden.token.slug}`}
              action={dict.golden.viewDossier}
            />
          </Reveal>
          <div className="grid gap-6 lg:grid-cols-2">
            <Reveal delay={80}>
              <Panel hover={false} className="h-full">
                <div className="flex flex-wrap items-center justify-around gap-6">
                  <Radar
                    size={280}
                    axes={([
                      ["opportunity", ov.golden.scores.opportunity],
                      ["security", ov.golden.scores.security],
                      ["liquidity", ov.golden.scores.liquidity],
                      ["whale", ov.golden.scores.whale],
                      ["social", ov.golden.scores.social],
                      ["narrative", ov.golden.scores.narrative],
                      ["evidence", ov.golden.scores.evidence],
                      ["confidence", ov.golden.scores.confidence],
                    ] as const).map(([k, v]) => ({ label: dict.scores[k], value: v }))}
                  />
                  <div className="text-center">
                    <ScoreRing value={ov.golden.scores.confidence} size={130} tone="gold" label={dict.scores.confidence} />
                    <div className="mt-3 text-[10px] text-mist">
                      {dict.golden.since}: {timeAgo(loc, ov.golden.decision.createdAt)}
                    </div>
                  </div>
                </div>
              </Panel>
            </Reveal>
            <Reveal delay={160}>
              <Panel hover={false} className="h-full">
                <h3 className="flex items-center gap-2 text-base font-extrabold text-frost">
                  <Sparkles className="size-4 text-gild-300" />
                  {dict.golden.whyTitle}
                </h3>
                <ul className="mt-5 space-y-3.5">
                  {(fa ? ov.golden.decision.whyFa : ov.golden.decision.whyEn).map((w, i) => (
                    <li key={i} className="flex gap-3 text-[13px] leading-6 text-frost/85">
                      <span className="num mt-0.5 grid size-5 shrink-0 place-items-center rounded-md bg-gild-400/15 text-[10px] font-bold text-gild-300">
                        {fmtInt(loc, i + 1)}
                      </span>
                      {w}
                    </li>
                  ))}
                </ul>
                <div className="mt-6 flex flex-wrap gap-2">
                  <Badge label={dict.identity[ov.golden.token.identityStatus]} tone={IDENTITY_TONE[ov.golden.token.identityStatus]} />
                  <Badge label={`${dict.dossier.gates.security}: ${gateDict[ov.golden.token.securityGate]}`} tone="jade" />
                </div>
              </Panel>
            </Reveal>
          </div>
        </section>
      ) : null}

      {/* ============================ council strip ============================ */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <Reveal>
          <SectionHead
            kicker={dict.council.kicker}
            title={<span className="text-grad-ice">{dict.council.title}</span>}
            sub={dict.council.sub}
            href={`/${loc}/council`}
            action={dict.hero.ctaSecondary}
            tone="sky"
          />
        </Reveal>
        <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {ov.teams.map((t, i) => {
            const stance = ov.session?.opinions.find((o) => o.teamId === t.teamId)?.stance as Stance | undefined;
            return (
              <Reveal key={t.teamId} delay={i * 60} className="w-56 shrink-0 snap-start">
                <TeamCard team={t} locale={loc} dict={dict} stance={stance ?? null} compact />
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* ============================ wise tree preview ============================ */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <Reveal>
          <SectionHead
            kicker={dict.tree.kicker}
            title={<span className="text-grad-jade">{dict.tree.title}</span>}
            sub={dict.tree.sub}
            href={`/${loc}/wise-tree`}
            action={`${dict.tree.growth} ←`}
          />
        </Reveal>
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Reveal delay={80}>
            <Panel hover={false} className="overflow-hidden !p-2">
              <TreeCanvas vitals={ov.vitals} />
            </Panel>
          </Reveal>
          <Reveal delay={160}>
            <div className="flex h-full flex-col gap-3">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { v: ov.vitals.healthyRoots, l: dict.tree.legend.roots.split("—")[0], c: "text-jade-300" },
                  { v: ov.vitals.leaves, l: dict.tree.legend.leaves.split("—")[0], c: "text-jade-200" },
                  { v: ov.vitals.rocks, l: dict.tree.legend.rocks.split("—")[0], c: "text-flare" },
                ].map((s) => (
                  <div key={s.l} className="glass-soft rounded-2xl px-3 py-3 text-center">
                    <Counter locale={loc} value={s.v} className={cx("num block text-2xl font-black", s.c)} />
                    <span className="mt-1 block text-[10px] leading-4 text-mist">{s.l}</span>
                  </div>
                ))}
              </div>
              <Panel hover={false} className="grow !p-5">
                <h4 className="text-[12px] font-bold text-mist">{dict.tree.growth}</h4>
                <ul className="mt-3 space-y-3">
                  {ov.events.slice(0, 4).map((e) => (
                    <li key={e.id} className="flex gap-3 text-[12px] leading-5">
                      <span
                        className={cx(
                          "mt-1.5 size-2 shrink-0 rounded-full",
                          e.kind === "ROCK" ? "bg-flare" : e.kind === "GOLDEN_FRUIT" ? "bg-gild-400 a-pulse-soft" : "bg-jade-400",
                        )}
                      />
                      <div>
                        <span className="font-semibold text-frost/90">{fa ? e.titleFa : e.titleEn}</span>
                        <span className="ms-2 text-[10px] text-mist/70">{timeAgo(loc, e.createdAt)}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </Panel>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ============================ alerts ============================ */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <Reveal>
          <SectionHead
            kicker={dict.alerts.kicker}
            tone="rose"
            title={<span>{dict.alerts.title}</span>}
            sub={dict.alerts.sub}
          />
        </Reveal>
        <Reveal delay={100}>
          <Panel hover={false} className="divide-y divide-white/5 !p-0">
            {ov.alerts.slice(0, 6).map((a: AlertRow) => {
              const Icon = ALERT_ICON[a.type] ?? ScrollText;
              const tone = SEV_TONE[a.severity] ?? "zinc";
              return (
                <div key={a.id} className="flex items-start gap-4 px-6 py-4 transition-colors hover:bg-white/[0.02]">
                  <span
                    className={cx(
                      "mt-0.5 grid size-9 shrink-0 place-items-center rounded-xl border",
                      TONE[tone].bg, TONE[tone].border,
                    )}
                  >
                    <Icon className={cx("size-4", TONE[tone].text)} />
                  </span>
                  <div className="grow">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[13px] font-bold text-frost">{fa ? a.titleFa : a.titleEn}</span>
                      <Badge label={dict.alerts.types[a.type as keyof Dict["alerts"]["types"]] ?? a.type} tone={tone} />
                    </div>
                    <p className="mt-1 text-[12px] leading-5 text-mist">{fa ? a.bodyFa : a.bodyEn}</p>
                  </div>
                  <span className="shrink-0 text-[10px] text-mist/70">{timeAgo(loc, a.createdAt)}</span>
                </div>
              );
            })}
          </Panel>
        </Reveal>
        <Reveal delay={160}>
          <p className="mt-3 text-center text-[10.5px] text-mist/70">{dict.alerts.sourceNote}</p>
        </Reveal>
      </section>

      {/* ============================ providers + learning ============================ */}
      <section className="mx-auto grid max-w-7xl gap-6 px-5 py-16 lg:grid-cols-2">
        <div>
          <Reveal>
            <SectionHead
              kicker={dict.providers.kicker}
              tone="cyan"
              title={dict.providers.title}
              sub={dict.providers.sub}
            />
          </Reveal>
          <div className="grid gap-3 sm:grid-cols-2">
            {ov.providers.map((p, i) => (
              <Reveal key={p.id} delay={i * 50}>
                <div className="glass-soft rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[12.5px] font-bold text-frost">{p.name}</span>
                    <Badge label={dict.providers.status[p.status]} tone={PROVIDER_TONE[p.status]} pulse={p.status === "BLOCKED"} />
                  </div>
                  <div className="mt-1 text-[10px] text-mist">{p.kind}</div>
                  <div className="mt-3 flex items-center justify-between text-[10.5px] text-mist">
                    <span>{dict.providers.latency}: <span className="num text-frost/80">{p.latencyMs > 0 ? `${fmtInt(loc, p.latencyMs)}ms` : "—"}</span></span>
                    <span className="num text-frost/80">{fmtInt(loc, Math.round(p.reliability * 100))}٪</span>
                  </div>
                  <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="bar-grow h-full rounded-full"
                      style={{
                        width: `${p.reliability * 100}%`,
                        background: p.status === "OK" ? "linear-gradient(90deg,#10b98166,#34d399)" : p.status === "BLOCKED" ? "linear-gradient(90deg,#fb718566,#fb7185)" : "linear-gradient(90deg,#fbbf2466,#fbbf24)",
                      }}
                    />
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
        <div>
          <Reveal>
            <SectionHead
              kicker={dict.learning.kicker}
              tone="violet"
              title={dict.learning.title}
              sub={dict.learning.sub}
            />
          </Reveal>
          <div className="space-y-3">
            {ov.patterns.map((p, i) => (
              <Reveal key={p.id} delay={i * 60}>
                <div className={cx(
                  "glass-soft rounded-2xl border-s-2 p-5",
                  p.kind === "POSITIVE" ? "border-s-jade-400" : "border-s-flare",
                )}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[13px] font-extrabold text-frost">{fa ? p.titleFa : p.titleEn}</span>
                    <Badge
                      label={p.kind === "POSITIVE" ? dict.learning.positive : dict.learning.failure}
                      tone={p.kind === "POSITIVE" ? "jade" : "rose"}
                    />
                  </div>
                  <p className="mt-2 text-[12px] leading-6 text-mist">{fa ? p.descFa : p.descEn}</p>
                  {p.metricFa ? (
                    <span className="mt-3 inline-block rounded-lg bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-frost/70">
                      {fa ? p.metricFa : p.metricEn}
                    </span>
                  ) : null}
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
