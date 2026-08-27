import { loadCanonicalSnapshot, listCanonicalOpportunities } from "@/canonical_store";

export const dynamic = "force-dynamic";

/**
 * Canonical opportunities for the web UI — READ-ONLY adapter.
 *
 * The Python canonical brain is the sole authority/writer. This route only
 * reads `reports/canonical/decisions/latest.json` and returns the eligible
 * (valid, fresh, security-PASS) opportunities. It performs NO scoring, security
 * evaluation, discovery, or promotion. Empty/missing/stale ⇒ "no evaluated
 * opportunities yet" (fail-closed), never an invented opportunity.
 */
export async function GET() {
  try {
    const snapshot = await loadCanonicalSnapshot();
    const opportunities = listCanonicalOpportunities(snapshot);
    return Response.json({
      source: "canonical-decision-store",
      authoritative: true,
      count: opportunities.length,
      opportunities,
      messageFa: opportunities.length
        ? undefined
        : "هنوز فرصت معتبری توسط مغز کانونی ارزیابی نشده است.",
      disclaimerFa: "فقط پایش — سیگنال خرید واقعی نیست. PAPER ONLY.",
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "UNKNOWN";
    // Fail-closed: no opportunities on any error.
    return Response.json(
      { source: "canonical-decision-store", authoritative: true, count: 0, opportunities: [], error: message },
      { status: 200 },
    );
  }
}
