import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronDown, Target } from "lucide-react";
import { getPaperView } from "@/lib/engine";
import { getDict, isLocale, type Locale } from "@/lib/dict";
import { fmtInt, fmtPct, fmtUsd, timeAgo } from "@/lib/format";
import Reveal from "@/components/reveal";
import { EquityChart } from "@/components/charts";
import { Badge, Kicker, Monogram, Panel } from "@/components/primitives";
import { cx, TONE, type Tone } from "@/lib/ui";

export const dynamic = "force-dynamic";

export default async function PaperPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const loc: Locale = locale;
  const dict = getDict(loc);
  const fa = loc === "fa";
  const { open, closed, stats, equity, patterns } = await getPaperView();

  const statCards: { l: string; v: string; tone: Tone }[] = [
    { l: dict.paper.stats.winRate, v: stats.winRate !== null ? fmtPct(loc, stats.winRate, false) : "—", tone: "jade" },
    { l: dict.paper.stats.avgWin, v: stats.avgWin !== null ? fmtPct(loc, stats.avgWin) : "—", tone: "jade" },
    { l: dict.paper.stats.avgLoss, v: stats.avgLoss !== null ? fmtPct(loc, stats.avgLoss) : "—", tone: "rose" },
    { l: dict.paper.stats.maxDrawdown, v: fmtPct(loc, -stats.maxDrawdown), tone: "amber" },
    { l: dict.paper.stats.expectancy, v: stats.expectancy !== null ? fmtPct(loc, stats.expectancy) : "—", tone: "sky" },
    { l: dict.paper.stats.totalPnl, v: fmtUsd(loc, stats.totalPnlUsd), tone: stats.totalPnlUsd >= 0 ? "jade" : "rose" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-5 pb-10">
      <header className="py-12">
        <Reveal>
          <Kicker tone="violet">{dict.paper.kicker}</Kicker>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">
            <span className="text-grad-ice">{dict.paper.title}</span>
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-mist">{dict.paper.sub}</p>
        </Reveal>
      </header>

      {/* stats */}
      <Reveal delay={60}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {statCards.map((c) => (
            <div key={c.l} className="glass-soft rounded-2xl px-4 py-4 text-center">
              <div className={cx("num text-xl font-black", TONE[c.tone].text)}>{c.v}</div>
              <div className="mt-1 text-[10px] leading-4 text-mist">{c.l}</div>
            </div>
          ))}
        </div>
      </Reveal>

      {/* equity */}
      <Reveal delay={100}>
        <Panel hover={false} className="mt-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-extrabold text-frost">{dict.paper.equity}</h2>
            <div className="flex items-center gap-2 text-[10.5px] text-mist">
              <Badge label={dict.paper.result.WIN} tone="jade" />
              <span className="num">{fmtInt(loc, stats.wins)}</span>
              <Badge label={dict.paper.result.LOSS} tone="rose" />
              <span className="num">{fmtInt(loc, stats.losses)}</span>
              <Badge label={dict.paper.result.TIMEOUT} tone="zinc" />
              <span className="num">{fmtInt(loc, stats.timeouts)}</span>
            </div>
          </div>
          <EquityChart points={equity} />
        </Panel>
      </Reveal>

      {/* open positions */}
      <section className="mt-14">
        <Reveal>
          <h2 className="text-2xl font-black"><span className="text-grad-jade">{dict.paper.open}</span></h2>
        </Reveal>
        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          {open.map(({ trade, token, runningPct }) => {
            const lo = trade.stop, hi = trade.target1;
            const spanAll = hi - lo || 1;
            const cur = trade.currentPrice ?? trade.entry;
            const posCur = Math.min(100, Math.max(0, ((cur - lo) / spanAll) * 100));
            const posEntry = ((trade.entry - lo) / spanAll) * 100;
            const up = runningPct >= 0;
            return (
              <Reveal key={trade.id}>
                <Panel hover={false}>
                  <div className="flex items-center justify-between gap-3">
                    <Link href={`/${loc}/token/${token.slug}`} className="flex items-center gap-3">
                      <Monogram symbol={token.symbol} seed={token.slug} size={40} />
                      <div>
                        <div className="text-[14px] font-extrabold text-frost">{fa ? token.nameFa : token.name}</div>
                        <div className="num text-[10px] text-mist">{token.symbol}</div>
                      </div>
                    </Link>
                    <span className={cx("num text-2xl font-black", up ? "text-jade-300" : "text-flare")}>
                      {fmtPct(loc, runningPct)}
                    </span>
                  </div>

                  {/* position track */}
                  <div className="mt-6">
                    <div className="relative h-2 rounded-full bg-white/5">
                      <div
                        className={cx("absolute inset-y-0 rounded-full", up ? "bg-gradient-to-r from-jade-500/40 to-jade-400/80" : "bg-gradient-to-r from-flare/40 to-flare/70")}
                        style={{ insetInlineStart: `${Math.min(posEntry, posCur)}%`, width: `${Math.abs(posCur - posEntry)}%` }}
                      />
                      {/* entry marker */}
                      <span className="absolute top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-frost/80 bg-abyss-900" style={{ insetInlineStart: `calc(${posEntry}% - 6px)` }} />
                      {/* current marker */}
                      <span
                        className={cx("absolute top-1/2 size-3.5 -translate-y-1/2 rounded-full a-pulse-soft", up ? "bg-jade-400" : "bg-flare")}
                        style={{ insetInlineStart: `calc(${posCur}% - 7px)`, boxShadow: `0 0 12px ${up ? "#34d399" : "#fb7185"}` }}
                      />
                    </div>
                    <div className="mt-2 flex justify-between text-[9.5px] text-mist">
                      <span>{dict.paper.pos.stop}: <span className="num text-flare/90">{fmtUsd(loc, lo)}</span></span>
                      <span className="text-frost/70">{dict.paper.pos.progress}</span>
                      <span>{dict.paper.pos.target}: <span className="num text-jade-300">{fmtUsd(loc, hi)}</span></span>
                    </div>
                  </div>

                  <div className="mt-5 grid grid-cols-4 gap-2 text-center">
                    {[
                      { l: dict.paper.pos.entry, v: fmtUsd(loc, trade.entry) },
                      { l: dict.paper.pos.current, v: fmtUsd(loc, cur) },
                      { l: dict.paper.pos.size, v: fmtUsd(loc, trade.sizeUsd) },
                      { l: dict.paper.pos.opened, v: timeAgo(loc, trade.openedAt) },
                    ].map((x) => (
                      <div key={x.l} className="rounded-xl bg-white/[0.03] px-2 py-2.5">
                        <div className="text-[9px] text-mist">{x.l}</div>
                        <div className="num mt-0.5 text-[11px] font-bold text-frost/90">{x.v}</div>
                      </div>
                    ))}
                  </div>
                </Panel>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* closed */}
      <section className="mt-14">
        <Reveal>
          <h2 className="text-2xl font-black"><span className="text-grad-ice">{dict.paper.closed}</span></h2>
        </Reveal>
        <Reveal delay={80}>
          <Panel hover={false} className="mt-6 divide-y divide-white/5 !p-0">
            {closed.map(({ trade, token }) => {
              const tone: Tone = trade.result === "WIN" ? "jade" : trade.result === "LOSS" ? "rose" : "zinc";
              const hasPM = Boolean(trade.postmortemFa);
              return (
                <details key={trade.id} className="group px-6 py-4 open:bg-white/[0.02]">
                  <summary className="flex cursor-pointer list-none flex-wrap items-center gap-4 [&::-webkit-details-marker]:hidden">
                    <Monogram symbol={token.symbol} seed={token.slug} size={38} />
                    <div className="min-w-0 grow">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[13px] font-bold text-frost">{fa ? token.nameFa : token.name}</span>
                        <Badge label={dict.paper.result[trade.result ?? "TIMEOUT"]} tone={tone} />
                      </div>
                      <div className="num mt-0.5 text-[10.5px] text-mist" dir="ltr">
                        {fmtUsd(loc, trade.entry)} → {fmtUsd(loc, trade.exitPrice ?? 0)}
                      </div>
                    </div>
                    <div className="text-end">
                      <div className={cx("num text-lg font-black", TONE[tone].text)}>{fmtPct(loc, trade.pnlPct ?? 0)}</div>
                      <div className="num text-[10px] text-mist">{fmtUsd(loc, trade.pnlUsd ?? 0)}</div>
                    </div>
                    <span className="hidden text-[10px] text-mist/70 sm:block">{trade.closedAt ? timeAgo(loc, trade.closedAt) : ""}</span>
                    <ChevronDown className="size-4 text-mist transition-transform group-open:rotate-180" />
                  </summary>
                  {hasPM ? (
                    <div className="mt-4 grid gap-3 border-t border-white/5 pt-4 lg:grid-cols-2">
                      <div className="rounded-xl bg-white/[0.03] p-4 text-[12px] leading-6 text-mist">
                        <span className="mb-1.5 block font-extrabold text-frost/85">{dict.paper.postmortem}</span>
                        {fa ? trade.postmortemFa : trade.postmortemEn}
                      </div>
                      {trade.lessonFa ? (
                        <div className={cx("rounded-xl border p-4 text-[12px] leading-6", TONE[tone].border, TONE[tone].bg)}>
                          <span className={cx("mb-1.5 block font-extrabold", TONE[tone].text)}>{dict.paper.lesson}</span>
                          <span className="text-frost/85">{fa ? trade.lessonFa : trade.lessonEn}</span>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </details>
              );
            })}
          </Panel>
        </Reveal>
      </section>

      {/* patterns */}
      <section className="mt-14">
        <Reveal>
          <h2 className="flex items-center gap-2 text-2xl font-black">
            <Target className="size-5 text-gild-300" />
            <span className="text-grad-gold">{dict.learning.title}</span>
          </h2>
        </Reveal>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {patterns.map((p, i) => {
            const tone: Tone = p.kind === "POSITIVE" ? "jade" : "rose";
            return (
              <Reveal key={p.id} delay={(i % 2) * 80}>
                <div className={cx("glass-soft h-full rounded-2xl border-s-2 p-5", tone === "jade" ? "border-s-jade-400" : "border-s-flare")}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[13px] font-extrabold text-frost">{fa ? p.titleFa : p.titleEn}</span>
                    <Badge label={p.kind === "POSITIVE" ? dict.learning.positive : dict.learning.failure} tone={tone} />
                  </div>
                  <p className="mt-2 text-[12px] leading-6 text-mist">{fa ? p.descFa : p.descEn}</p>
                  {p.metricFa ? (
                    <span className={cx("num mt-3 inline-block rounded-lg px-2.5 py-1 text-[10px] font-semibold", TONE[tone].bg, TONE[tone].text)}>
                      {fa ? p.metricFa : p.metricEn}
                    </span>
                  ) : null}
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      <p className="mt-12 text-center text-[10.5px] text-mist/70">{dict.footer.line}</p>
    </div>
  );
}
