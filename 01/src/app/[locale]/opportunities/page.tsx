import Link from "next/link";
import { notFound } from "next/navigation";
import { Eye } from "lucide-react";
import { getOpportunities, type DecisionKind, type TokenCard } from "@/lib/engine";
import { getDict, isLocale, type Locale } from "@/lib/dict";
import { fmtPct, fmtUsd } from "@/lib/format";
import Reveal from "@/components/reveal";
import { ScoreRing, Sparkline } from "@/components/charts";
import { Badge, Kicker, Monogram, ScoreBar } from "@/components/primitives";
import {
  CHAIN_LABEL, DECISION_TONE, IDENTITY_TONE, GATE_TONE, TONE,
  cx, scoreTone,
} from "@/lib/ui";

export const dynamic = "force-dynamic";

const KINDS: (DecisionKind | "all")[] = ["all", "STRONG_CANDIDATE", "CANDIDATE", "MONITOR", "SKIP", "REJECT"];

function Card({ card, rank, locale, dict }: { card: TokenCard; rank: number; locale: Locale; dict: ReturnType<typeof getDict> }) {
  const fa = locale === "fa";
  const t = card.token;
  const d = card.decision;
  const s = card.scores;
  const strong = d?.kind === "STRONG_CANDIDATE";
  return (
    <Link href={`/${locale}/token/${t.slug}`} className="group block">
      <div
        className={cx(
          "glass relative h-full rounded-3xl p-5 panel-hover",
          strong && "gold-hair a-glow-gold",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3.5">
            <span className={cx("num w-7 text-2xl font-black", strong ? "text-gild-400/80" : "text-white/15")}>
              {rank}
            </span>
            <Monogram symbol={t.symbol} seed={t.slug} size={50} />
            <div>
              <div className="text-[15px] font-black text-frost transition group-hover:text-gild-300">
                {fa ? t.nameFa : t.name}
              </div>
              <div className="mt-0.5 flex items-center gap-1.5 text-[10.5px] text-mist">
                <span className="num font-bold">{t.symbol}</span>
                <span>·</span>
                <span>{CHAIN_LABEL[t.chain]}</span>
              </div>
            </div>
          </div>
          {s ? (
            <ScoreRing value={s.opportunity} size={76} stroke={6} tone={strong ? "gold" : scoreTone(s.opportunity)} />
          ) : null}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          {d ? (
            <Badge label={dict.decision[d.kind]} tone={DECISION_TONE[d.kind]} pulse={strong} />
          ) : (
            <Badge label={dict.opp.noDecision} tone="zinc" />
          )}
          <Badge label={dict.identity[t.identityStatus]} tone={IDENTITY_TONE[t.identityStatus]} />
          <Badge
            label={`${dict.dossier.gates.security}: ${dict.gate[t.securityGate]}`}
            tone={GATE_TONE[t.securityGate]}
          />
        </div>

        {t.monitoringOnly ? (
          <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-amber-400/8 px-2.5 py-1.5 text-[10.5px] text-amber-300/90">
            <Eye className="size-3" />
            {dict.opp.tokenOnly}
          </p>
        ) : null}

        {s ? (
          <div className="mt-4 space-y-2">
            <ScoreBar label={dict.scores.security} value={s.security} toneHex={TONE[scoreTone(s.security)].hex} delay={0} />
            <ScoreBar label={dict.scores.liquidity} value={s.liquidity} toneHex={TONE[scoreTone(s.liquidity)].hex} delay={60} />
            <ScoreBar label={dict.scores.social} value={s.social} toneHex={TONE[scoreTone(s.social)].hex} delay={120} />
            <ScoreBar label={dict.scores.evidence} value={s.evidence} toneHex={TONE[scoreTone(s.evidence)].hex} delay={180} />
          </div>
        ) : null}

        <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-4">
          <div>
            <div className="num text-[13px] font-bold text-frost">{fmtUsd(locale, t.priceUsd)}</div>
            <div className={cx("num mt-0.5 text-[11px] font-semibold", t.change24h >= 0 ? "text-jade-300" : "text-flare")}>
              {fmtPct(locale, t.change24h)}
            </div>
          </div>
          <Sparkline data={t.sparkline} w={120} h={36} />
        </div>
      </div>
    </Link>
  );
}

export default async function OpportunitiesPage({
  params, searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ kind?: string }>;
}) {
  const { locale } = await params;
  const { kind } = await searchParams;
  if (!isLocale(locale)) notFound();
  const dict = getDict(locale);
  const cards = await getOpportunities();
  const filter: (DecisionKind | "all") = KINDS.includes(kind as DecisionKind | "all") ? (kind as DecisionKind | "all") : "all";
  const shown = filter === "all" ? cards : cards.filter((c) => c.decision?.kind === filter);

  return (
    <div className="mx-auto max-w-7xl px-5 pb-10">
      <header className="py-12">
        <Reveal>
          <Kicker tone="gold">{dict.opp.kicker}</Kicker>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">
            <span className="text-grad-gold">{dict.opp.title}</span>
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-mist">{dict.opp.sub}</p>
        </Reveal>
        <Reveal delay={120}>
          <div className="mt-8 flex flex-wrap gap-2">
            {KINDS.map((k) => {
              const active = filter === k;
              const tone = k === "all" ? "jade" : DECISION_TONE[k];
              return (
                <Link
                  key={k}
                  href={k === "all" ? `/${locale}/opportunities` : `/${locale}/opportunities?kind=${k}`}
                  className={cx(
                    "rounded-full border px-4 py-2 text-[12px] font-bold transition-all",
                    active
                      ? `${TONE[tone].border} ${TONE[tone].bg} ${TONE[tone].text} shadow-[0_0_20px_-8px_currentColor]`
                      : "border-white/10 bg-white/[0.03] text-mist hover:border-white/20 hover:text-frost",
                  )}
                >
                  {k === "all" ? dict.opp.filters.all : dict.opp.filters[k]}
                </Link>
              );
            })}
          </div>
        </Reveal>
      </header>

      {shown.length === 0 ? (
        <p className="py-20 text-center text-mist">{dict.opp.empty}</p>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {shown.map((c, i) => (
            <Reveal key={c.token.id} delay={(i % 3) * 90}>
              <Card card={c} rank={i + 1} locale={locale} dict={dict} />
            </Reveal>
          ))}
        </div>
      )}

      <p className="mt-10 text-center text-[10.5px] text-mist/70">
        {dict.opp.subScoreLegend} · {dict.common.demo}
      </p>
    </div>
  );
}
