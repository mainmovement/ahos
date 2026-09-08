import { PageHeader } from "@/components/page-header";
import { loadAlerts } from "@/lib/queries";
import { timeAgo } from "@/lib/format";
import { MarkRead } from "@/components/mark-read";

export const dynamic = "force-dynamic";

export default async function AlertsPage() {
  const rows = await loadAlerts();
  return (
    <div>
      <PageHeader
        kicker="Alerts"
        title="The tree speaks when the soil moves."
        lede="Discovery, opportunity, security, exit, whale, news, system. Critical security always outranks a pretty pump."
      />
      <div className="space-y-3">
        {rows.map((a) => (
          <article key={a.id} className={`panel rounded-2xl p-5 ${a.read ? "opacity-60" : ""}`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex gap-2">
                <span className={`badge ${a.severity === "critical" || a.severity === "high" ? "bad" : "watch"}`}>{a.severity}</span>
                <span className="badge">{a.kind}</span>
              </div>
              <span className="font-mono text-[11px] text-[#f3d5a0]/40">{timeAgo(a.createdAt)}</span>
            </div>
            <h3 className="mt-3 font-display text-2xl italic">{a.title}</h3>
            <p className="mt-1 text-sm text-[#efe6d6]/65">{a.body}</p>
            {!a.read && <MarkRead id={a.id} />}
          </article>
        ))}
        {rows.length === 0 && <div className="panel rounded-2xl p-8 text-[#efe6d6]/40">Quiet soil. No alerts.</div>}
      </div>
    </div>
  );
}
