/**
 * AHOS Opportunity Alert Engine (paper-only).
 * Writes reports/pump_alert_state.json for the web banner.
 * Optionally notifies Telegram when TELEGRAM_BOT_TOKEN + TELEGRAM_ALLOWED_CHAT_IDS are set.
 * Never hardcodes credentials. Never claims buy signals.
 */
import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import type { ScoredOpportunity } from "./types";

const STATE_REL = path.join("reports", "pump_alert_state.json");
const COOLDOWN_SEC = Number(process.env.AHOS_ALERT_COOLDOWN_SEC || "900");
const SCORE_FLOOR = Number(process.env.AHOS_ALERT_SCORE_FLOOR || "0.72");

export type AlertState = {
  sent: Record<string, number>;
  last_alert_at?: number;
  last_token?: string;
  last_payload?: AlertPayload;
};

export type AlertPayload = {
  tokenKey: string;
  symbol: string;
  chain: string;
  address: string | null;
  decision: string;
  rankScore: number | null;
  confidence: string;
  securityStatus: string;
  liquidityUsd: number | null;
  volume24h: number | null;
  priceUsd: number | null;
  priceChange1h: number | null;
  reasonsFa: string[];
  risksFa: string[];
  unknownsFa: string[];
  timestamp: string;
  disclaimerFa: string;
};

async function loadState(): Promise<AlertState> {
  try {
    const raw = await readFile(path.join(process.cwd(), STATE_REL), "utf8");
    const json = JSON.parse(raw) as AlertState;
    return { ...json, sent: json.sent || {} };
  } catch {
    return { sent: {} };
  }
}

async function saveState(state: AlertState): Promise<void> {
  const dir = path.join(process.cwd(), "reports");
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(process.cwd(), STATE_REL), JSON.stringify(state, null, 2), "utf8");
}

function securityOk(status: string, rankScore: number | null): boolean {
  const s = (status || "").toUpperCase();
  if (["HONEYPOT", "REJECT", "FAIL", "DOWN"].includes(s)) return false;
  if (s === "UNKNOWN") return rankScore != null && rankScore >= 0.8;
  return true;
}

export function shouldAlertOpportunity(opp: ScoredOpportunity, state: AlertState): boolean {
  if (opp.decision !== "WATCH") return false;
  if (opp.rankScore == null || opp.rankScore < SCORE_FLOOR) return false;
  if (!securityOk(opp.securityStatus, opp.rankScore)) return false;
  if ((opp.token.liquidityUsd ?? 0) < 15_000 && opp.token.liquidityUsd != null) return false;
  if (opp.token.paidPromotion && (opp.token.liquidityUsd ?? 0) < 50_000) return false;
  const key = opp.token.tokenKey;
  const last = state.sent[key] || 0;
  if (Date.now() / 1000 - last < COOLDOWN_SEC) return false;
  return true;
}

export function buildAlertPayload(opp: ScoredOpportunity): AlertPayload {
  return {
    tokenKey: opp.token.tokenKey,
    symbol: opp.token.symbol,
    chain: opp.token.chain,
    address: opp.token.address,
    decision: opp.decision,
    rankScore: opp.rankScore,
    confidence: opp.confidence,
    securityStatus: opp.securityStatus,
    liquidityUsd: opp.token.liquidityUsd,
    volume24h: opp.token.volume24h,
    priceUsd: opp.token.priceUsd,
    priceChange1h: opp.token.priceChange1h,
    reasonsFa: (opp.reasonsFa || []).slice(0, 5),
    risksFa: (opp.risksFa || []).slice(0, 5),
    unknownsFa: (opp.unknownsFa || []).slice(0, 5),
    timestamp: new Date().toISOString(),
    disclaimerFa:
      "این هشدار فرصت پایش است — سیگنال خرید واقعی نیست. PAPER ONLY. تصمیم نهایی با کاربر است.",
  };
}

function formatTelegramHtml(p: AlertPayload): string {
  const score =
    p.rankScore != null ? Math.round(p.rankScore * 100).toString() : "UNKNOWN";
  const lines = [
    "🚨 <b>CRITICAL OPPORTUNITY ALERT — AHOS / Sun Sniper</b>",
    "",
    `• نماد: <b>${escapeHtml(p.symbol)}</b> | زنجیره: ${escapeHtml(p.chain)}`,
    `• حکم: <b>${escapeHtml(p.decision)}</b> | امتیاز: ${score} | اطمینان: ${escapeHtml(p.confidence)}`,
    `• امنیت: ${escapeHtml(p.securityStatus)}`,
  ];
  if (p.priceUsd != null) lines.push(`• قیمت (شواهد): $${p.priceUsd}`);
  if (p.liquidityUsd != null) lines.push(`• نقدینگی: $${Math.round(p.liquidityUsd).toLocaleString("en-US")}`);
  if (p.volume24h != null) lines.push(`• حجم ۲۴س: $${Math.round(p.volume24h).toLocaleString("en-US")}`);
  if (p.priceChange1h != null) lines.push(`• تغییر ۱س: ${p.priceChange1h >= 0 ? "+" : ""}${p.priceChange1h.toFixed(1)}%`);
  if (p.address) lines.push(`• قرارداد: <code>${escapeHtml(p.address)}</code>`);
  if (p.reasonsFa.length) {
    lines.push("", "<b>شواهد</b>");
    for (const r of p.reasonsFa) lines.push(`  ✅ ${escapeHtml(r)}`);
  }
  if (p.risksFa.length) {
    lines.push("", "<b>ریسک</b>");
    for (const r of p.risksFa) lines.push(`  ⚠️ ${escapeHtml(r)}`);
  }
  if (p.unknownsFa.length) {
    lines.push("", "<b>UNKNOWN</b>");
    for (const u of p.unknownsFa) lines.push(`  ❓ ${escapeHtml(u)}`);
  }
  lines.push("", `⏱ ${p.timestamp}`, "", `⚠️ ${p.disclaimerFa}`);
  return lines.join("\n");
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">");
}

async function pushTelegram(text: string): Promise<{ ok: boolean; error?: string; sent?: number }> {
  const token = (process.env.TELEGRAM_BOT_TOKEN || "").trim();
  const raw = (process.env.TELEGRAM_ALLOWED_CHAT_IDS || "").trim();
  const chats = raw.split(",").map((x) => x.trim()).filter(Boolean);
  if (!token) return { ok: false, error: "NO_TOKEN" };
  if (!chats.length) return { ok: false, error: "NO_CHAT_IDS" };

  let sent = 0;
  for (const chatId of chats) {
    try {
      const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          parse_mode: "HTML",
          disable_notification: false,
        }),
        signal: AbortSignal.timeout(12_000),
      });
      const json = (await res.json()) as { ok?: boolean };
      if (json.ok) sent += 1;
    } catch {
      /* per-chat failure does not abort others */
    }
  }
  return sent > 0 ? { ok: true, sent } : { ok: false, error: "SEND_FAILED" };
}

/**
 * After ranking: emit at most a few high-evidence WATCH alerts per cycle.
 */
export async function processOpportunityAlerts(
  ranked: ScoredOpportunity[],
): Promise<{ emitted: AlertPayload[]; telegram: Array<{ tokenKey: string; ok: boolean; error?: string }> }> {
  const state = await loadState();
  const emitted: AlertPayload[] = [];
  const telegram: Array<{ tokenKey: string; ok: boolean; error?: string }> = [];

  for (const opp of ranked) {
    if (emitted.length >= 3) break;
    if (!shouldAlertOpportunity(opp, state)) continue;
    const payload = buildAlertPayload(opp);
    state.sent[payload.tokenKey] = Date.now() / 1000;
    state.last_alert_at = Date.now() / 1000;
    state.last_token = payload.tokenKey;
    state.last_payload = payload;
    emitted.push(payload);

    const tg = await pushTelegram(formatTelegramHtml(payload));
    telegram.push({ tokenKey: payload.tokenKey, ok: tg.ok, error: tg.error });
  }

  if (emitted.length) await saveState(state);
  return { emitted, telegram };
}
