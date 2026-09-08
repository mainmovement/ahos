import { PageHeader } from "@/components/page-header";
import { loadLearning } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function LearningPage() {
  const rows = await loadLearning();
  return (
    <div>
      <PageHeader
        kicker="Learning engine"
        title="Every skip is a teacher."
        lede="Discover → analyze → decide → paper → monitor → result → post-mortem → learn → update → retest → improve."
      />
      <div className="space-y-4">
        {rows.map((r) => (
          <article key={r.learning_records.id} className="panel rounded-3xl p-6">
            <span className={`badge ${r.learning_records.kind === "win" ? "good" : r.learning_records.kind === "loss" ? "bad" : "watch"}`}>
              {r.learning_records.kind}
            </span>
            <h3 className="font-display mt-3 text-3xl italic">{r.learning_records.title}</h3>
            <p className="mt-2 text-[#efe6d6]/70">{r.learning_records.insight}</p>
            {r.tokens && <p className="kicker mt-3">{r.tokens.symbol}</p>}
          </article>
        ))}
      </div>
    </div>
  );
}
