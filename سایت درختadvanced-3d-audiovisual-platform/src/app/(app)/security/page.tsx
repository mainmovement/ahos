import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { loadSecurity } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function SecurityPage() {
  const rows = await loadSecurity();
  const rejects = rows.filter((r) => r.security_findings.gate === "reject");

  return (
    <div>
      <PageHeader
        kicker="Security intelligence"
        title="The gate is not optional."
        lede="High opportunity plus critical risk equals REJECT. Honeypots, mint, freeze, tax, blacklist, LP ownership, deployer history."
      />
      <div className="panel mb-6 rounded-2xl p-5">
        <p className="kicker">Risk gate</p>
        <p className="font-display mt-2 text-4xl italic">{rejects.length} names bricked by the gate</p>
      </div>
      <div className="space-y-3">
        {rows.map((r) => (
          <article key={r.security_findings.id} className="panel rounded-2xl p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <Link href={`/tokens/${r.tokens?.slug ?? ""}`} className="font-display text-2xl italic">
                {r.tokens?.name ?? "Unknown"} <span className="font-mono text-sm">{r.tokens?.symbol}</span>
              </Link>
              <div className="flex gap-2">
                <span className={`badge ${r.security_findings.severity === "critical" ? "bad" : "mid"}`}>
                  {r.security_findings.severity}
                </span>
                <span className={`badge ${r.security_findings.gate}`}>{r.security_findings.gate}</span>
              </div>
            </div>
            <h3 className="mt-3">{r.security_findings.title}</h3>
            <p className="mt-1 text-sm text-[#efe6d6]/65">{r.security_findings.detail}</p>
            {r.token_scores && (
              <p className="mt-3 font-mono text-xs text-[#f3d5a0]/50">
                OPP {r.token_scores.opportunity} · SEC {r.token_scores.security} · CONF {r.token_scores.confidence}
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
