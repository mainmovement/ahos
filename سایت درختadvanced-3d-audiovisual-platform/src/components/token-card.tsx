import Link from "next/link";
import type { Token, TokenScore } from "@/db/schema";
import { decisionLabel, groupLabel, usd } from "@/lib/format";
import { ScoreBar } from "@/components/score-ring";

export function TokenCard({ token, score }: { token: Token; score: TokenScore | null }) {
  return (
    <Link
      href={`/tokens/${token.slug}`}
      className="panel panel-3d group block rounded-2xl p-5 hover:-translate-y-1"
      data-hot
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="kicker">{groupLabel(token.tokenGroup)}</div>
          <h3 className="font-display mt-2 text-3xl italic text-[#fff6e4]">{token.name}</h3>
          <p className="font-mono text-xs text-[#f3d5a0]/70">
            {token.symbol} · {token.chain}
          </p>
        </div>
        <span className={`badge ${score?.decision ?? token.status}`}>{decisionLabel(score?.decision ?? token.status)}</span>
      </div>
      <p className="mt-3 line-clamp-3 text-sm text-[#efe6d6]/70">{token.summary}</p>
      <div className="mt-4 grid grid-cols-3 gap-2 font-mono text-[11px] text-[#f3d5a0]/70">
        <div>
          MC
          <div className="text-[#fff6e4]">{usd(token.marketCapUsd)}</div>
        </div>
        <div>
          LIQ
          <div className="text-[#fff6e4]">{usd(token.liquidityUsd)}</div>
        </div>
        <div>
          VOL
          <div className="text-[#fff6e4]">{usd(token.volumeUsd)}</div>
        </div>
      </div>
      {score && (
        <div className="mt-4 grid gap-2">
          <ScoreBar value={score.opportunity} label="Opportunity" />
          <ScoreBar value={score.security} label="Security" />
          <ScoreBar value={score.confidence} label="Confidence" />
        </div>
      )}
    </Link>
  );
}
