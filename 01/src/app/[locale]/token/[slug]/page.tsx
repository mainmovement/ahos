import Link from "next/link";
import { notFound } from "next/navigation";
import {
  AlertTriangle, ArrowRight, Ban, CheckCircle2, ClipboardList, Eye,
  FileText, Landmark, MessagesSquare, ShieldCheck,
} from "lucide-react";
import { getDossier, type Stance } from "@/lib/engine";
import { getDict, isLocale, type Locale } from "@/lib/dict";
import { fmtDate, fmtInt, fmtPct, fmtUsd, shortAddress, timeAgo } from "@/lib/format";
import Reveal from "@/components/reveal";
import { Radar, ScoreRing, Sparkline } from "@/components/charts";
import { Badge, Kicker, Monogram, Panel, ScoreBar } from "@/components/primitives";
import { DisagreementMeter, TeamAvatar } from "@/components/team";
import {
  CHAIN_LABEL, DECISION_TONE, IDENTITY_TONE, GATE_TONE, STANCE_TONE, TONE,
  cx, scoreTone, type Tone,
} from "@/lib/ui";

export const dynamic = "force-dynamic";

function gateValTone(v: string): Tone {
  if (v === "PASS") return "jade";
  if (v === "WARN" || v === "INCOMPLETE") return "amber";
  return "rose";
}

export default async function DossierPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDict(locale);
  const fa = locale === "fa";
  const d = await getDossier(slug);
  if (!d) notFound();

  const { token: t, scores: s, decision, opinions, evidence, trades, teams } = d;
  const gateDict = dict.gate as Record<string, string>;
  const strong = decision?.kind === "STRONG_CANDIDATE";

  const stats: { l: string; v: string }[] = [
    { l: dict.dossier.mcap, v: fmtUsd(locale, t.marketCap) },
    { l: dict.dossier.liq, v: t.liquidityUsd > 0 ? fmtUsd(locale, t.liquidityUsd) : dict.common.unknown },
    { l: dict.dossier.vol, v: fmtUsd(locale, t.volume24h) },
    { l: dict.dossier.launch, v: t.launchAt ? fmtDate(locale, t.launchAt) : dict.common.unknown },
  ];

  return (
    <div className="mx-auto max-w-7xl px-5 pb-10">
      {/* back */}
      <div className="pt-10">
        <Link
          href={`/${locale}/opportunities`}
          className="inline-flex items-center gap-2 text-[12px] font-semibold text-mist transition hover:text-jade-300"
        >
          <ArrowRight className="size-3.5 ltr:rotate-180" />
          {dict.dossier.back}
        </Link>
      </div>

      {/* ---------- header ---------- */}
      <header className="mt-6">
        <Reveal>
          <div className={cx("glass relative overflow-hidden rounded-[2rem] p-7", strong && "gold-hair a-glow-gold")}>
            <div className="pointer-events-none absolute -top-24 end-8 hidden select-none text-[10rem] font-black leading-none text-white/[0.03] lg:block">
              {t.symbol}
            </div>
            <div className="relative flex flex-wrap items-center gap-6">
              <Monogram symbol={t.symbol} seed={t.slug} size={72} />
              <div className="min-w-0 grow">
                <div className="flex flex-wrap items-center gap-3">
                  <Kicker tone="gold">{dict.dossier.kicker}</Kicker>
                  {decision ? (
                    <Badge label={dict.decision[decision.kind]} tone={DECISION_TONE[decision.kind]} pulse={strong} />
                  ) : null}
                </div>
                <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">
                  {fa ? t.nameFa : t.name}{" "}
                  <span className="num text-grad-gold">{t.symbol}</span>
                </h1>
                <p className="mt-2 max-w-2xl text-[13px] leading-6 text-mist">
                  {fa ? t.summaryFa : t.summaryEn}
                </p>
                <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px]">
                  <Badge label={dict.identity[t.identityStatus]} tone={IDENTITY_TONE[t.identityStatus]} />
                  <Badge label={`${dict.dossier.gates.security}: ${dict.gate[t.securityGate]}`} tone={GATE_TONE[t.securityGate]} />
                  <span className="rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1 text-mist">
                    {dict.dossier.chain}: <span className="font-bold text-frost/85">{CHAIN_LABEL[t.chain]}</span>
                  </span>
                  <span className="num rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1 text-mist" dir="ltr" title={t.address}>
                    {dict.dossier.contract}: <span className="text-frost/85">{shortAddress(t.address)}</span>
                  </span>
                </div>
                {t.monitoringOnly ? (
                  <p className="mt-3 flex w-fit items-center gap-1.5 rounded-lg bg-amber-400/10 px-3 py-1.5 text-[11px] font-semibold text-amber-300">
                    <Eye className="size-3.5" />
                    {dict.opp.tokenOnly}
                  </p>
                ) : null}
              </div>
              <div className="hidden shrink-0 flex-col items-center gap-2 sm:flex">
                <Sparkline data={t.sparkline} w={170} h={54} />
                <div className="flex items-baseline gap-2">
                  <span className="num text-xl font-black text-frost">{fmtUsd(locale, t.priceUsd)}</span>
                  <span className={cx("num text-[12px] font-bold", t.change24h >= 0 ? "text-jade-300" : "text-flare")}>
                    {fmtPct(locale, t.change24h)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </header>

      {/* ---------- stats ---------- */}
      <Reveal delay={80}>
        <div className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {stats.map((x) => (
            <div key={x.l} className="glass-soft rounded-2xl px-5 py-4">
              <div className="text-[10.5px] text-mist">{x.l}</div>
              <div className="num mt-1 text-lg font-black text-frost">{x.v}</div>
            </div>
          ))}
        </div>
      </Reveal>

      {/* ---------- gates + decision ---------- */}
      {decision ? (
        <div className="mt-6 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <Reveal delay={100}>
            <Panel hover={false} className="h-full">
              <h3 className="flex items-center gap-2 text-base font-extrabold text-frost">
                <ShieldCheck className="size-4 text-jade-300" />
                {dict.dossier.sections.gates}
              </h3>
              <div className="mt-6 space-y-0">
                {(Object.entries(decision.gateSnapshot) as [string, string][]).map(([k, v], i, arr) => (
                  <div key={k} className="relative flex items-center gap-4 pb-5 last:pb-0">
                    {i < arr.length - 1 ? (
                      <span className="absolute start-[13px] top-7 h-full w-px bg-white/8" />
                    ) : null}
                    <span className={cx("relative z-10 grid size-7 shrink-0 place-items-center rounded-full border", TONE[gateValTone(v)].bg, TONE[gateValTone(v)].border)}>
                      <span className={cx("size-2 rounded-full", TONE[gateValTone(v)].dot, v === "PASS" && "a-pulse-soft")} />
                    </span>
                    <div className="flex grow items-center justify-between rounded-xl bg-white/[0.03] px-4 py-2.5">
                      <span className="text-[12.5px] font-bold text-frost/90">
                        {(dict.dossier.gates as Record<string, string>)[k] ?? k}
                      </span>
                      <span className={cx("text-[11px] font-extrabold", TONE[gateValTone(v)].text)}>
                        {gateDict[v] ?? v}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex items-center justify-between rounded-xl border border-white/8 bg-abyss-900/60 px-4 py-3 text-[11px] text-mist">
                <span>{dict.dossier.policy}</span>
                <span className="num font-bold text-frost/80">{decision.policyVersion}</span>
              </div>
            </Panel>
          </Reveal>
          <Reveal delay={160}>
            <Panel
              hover={false}
              className={cx(
                "flex h-full flex-col justify-between",
                decision.kind === "REJECT" && "!border-flare/30",
                strong && "gold-hair",
              )}
            >
              <div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <Badge label={dict.decision[decision.kind]} tone={DECISION_TONE[decision.kind]} pulse={strong || decision.kind === "REJECT"} className="!px-3.5 !py-1.5 !text-[12px]" />
                  <ScoreRing value={decision.confidence} size={92} stroke={7} tone={scoreTone(decision.confidence)} label={dict.scores.confidence} />
                </div>
                <div className="mt-6 grid grid-cols-2 gap-3">
                  {(fa ? decision.risksFa : decision.risksEn).slice(0, 4).map((r, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-xl bg-flare/[0.06] px-3 py-2.5 text-[11.5px] leading-5 text-frost/80">
                      <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-flare/80" />
                      {r}
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-5 flex items-center justify-between border-t border-white/5 pt-4 text-[10.5px] text-mist">
                <span>{dict.alerts.sourceNote}</span>
                <span>{timeAgo(locale, decision.createdAt)}</span>
              </div>
            </Panel>
          </Reveal>
        </div>
      ) : null}

      {/* ---------- scores ---------- */}
      {s ? (
        <section className="mt-14">
          <Reveal>
            <h2 className="text-2xl font-black"><span className="text-grad-jade">{dict.dossier.sections.scores}</span></h2>
          </Reveal>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Reveal delay={80}>
              <Panel hover={false} className="grid h-full place-items-center">
                <Radar
                  size={300}
                  axes={([
                    ["opportunity", s.opportunity], ["security", s.security], ["liquidity", s.liquidity],
                    ["whale", s.whale], ["social", s.social], ["narrative", s.narrative],
                    ["evidence", s.evidence], ["confidence", s.confidence],
                  ] as const).map(([k, v]) => ({ label: dict.scores[k], value: v }))}
                />
              </Panel>
            </Reveal>
            <Reveal delay={140}>
              <Panel hover={false} className="flex h-full flex-col justify-center gap-3.5">
                {([
                  ["opportunity", s.opportunity], ["security", s.security], ["liquidity", s.liquidity],
                  ["whale", s.whale], ["social", s.social], ["narrative", s.narrative],
                  ["evidence", s.evidence], ["confidence", s.confidence],
                ] as const).map(([k, v], i) => (
                  <ScoreBar key={k} label={dict.scores[k]} value={v} toneHex={TONE[scoreTone(v)].hex} delay={i * 70} />
                ))}
              </Panel>
            </Reveal>
          </div>
        </section>
      ) : null}

      {/* ---------- why / risks / reject ---------- */}
      {decision ? (
        <section className="mt-14 grid gap-6 lg:grid-cols-3">
          {[
            { title: dict.dossier.sections.why, items: fa ? decision.whyFa : decision.whyEn, icon: CheckCircle2, tone: "jade" as Tone },
            { title: dict.dossier.sections.risks, items: fa ? decision.risksFa : decision.risksEn, icon: AlertTriangle, tone: "amber" as Tone },
            { title: dict.dossier.sections.reject, items: fa ? decision.rejectFa : decision.rejectEn, icon: Ban, tone: "rose" as Tone },
          ].map((sec, si) => (
            <Reveal key={sec.title} delay={si * 90}>
              <Panel hover={false} className="h-full">
                <h3 className={cx("flex items-center gap-2 text-base font-extrabold", TONE[sec.tone].text)}>
                  <sec.icon className="size-4" />
                  {sec.title}
                </h3>
                <ul className="mt-5 space-y-3">
                  {sec.items.map((it, i) => (
                    <li key={i} className="flex gap-2.5 text-[12.5px] leading-6 text-frost/85">
                      <span className={cx("num mt-1 text-[10px] font-bold", TONE[sec.tone].text)}>{fmtInt(locale, i + 1)}</span>
                      {it}
                    </li>
                  ))}
                </ul>
              </Panel>
            </Reveal>
          ))}
        </section>
      ) : null}

      {/* ---------- scenarios ---------- */}
      {decision ? (
        <section className="mt-14">
          <Reveal>
            <h2 className="text-2xl font-black"><span className="text-grad-ice">{dict.dossier.sections.scenarios}</span></h2>
          </Reveal>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {decision.scenarios.map((sc, i) => {
              const tone: Tone = sc.key === "bull" ? "jade" : sc.key === "base" ? "sky" : sc.key === "bear" ? "amber" : "rose";
              return (
                <Reveal key={sc.key} delay={i * 70}>
                  <div className={cx("glass h-full rounded-3xl border p-5", TONE[tone].border)}>
                    <div className="flex items-center justify-between">
                      <span className={cx("text-[12px] font-extrabold", TONE[tone].text)}>
                        {dict.dossier.scenarioKeys[sc.key]}
                      </span>
                      <span className="num text-lg font-black text-frost">{fmtInt(locale, sc.prob)}٪</span>
                    </div>
                    <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5">
                      <div className="bar-grow h-full rounded-full" style={{ width: `${sc.prob}%`, background: TONE[tone].hex }} />
                    </div>
                    <p className="mt-3 text-[11.5px] leading-5 text-mist">{fa ? sc.fa : sc.en}</p>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </section>
      ) : null}

      {/* ---------- evidence ledger ---------- */}
      <section className="mt-14">
        <Reveal>
          <h2 className="flex items-center gap-2 text-2xl font-black">
            <ClipboardList className="size-5 text-jade-300" />
            <span className="text-grad-jade">{dict.dossier.sections.evidenceLedger}</span>
          </h2>
        </Reveal>
        <div className="mt-6 space-y-3">
          {evidence.map((e, i) => {
            const tone: Tone = e.status === "VERIFIED" ? "jade" : e.status === "CONFLICTED" ? "rose" : e.status === "STALE" ? "zinc" : "amber";
            return (
              <Reveal key={e.id} delay={Math.min(i, 5) * 50}>
                <div className="glass-soft flex flex-wrap items-start gap-4 rounded-2xl p-5">
                  <span className={cx("mt-1 grid size-8 shrink-0 place-items-center rounded-xl border", TONE[tone].bg, TONE[tone].border)}>
                    <FileText className={cx("size-3.5", TONE[tone].text)} />
                  </span>
                  <div className="min-w-0 grow">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge label={dict.dossier.evKind[e.kind as keyof typeof dict.dossier.evKind] ?? e.kind} tone="sky" />
                      <Badge label={dict.dossier.evStatus[e.status as keyof typeof dict.dossier.evStatus] ?? e.status} tone={tone} />
                      <span className="text-[10px] text-mist/70">{timeAgo(locale, e.observedAt)}</span>
                    </div>
                    <p className="mt-2 text-[12.5px] leading-6 text-frost/85">{fa ? e.contentFa : e.contentEn}</p>
                    <p className="mt-1.5 text-[10.5px] text-mist/80">
                      {dict.common.source}: <span className="text-frost/70">{e.source}</span>
                    </p>
                  </div>
                  <div className="shrink-0 text-center">
                    <div className="num text-lg font-black text-frost/90">{e.confidence}</div>
                    <div className="text-[9px] text-mist">{dict.common.confidenceWord}</div>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* ---------- council debate ---------- */}
      {opinions.length > 0 ? (
        <section className="mt-14">
          <Reveal>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h2 className="flex items-center gap-2 text-2xl font-black">
                <MessagesSquare className="size-5 text-ice" />
                <span className="text-grad-ice">{dict.dossier.sections.councilDebate}</span>
              </h2>
              <DisagreementMeter value={d.disagreement} label={dict.council.disagreement} locale={locale} />
            </div>
          </Reveal>
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {opinions.map((o, i) => {
              const team = teams.find((x) => x.teamId === o.teamId);
              if (!team) return null;
              return (
                <Reveal key={o.id} delay={Math.min(i, 6) * 50}>
                  <div className="glass-soft flex h-full flex-col gap-3 rounded-2xl p-5">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <TeamAvatar team={team} size={38} />
                        <div>
                          <div className="text-[12.5px] font-extrabold text-frost">{fa ? team.nameFa : team.nameEn}</div>
                          <div className="text-[10px] text-mist">{fa ? team.personaFa : team.personaEn}</div>
                        </div>
                      </div>
                      <Badge label={dict.stance[o.stance as Stance]} tone={STANCE_TONE[o.stance]} pulse={o.stance === "ALARM"} />
                    </div>
                    <p className="text-[12px] leading-6 text-frost/80">{fa ? o.summaryFa : o.summaryEn}</p>
                    <div className="mt-auto flex items-center gap-2">
                      <div className="h-1 grow overflow-hidden rounded-full bg-white/5">
                        <div className="bar-grow h-full rounded-full" style={{ width: `${o.confidence}%`, background: team.color }} />
                      </div>
                      <span className="num text-[10px] font-bold text-mist">{o.confidence}</span>
                    </div>
                  </div>
                </Reveal>
              );
            })}
          </div>
          <Reveal delay={120}>
            <p className="mt-5 text-center text-[11px] text-mist/80">{dict.council.finalWord}</p>
          </Reveal>
        </section>
      ) : null}

      {/* ---------- paper exposure ---------- */}
      {trades.length > 0 ? (
        <section className="mt-14">
          <Reveal>
            <h2 className="flex items-center gap-2 text-2xl font-black">
              <Landmark className="size-5 text-vio" />
              <span className="text-grad-ice">{dict.dossier.sections.paper}</span>
            </h2>
          </Reveal>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {trades.map((pt) => {
              const open = pt.status === "OPEN";
              const running = open && pt.currentPrice ? ((pt.currentPrice - pt.entry) / pt.entry) * 100 : pt.pnlPct ?? 0;
              const tone: Tone = open ? "sky" : pt.result === "WIN" ? "jade" : pt.result === "LOSS" ? "rose" : "zinc";
              return (
                <Reveal key={pt.id}>
                  <Panel hover={false}>
                    <div className="flex items-center justify-between">
                      <Badge
                        label={open ? dict.paper.open : dict.paper.result[pt.result ?? "TIMEOUT"]}
                        tone={tone}
                        pulse={open}
                      />
                      <span className={cx("num text-xl font-black", running >= 0 ? "text-jade-300" : "text-flare")}>
                        {fmtPct(locale, running)}
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                      {[
                        { l: dict.paper.pos.entry, v: fmtUsd(locale, pt.entry) },
                        { l: open ? dict.paper.pos.current : dict.paper.pos.exit, v: fmtUsd(locale, (open ? pt.currentPrice : pt.exitPrice) ?? 0) },
                        { l: dict.paper.pos.stop, v: fmtUsd(locale, pt.stop) },
                      ].map((x) => (
                        <div key={x.l} className="rounded-xl bg-white/[0.03] px-2 py-2.5">
                          <div className="text-[9.5px] text-mist">{x.l}</div>
                          <div className="num mt-0.5 text-[12px] font-bold text-frost/90">{x.v}</div>
                        </div>
                      ))}
                    </div>
                    {!open && pt.postmortemFa ? (
                      <p className="mt-4 rounded-xl bg-white/[0.03] p-3.5 text-[11.5px] leading-6 text-mist">
                        <span className="mb-1 block font-bold text-frost/80">{dict.paper.postmortem}</span>
                        {fa ? pt.postmortemFa : pt.postmortemEn}
                      </p>
                    ) : null}
                  </Panel>
                </Reveal>
              );
            })}
          </div>
        </section>
      ) : null}

      <p className="mt-14 border-t border-white/5 pt-6 text-center text-[10.5px] text-mist/70">
        {dict.dossier.proofNote}
      </p>
    </div>
  );
}
