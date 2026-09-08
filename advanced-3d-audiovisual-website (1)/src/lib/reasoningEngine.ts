import { db } from "@/db";
import { tokens, opportunityScores, paperTrades, alerts as alertsTable } from "@/db/schema";
import { desc, eq, ilike, or, sql } from "drizzle-orm";

// ---------------------------------------------------------------------------
// AHOS Local Reasoning Engine — PRESENTATION CONSUMER, NOT CANONICAL BRAIN
// ---------------------------------------------------------------------------
// Classification: uploaded Web/3D conversational fallback over *stored* rows.
// It ranks `opportunityScores` already in local Postgres. It does not:
//   - resolve canonical identity
//   - evaluate the Lane B security overlay
//   - compute a Python CanonicalDecision
//   - synthesize BUY / ENTER
//
// Preserve this tree. Do not wire it as a second decision authority.
// Canonical authority: architecture/decision/authority.py
// ---------------------------------------------------------------------------
// This is the zero-budget fallback conversational layer described in the
// project vision (§30-32): when no external LLM provider key is configured,
// AHOS must still be able to answer questions using its own verified data —
// never hallucinating, always citing evidence, always defaulting to
// UNKNOWN / INSUFFICIENT EVIDENCE rather than inventing an answer.
//
// If process.env.OPENAI_API_KEY (or another provider key) is present in the
// future, this module can be swapped for a real LLM call while keeping the
// same interface: answerQuestion(message) => string.
// ---------------------------------------------------------------------------

function fmtUsd(v: string | number | null | undefined) {
  const n = typeof v === "string" ? parseFloat(v) : v ?? 0;
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: n < 1 ? 6 : 2 })}`;
}

async function bestOpportunity() {
  const [row] = await db
    .select({ token: tokens, score: opportunityScores })
    .from(opportunityScores)
    .innerJoin(tokens, eq(tokens.id, opportunityScores.tokenId))
    .where(sql`${opportunityScores.councilDecision} != 'reject'`)
    .orderBy(desc(opportunityScores.opportunityScore))
    .limit(1);
  return row;
}

async function findToken(query: string) {
  const cleaned = query.replace(/[$#]/g, "").trim();
  const [row] = await db
    .select()
    .from(tokens)
    .where(or(ilike(tokens.symbol, `%${cleaned}%`), ilike(tokens.name, `%${cleaned}%`)))
    .limit(1);
  return row;
}

async function tokenReport(tokenId: number) {
  const [score] = await db.select().from(opportunityScores).where(eq(opportunityScores.tokenId, tokenId));
  return score;
}

async function openTradesSummary() {
  return db
    .select({ trade: paperTrades, token: tokens })
    .from(paperTrades)
    .innerJoin(tokens, eq(tokens.id, paperTrades.tokenId))
    .where(eq(paperTrades.status, "open"));
}

async function recentAlertsSummary() {
  return db.select().from(alertsTable).orderBy(desc(alertsTable.createdAt)).limit(5);
}

export async function answerQuestion(rawMessage: string): Promise<string> {
  const message = rawMessage.toLowerCase().trim();

  // Best opportunity
  if (/(best|top|بهترین).*(opportunity|فرصت|token|توکن)|فرصت امروز/.test(message)) {
    const best = await bestOpportunity();
    if (!best) return "INSUFFICIENT EVIDENCE — no scored candidates are currently available in the system.";
    const { token, score } = best;
    return [
      `Stored ranking (not a canonical Python BUY): **${token.name} ($${token.symbol})** on ${token.chain}.`,
      `Stored opportunity score: ${score.opportunityScore}/100 · Stored security score: ${score.securityScore}/100 · Confidence: ${score.confidence}/100.`,
      `Stored council field: ${score.councilDecision.toUpperCase().replace("_", " ")} — this is a database row, not CanonicalDecisionAuthority.`,
      score.whyPoints?.[0] ? `Primary stored evidence: ${score.whyPoints[0]}` : "",
      `Ask me to "explain ${token.symbol}" for the stored evidence breakdown.`,
    ]
      .filter(Boolean)
      .join("\n");
  }

  // Open trades
  if (/(open|active).*(trade|position)|معامله.*(باز|فعال)/.test(message)) {
    const open = await openTradesSummary();
    if (open.length === 0) return "There are no open paper trades right now.";
    return (
      `${open.length} open paper trade(s):\n` +
      open
        .map((o) => `• ${o.token.symbol}: entry ${fmtUsd(o.trade.entryPrice)}, stop ${fmtUsd(o.trade.stopLoss)}, target1 ${fmtUsd(o.trade.target1)}`)
        .join("\n")
    );
  }

  // Alerts
  if (/(alert|notification|هشدار)/.test(message)) {
    const recent = await recentAlertsSummary();
    if (recent.length === 0) return "No alerts have been generated yet.";
    return `Most recent alerts:\n` + recent.map((a) => `• [${a.severity.toUpperCase()}] ${a.title}`).join("\n");
  }

  // Explain / why a specific token
  const explainMatch = message.match(/(?:explain|why|چرا|بررسی)\s*([a-z0-9$#]+)/i);
  if (explainMatch) {
    const token = await findToken(explainMatch[1]);
    if (!token) return `I could not find a token matching "${explainMatch[1]}". Try the exact symbol, e.g. SOLV or AURM.`;
    const score = await tokenReport(token.id);
    if (!score) return `${token.name} has not completed council scoring yet — INSUFFICIENT EVIDENCE.`;
    return [
      `**${token.name} ($${token.symbol})** — Council decision: ${score.councilDecision.toUpperCase().replace("_", " ")}`,
      `Opportunity ${score.opportunityScore} · Security ${score.securityScore} · Confidence ${score.confidence}`,
      "Why:",
      ...(score.whyPoints ?? []).map((p) => `  • ${p}`),
      "Risks:",
      ...(score.riskPoints ?? []).map((p) => `  • ${p}`),
    ].join("\n");
  }

  // Direct symbol lookup e.g. "SOLV" or "$SOLV"
  const directToken = await findToken(rawMessage.trim());
  if (directToken && rawMessage.trim().length <= 12) {
    const score = await tokenReport(directToken.id);
    if (!score) return `${directToken.name} exists in the discovery feed but has no score yet — INSUFFICIENT EVIDENCE.`;
    return `${directToken.name} ($${directToken.symbol}): Opportunity ${score.opportunityScore}, Security ${score.securityScore}, Confidence ${score.confidence}. Decision: ${score.councilDecision.replace("_", " ")}.`;
  }

  // Fallback — honest uncertainty per project philosophy (§57 anti-hallucination)
  return [
    "I don't have a verified, evidence-backed answer for that yet — flagging as INSUFFICIENT EVIDENCE rather than guessing.",
    "Try asking things like:",
    "• \"What's the best opportunity today?\"",
    "• \"Explain SOLV\"",
    "• \"Show open trades\"",
    "• \"Any new alerts?\"",
  ].join("\n");
}
