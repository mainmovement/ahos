import { authorizeWebApi, sanitizePublicError } from "@/web_api_auth";
import { evaluateWebAlertBanner } from "@/alert_banner";
import { loadCanonicalReadModel } from "@/canonical_read_model";
import { readFile } from "fs/promises";
import path from "path";

export const dynamic = "force-dynamic";

const FAIL_CLOSED = {
  active: false,
  reason: "BANNER_EVAL_FAILED",
  ageSec: null,
  lastToken: null,
  lastAlertAt: null,
  recentCount: 0,
  payload: null,
  disclaimerFa: "هشدار فرصت پایش است — سیگنال خرید واقعی نیست. PAPER ONLY.",
};

/** Latest opportunity-monitor banner. Re-checks live canonical BUY + overlay PASS. */
export async function GET(req: Request) {
  const denied = authorizeWebApi(req);
  if (denied) return denied;
  try {
    const file = path.join(process.cwd(), "reports", "pump_alert_state.json");
    const raw = await readFile(file, "utf8").catch(() => "{}");
    let json: unknown = {};
    try {
      json = JSON.parse(raw || "{}");
    } catch {
      json = {};
    }
    const model = await loadCanonicalReadModel();
    return Response.json(evaluateWebAlertBanner(json as object, model));
  } catch (e) {
    return Response.json(
      { ...FAIL_CLOSED, error: sanitizePublicError(e) },
      { status: 200 },
    );
  }
}
