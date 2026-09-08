import { PageHeader } from "@/components/page-header";
import { PROVIDERS } from "@/lib/constants";
import { loadSystem } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function SystemPage() {
  const { components, logs } = await loadSystem();
  return (
    <div>
      <PageHeader
        kicker="System status"
        title="Self-debug the roots."
        lede="Collector, API, scoring, database, telegram, web, scheduler. Fail closed. Fallback is architecture, not apology."
      />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {components.map((c) => (
          <article key={c.id} className="panel rounded-2xl p-4">
            <div className="flex items-center justify-between">
              <span className="kicker">{c.layer}</span>
              <span className={`badge ${c.status === "ok" ? "good" : c.status === "degraded" ? "mid" : "bad"}`}>{c.status}</span>
            </div>
            <h3 className="mt-2 font-display text-2xl italic">{c.name}</h3>
            <p className="font-mono text-xs text-[#6ee7f9]">{c.provider} · {c.latencyMs}ms</p>
            <p className="mt-2 text-sm text-[#efe6d6]/60">{c.note}</p>
          </article>
        ))}
      </div>
      <h2 className="font-display mt-10 text-3xl italic">Provider abstraction</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {PROVIDERS.map((p) => (
          <div key={p.layer} className="panel rounded-2xl p-4">
            <div className="kicker">{p.layer}</div>
            <p className="mt-2">Primary: {p.primary}</p>
            <p className="text-sm text-[#efe6d6]/60">Fallback: {p.fallback.join(" → ")}</p>
          </div>
        ))}
      </div>
      <h2 className="font-display mt-10 text-3xl italic">System notes</h2>
      <div className="mt-4 space-y-3">
        {logs.map((l) => (
          <article key={l.id} className="panel rounded-2xl p-4">
            <p>{l.title}</p>
            <p className="text-sm text-[#efe6d6]/60">{l.body}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
