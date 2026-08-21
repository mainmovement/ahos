import { readFile } from "fs/promises";
import path from "path";

export const dynamic = "force-dynamic";

/** Latest critical opportunity alert for the web dashboard (loud banner). */
export async function GET() {
  try {
    const file = path.join(process.cwd(), "reports", "pump_alert_state.json");
    const raw = await readFile(file, "utf8").catch(() => "{}");
    const json = JSON.parse(raw || "{}") as {
      last_alert_at?: number;
      last_token?: string;
      sent?: Record<string, number>;
      last_payload?: Record<string, unknown>;
    };
    const ageSec =
      typeof json.last_alert_at === "number"
        ? Math.max(0, Date.now() / 1000 - json.last_alert_at)
        : null;
    const active = ageSec != null && ageSec < 180; // banner stays hot 3 min
    return Response.json({
      active,
      ageSec,
      lastToken: json.last_token ?? null,
      lastAlertAt: json.last_alert_at ?? null,
      recentCount: Object.keys(json.sent || {}).length,
      payload: json.last_payload ?? null,
      disclaimerFa:
        "هشدار فرصت پایش است — سیگنال خرید واقعی نیست. PAPER ONLY.",
    });
  } catch (e) {
    const message = e instanceof Error ? e.message : "UNKNOWN";
    return Response.json({ active: false, error: message }, { status: 200 });
  }
}
