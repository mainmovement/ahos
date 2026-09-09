import Link from "next/link";
import { notFound } from "next/navigation";
import { ShieldAlert } from "lucide-react";
import { getCouncilView } from "@/lib/engine";
import { getDict, isLocale } from "@/lib/dict";
import { fmtInt, timeAgo } from "@/lib/format";
import Reveal from "@/components/reveal";
import { Badge, Kicker, Monogram, Panel } from "@/components/primitives";
import { DisagreementMeter, TeamAvatar, TeamCard } from "@/components/team";
import { DECISION_TONE, STANCE_TONE, cx } from "@/lib/ui";

export const dynamic = "force-dynamic";

export default async function CouncilPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDict(locale);
  const fa = locale === "fa";
  const { teams, sessions } = await getCouncilView();

  return (
    <div className="mx-auto max-w-7xl px-5 pb-10">
      <header className="py-12 text-center">
        <Reveal>
          <div className="flex justify-center">
            <Kicker tone="sky">{dict.council.kicker}</Kicker>
          </div>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-5xl">
            <span className="text-grad-ice">{dict.council.title}</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-mist">{dict.council.sub}</p>
        </Reveal>
        <Reveal delay={140}>
          <div className="mx-auto mt-6 flex w-fit items-center gap-2 rounded-full border border-flare/25 bg-flare/8 px-4 py-2 text-[11px] font-semibold text-flare">
            <ShieldAlert className="size-3.5" />
            {dict.council.redTeamNote}
          </div>
        </Reveal>
      </header>

      {/* team grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {teams.map((t, i) => {
          const stance = sessions[0]?.opinions.find((o) => o.teamId === t.teamId)?.stance ?? null;
          return (
            <Reveal key={t.teamId} delay={(i % 5) * 70}>
              <TeamCard team={t} locale={locale} dict={dict} stance={stance} />
            </Reveal>
          );
        })}
      </div>

      {/* sessions */}
      <section className="mt-16 space-y-8">
        <Reveal>
          <h2 className="text-2xl font-black">
            <span className="text-grad-ice">{dict.council.session}</span>
          </h2>
        </Reveal>
        {sessions.map((s, si) => (
          <Reveal key={s.decision.id} delay={si * 100}>
            <Panel hover={false} className={cx(si === 1 && "!border-flare/25", si === 0 && "gold-hair")}>
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 pb-5">
                <div className="flex items-center gap-4">
                  <Monogram symbol={s.token.symbol} seed={s.token.slug} size={46} />
                  <div>
                    <div className="text-[15px] font-black text-frost">
                      {dict.council.debateFor}: {fa ? s.token.nameFa : s.token.name}{" "}
                      <span className="num text-mist">{s.token.symbol}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-[10.5px] text-mist">
                      <Badge label={dict.decision[s.decision.kind]} tone={DECISION_TONE[s.decision.kind]} pulse={s.decision.kind === "STRONG_CANDIDATE"} />
                      <span className="num">{s.decision.policyVersion}</span>
                      <span>·</span>
                      <span>{timeAgo(locale, s.decision.createdAt)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <DisagreementMeter value={s.disagreement} label={dict.council.disagreement} locale={locale} />
                  <Link
                    href={`/${locale}/token/${s.token.slug}`}
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-[11px] font-bold text-frost/85 transition hover:border-jade-400/40 hover:text-jade-300"
                  >
                    {dict.council.viewToken}
                  </Link>
                </div>
              </div>
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {s.opinions.map((o) => {
                  const team = teams.find((x) => x.teamId === o.teamId);
                  if (!team) return null;
                  return (
                    <div key={o.id} className="glass-soft rounded-2xl p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <TeamAvatar team={team} size={32} />
                          <span className="text-[12px] font-bold text-frost">{fa ? team.nameFa : team.nameEn}</span>
                        </div>
                        <Badge label={dict.stance[o.stance]} tone={STANCE_TONE[o.stance]} pulse={o.stance === "ALARM"} />
                      </div>
                      <p className="mt-2.5 text-[11.5px] leading-5 text-mist">{fa ? o.summaryFa : o.summaryEn}</p>
                      <div className="mt-3 flex items-center gap-2">
                        <div className="h-1 grow overflow-hidden rounded-full bg-white/5">
                          <div className="bar-grow h-full rounded-full" style={{ width: `${o.confidence}%`, background: team.color }} />
                        </div>
                        <span className="num w-6 text-end text-[10px] font-bold text-mist">{fmtInt(locale, o.confidence)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Panel>
          </Reveal>
        ))}
      </section>

      <Reveal delay={120}>
        <p className="mt-10 text-center text-[12px] font-semibold text-gild-300/80">{dict.council.finalWord}</p>
      </Reveal>
    </div>
  );
}
