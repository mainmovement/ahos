/**
 * Lane-B Web API auth gate — mirrors Telegram allowlist fail-closed doctrine.
 *
 * Modes:
 *   RESTRICTED          — AHOS_WEB_API_TOKEN set; Bearer / X-AHOS-Web-Token required
 *   OPEN_ACCESS         — AHOS_WEB_API_ALLOW_OPEN_ACCESS=1 (local/mock only)
 *   LOCKED_NO_TOKEN     — no token and no open-access opt-in (default)
 *
 * Never invent auth. Unset token without explicit open access = locked.
 */

import { timingSafeEqual } from "crypto";

export type WebApiGateMode = "RESTRICTED" | "OPEN_ACCESS" | "LOCKED_NO_TOKEN";

const OPEN_TOKENS = new Set(["1", "true", "yes", "on"]);

const SECRET_PATTERNS: RegExp[] = [
  /\b[0-9]{8,12}:[a-zA-Z0-9_-]{30,50}\b/g, // Telegram bot token
  /\bsk-[a-zA-Z0-9]{20,60}\b/g, // OpenAI-style
  /\bghp_[a-zA-Z0-9]{36}\b/g,
  /\bgsk_[a-zA-Z0-9]{40,60}\b/g,
  /\bAIzaSy[a-zA-Z0-9_-]{25,45}\b/g,
  /\b0x[0-9a-fA-F]{64}\b/g,
  /\bBearer\s+[a-zA-Z0-9_.-]{16,}\b/gi,
  /\bpostgresql:\/\/[^\s"'`]+/gi,
  /\bpostgres:\/\/[^\s"'`]+/gi,
];

const REDACTED = "[REDACTED_SECRET]";

function envFlag(name: string): boolean {
  const raw = (process.env[name] || "").trim().toLowerCase();
  return OPEN_TOKENS.has(raw);
}

export function webApiConfiguredToken(): string {
  return (process.env.AHOS_WEB_API_TOKEN || "").trim();
}

export function webApiGateMode(): WebApiGateMode {
  if (webApiConfiguredToken()) return "RESTRICTED";
  return envFlag("AHOS_WEB_API_ALLOW_OPEN_ACCESS") ? "OPEN_ACCESS" : "LOCKED_NO_TOKEN";
}

export function extractWebApiToken(req: Request): string | null {
  const auth = (req.headers.get("authorization") || "").trim();
  const bearer = /^Bearer\s+(.+)$/i.exec(auth);
  if (bearer?.[1]) return bearer[1].trim();
  const header = req.headers.get("x-ahos-web-token");
  if (header && header.trim()) return header.trim();
  return null;
}

function tokensEqual(a: string, b: string): boolean {
  const left = Buffer.from(a, "utf8");
  const right = Buffer.from(b, "utf8");
  if (left.length !== right.length) return false;
  try {
    return timingSafeEqual(left, right);
  } catch {
    return false;
  }
}

/**
 * Returns a 401 Response when the request must be rejected; null when allowed.
 */
export function authorizeWebApi(req: Request): Response | null {
  const mode = webApiGateMode();
  if (mode === "OPEN_ACCESS") return null;
  if (mode === "LOCKED_NO_TOKEN") {
    return Response.json(
      {
        ok: false,
        error: "WEB_API_LOCKED_NO_TOKEN",
        mode,
        hintFa:
          "AHOS_WEB_API_TOKEN تنظیم نشده. برای دسترسی محلی موقت AHOS_WEB_API_ALLOW_OPEN_ACCESS=1",
      },
      { status: 401 },
    );
  }
  const expected = webApiConfiguredToken();
  const got = extractWebApiToken(req);
  if (!got || !tokensEqual(got, expected)) {
    return Response.json(
      { ok: false, error: "WEB_API_UNAUTHORIZED", mode: "RESTRICTED" },
      { status: 401 },
    );
  }
  return null;
}

/** Public-facing error text — never leak secrets or long raw stacks. */
export function sanitizePublicError(error: unknown, maxLen = 180): string {
  let raw = error instanceof Error ? error.message : "UNKNOWN";
  if (typeof raw !== "string" || !raw.trim()) raw = "UNKNOWN";
  let out = raw;
  for (const pattern of SECRET_PATTERNS) {
    out = out.replace(pattern, REDACTED);
  }
  out = out.replace(/\s+/g, " ").trim();
  if (out.length > maxLen) out = `${out.slice(0, maxLen)}…`;
  return out || "UNKNOWN";
}
