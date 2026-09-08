import Link from "next/link";
import type { ReactNode } from "react";
import { notFound } from "next/navigation";
import { ScoreBar, ScoreRing } from "@/components/score-ring";
import { loadToken } from "@/lib/queries";
import { decisionLabel, groupLabel, pct, timeAgo, truncateAddr, usd } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TokenPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const data = await loadToken(slug);
  if (!data) notFound();
  const { token, score } = data;

  return (
    <div>
      <Link href="/tokens" className="kicker">
        ← Discovery
      </Link>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="kicker">{groupLabel(token.tokenGroup)} · {token.narrative}</p>
          <h1 className="font-display mt-2 text-5xl italic md:text-7xl">{token.name}</h1>
          <p className="font-mono text-sm text-[#f3d5a0]/70">
            {token.symbol} · {token.chain} · {truncateAddr(token.contract)}
          </p>
        </div>
        <span className={`badge ${score?.decision ?? token.status}`}>{decisionLabel(score?.decision ?? token.status)}</span>
      </div>

      <p className="mt-6 max-w-3xl text-lg text-[#efe6d6]/75">{token.summary}</p>

      <div className="mt-8 grid gap-3 md:grid-cols-4">
        {[
          ["Price", usd(token.priceUsd, 4)],
          ["Market cap", usd(token.marketCapUsd)],
          ["Liquidity", usd(token.liquidityUsd)],
          ["Volume", usd(token.volumeUsd)],
        ].map(([k, v]) => (
          <div key={k} className="panel rounded-2xl p-4">
            <div className="kicker">{k}</div>
            <div className="mt-1 font-mono text-xl">{v}</div>
          </div>
        ))}
      </div>

      {score && (
        <section className="panel mt-8 rounded-3xl p-6">
          <p className="kicker">Scores</p>
          <div className="mt-4 flex flex-wrap justify-between gap-4">
            <ScoreRing value={score.opportunity} label="Opportunity" />
            <ScoreRing value={score.security} label="Security" />
            <ScoreRing value={score.liquidity} label="Liquidity" />
            <ScoreRing value={score.social} label="Social" />
            <ScoreRing value={score.whale} label="Whale" />
            <ScoreRing value={score.narrative} label="Narrative" />
            <ScoreRing value={score.evidence} label="Evidence" />
            <ScoreRing value={score.confidence} label="Confidence" />
          </div>
          <p className="mt-6 max-w-3xl text-[#efe6d6]/70">{score.thesis}</p>
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            <ScoreBar value={score.opportunity} label="Opportunity" />
            <ScoreBar value={score.security} label="Security veto power" />
          </div>
        </section>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="panel rounded-3xl p-6">
          <p className="kicker">Why</p>
          <ul className="mt-4 space-y-4">
            {data.evidence.map((e) => (
              <li key={e.id} className="border-b border-[rgba(201,163,106,0.08)] pb-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm">{e.label}</span>
                  <span className={`badge ${e.verification}`}>{e.verification}</span>
                </div>
                <p className="mt-1 text-sm text-[#efe6d6]/60">{e.detail}</p>
                <p className="mt-1 font-mono text-[10px] text-[#f3d5a0]/40">
                  {e.source} · w{e.weight}
                </p>
              </li>
            ))}
            {data.evidence.length === 0 && <li className="text-[#efe6d6]/40">INSUFFICIENT EVIDENCE</li>}
          </ul>
        </section>

        <section className="panel rounded-3xl p-6">
          <p className="kicker">Risks & gate</p>
          <ul className="mt-4 space-y-4">
            {data.findings.map((f) => (
              <li key={f.id}>
                <div className="flex items-center gap-2">
                  <span className={`badge ${f.severity === "critical" || f.severity === "high" ? "bad" : "mid"}`}>{f.severity}</span>
                  <span className="badge">{f.gate}</span>
                </div>
                <p className="mt-2 text-sm">{f.title}</p>
                <p className="text-sm text-[#efe6d6]/60">{f.detail}</p>
              </li>
            ))}
            {data.findings.length === 0 && <li className="text-[#efe6d6]/40">No findings logged.</li>}
          </ul>
        </section>
      </div>

      <section className="panel mt-6 rounded-3xl p-6">
        <p className="kicker">Council</p>
        {data.votes.length === 0 ? (
          <p className="mt-4 text-[#efe6d6]/50">Council has not yet sat on this name. Disagreement itself is a signal.</p>
        ) : (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {data.votes.map((v) => (
              <article key={v.id} className="rounded-2xl border border-[rgba(201,163,106,0.12)] p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-[#6ee7f9]">
                    {String(v.teamNo).padStart(2, "0")} {v.teamName}
                  </span>
                  <span className={`badge ${v.stance}`}>{v.stance} {v.confidence}</span>
                </div>
                <p className="mt-2 text-sm text-[#efe6d6]/70">{v.rationale}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Block title="Whales" empty="No whale tape.">
          {data.whales.map((w) => (
            <p key={w.id} className="border-b border-[rgba(201,163,106,0.08)] py-2 text-sm">
              {w.action} {usd(w.amountUsd)} · {w.wallet}
              <span className="block text-xs text-[#efe6d6]/50">{w.note}</span>
            </p>
          ))}
        </Block>
        <Block title="On-chain" empty="No events.">
          {data.chain.map((e) => (
            <p key={e.id} className="border-b border-[rgba(201,163,106,0.08)] py-2 text-sm">
              {e.kind} · {e.wallet}
              <span className="block text-xs text-[#efe6d6]/50">{e.note}</span>
            </p>
          ))}
        </Block>
        <Block title="Social" empty="No social oxygen.">
          {data.social.map((s) => (
            <p key={s.id} className="border-b border-[rgba(201,163,106,0.08)] py-2 text-sm">
              {s.platform} {s.metric} {s.value} · {s.authenticity}
              <span className="block text-xs text-[#efe6d6]/50">{s.note}</span>
            </p>
          ))}
        </Block>
      </div>

      <section className="panel mt-6 rounded-3xl p-6">
        <p className="kicker">Paper / scenarios</p>
        {data.trades.length === 0 ? (
          <p className="mt-3 text-[#efe6d6]/50">No paper book. SKIP remains a legal outcome.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {data.trades.map((t) => (
              <div key={t.id} className="rounded-2xl border border-[rgba(201,163,106,0.12)] p-4 font-mono text-sm">
                <div className="flex justify-between">
                  <span>{t.status.toUpperCase()}</span>
                  <span className={t.pnlUsd >= 0 ? "text-[#4ade80]" : "text-[#fb7185]"}>
                    {usd(t.pnlUsd)} ({pct(t.pnlPct)})
                  </span>
                </div>
                <p className="mt-2 text-[#efe6d6]/70">
                  Entry {t.entry} · Stop {t.stop} · T1 {t.target1} · T2 {t.target2} · T3 {t.target3}
                </p>
                <p className="mt-2 font-sans text-sm">{t.notes}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <p className="mt-6 font-mono text-[11px] text-[#f3d5a0]/40">Holders {token.holders} · Updated {timeAgo(token.createdAt)}</p>
    </div>
  );
}

function Block({ title, empty, children }: { title: string; empty: string; children: ReactNode }) {
  const has = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <section className="panel rounded-3xl p-6">
      <p className="kicker">{title}</p>
      <div className="mt-3">{has ? children : <p className="text-[#efe6d6]/40">{empty}</p>}</div>
    </section>
  );
}
