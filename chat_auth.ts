/**
 * Mission 9.5 (corrective security): server-side identity proof for the chat
 * control surface. Fixes BLOCKER B1 / BL-3 of the 2026-10-02 independent
 * reviews (REDTEAM-19 and Agent-16 QA).
 *
 * Before this module, `chat_actions.isOwner()` trusted the client-supplied
 * `channel`/`user_id` from the JSON body, `channel` defaulted to `"web"` (an
 * owner channel), and the dashboard bearer token was a `NEXT_PUBLIC_*` value
 * compiled into the browser bundle. Anyone holding that token could claim
 * `channel: "web"` (or a spoofed Telegram admin id), receive the one-time
 * confirm code in the HTTP response, and confirm it in a second request —
 * starting/stopping the engine and recording paper buys with no human.
 *
 * Two server-verified identity paths now exist. Both are backed by server-only
 * secrets that live in the process environment (never `NEXT_PUBLIC`, never
 * printed, never committed — `.env` is gitignored):
 *
 *  1. Telegram bot -> gateway. The bot HMAC-signs every request with
 *     AHOS_TELEGRAM_GATEWAY_SECRET over `user_id|timestamp|sha256(body)`.
 *     A ±300 s replay window and a constant-time compare are enforced, and the
 *     signature covers the exact request body, so `user_id` cannot be swapped.
 *  2. Dashboard browser -> gateway. `POST /api/auth/session` issues an
 *     httpOnly + SameSite=Lax session cookie plus a CSRF token (a second
 *     cookie the browser may read and must echo back in the `X-AHOS-CSRF`
 *     header). Both are HMAC-signed with AHOS_DASHBOARD_SESSION_SECRET.
 *     The browser holds no shared secret at all.
 *
 * Everything else — a bare bearer from a script, a body-asserted channel, a
 * header without a valid signature — resolves to `proven: false` and can never
 * be the owner (see `chat_actions.isOwner`). The client-asserted `channel` and
 * `user_id` are still carried through to the audit as `channel_claimed` /
 * hashed id, exactly as before; they are simply no longer a grant.
 *
 * Pure apart from `issueDashboardSession` (which generates the tokens). No
 * network, no DB, no file writes. Run: npm run test:chat-auth
 */
import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export const TG_UID_HEADER = "x-ahos-tg-uid";
export const TG_TS_HEADER = "x-ahos-tg-ts";
export const TG_SIG_HEADER = "x-ahos-tg-sig";
export const CSRF_HEADER = "x-ahos-csrf";
export const SID_COOKIE = "AHOS_SID";
export const CSRF_COOKIE = "AHOS_CSRF";

/** The bot and the gateway must agree to within this skew (both are local). */
export const TG_REPLAY_WINDOW_MS = 300_000;
export const SESSION_MAX_AGE_S = 12 * 60 * 60;

export type EnvMap = Record<string, string | undefined>;

export type ResolvedIdentity = {
  channel: string | null;
  userId: string | null;
  /** True only for a verified Telegram HMAC or a verified dashboard session. */
  proven: boolean;
  proof: "telegram_hmac" | "dashboard_session" | "none";
  /** Never shown to the caller; evidence/diagnostic only. */
  proofReason: string | null;
};

// ---------------------------------------------------------------- helpers --

function hmacHex(secret: string, msg: string): string {
  return createHmac("sha256", secret).update(msg, "utf8").digest("hex");
}

function constTimeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a, "utf8");
  const right = Buffer.from(b, "utf8");
  if (left.length !== right.length) return false;
  try {
    return timingSafeEqual(left, right);
  } catch {
    return false;
  }
}

function readSecret(env: EnvMap, name: string): string | null {
  const v = String(env[name] ?? "").trim();
  return v.length >= 16 ? v : null;
}

/** Parse `name=value` pairs out of a Cookie header (no quoting support needed). */
export function readCookies(cookieHeader: string | null | undefined): Map<string, string> {
  const out = new Map<string, string>();
  for (const part of String(cookieHeader ?? "").split(/;+/)) {
    const idx = part.indexOf("=");
    if (idx <= 0) continue;
    const k = part.slice(0, idx).trim();
    const v = part.slice(idx + 1).trim();
    if (k) out.set(k, v);
  }
  return out;
}

// ------------------------------------------------------------ telegram HMAC --

export type TelegramProof = { ok: true; userId: string } | { ok: false; reason: string };

/**
 * Verify the bot's HMAC over `user_id|timestamp|sha256(body)`. Fails closed:
 * a missing/short server secret, a missing header, a stale timestamp, a bad
 * signature or a body mismatch all return `{ ok: false }`, and the caller is
 * then NOT the owner.
 */
export function verifyTelegramIdentity(
  headers: Headers,
  bodySha256: string,
  env: EnvMap = process.env,
): TelegramProof {
  const secret = readSecret(env, "AHOS_TELEGRAM_GATEWAY_SECRET");
  if (!secret) return { ok: false, reason: "NO_SERVER_SECRET" };
  const uid = String(headers.get(TG_UID_HEADER) ?? "").trim();
  const tsRaw = String(headers.get(TG_TS_HEADER) ?? "").trim();
  const sig = String(headers.get(TG_SIG_HEADER) ?? "").trim();
  if (!uid || !tsRaw || !sig) return { ok: false, reason: "NO_HMAC_HEADERS" };
  const ts = Number(tsRaw);
  if (!Number.isInteger(ts) || ts <= 0) return { ok: false, reason: "BAD_TIMESTAMP" };
  const now = Date.now();
  if (Math.abs(now - ts) > TG_REPLAY_WINDOW_MS) return { ok: false, reason: "TIMESTAMP_OUTSIDE_WINDOW" };
  const expected = hmacHex(secret, `${uid}|${tsRaw}|${bodySha256}`);
  if (!constTimeEqual(sig, expected)) return { ok: false, reason: "BAD_SIGNATURE" };
  return { ok: true, userId: uid };
}

// ------------------------------------------------------ dashboard session --

export type SessionProof = { ok: true; sessionId: string } | { ok: false; reason: string };

/** `<random>.<hmac>`; the hmac binds the id to this server's secret. */
function signToken(secret: string, kind: string, id: string, extra: string): string {
  return `${id}.${hmacHex(secret, `${kind}:${id}:${extra}`)}`;
}

function verifySignedToken(secret: string, kind: string, raw: string, extra: string): string | null {
  const idx = raw.lastIndexOf(".");
  if (idx <= 0) return null;
  const id = raw.slice(0, idx);
  const sig = raw.slice(idx + 1);
  if (!id || !/^[0-9a-f]{16,}$/.test(id)) return null;
  if (!constTimeEqual(sig, hmacHex(secret, `${kind}:${id}:${extra}`))) return null;
  return id;
}

export type IssuedSession = { sessionId: string; csrfToken: string; cookies: string[] };

/**
 * Mint a dashboard session: an httpOnly session id cookie plus a CSRF token
 * the browser may read and must echo in the `X-AHOS-CSRF` header. Returns null
 * when the server secret is unset or too short (fail closed).
 */
export function issueDashboardSession(env: EnvMap = process.env): IssuedSession | null {
  const secret = readSecret(env, "AHOS_DASHBOARD_SESSION_SECRET");
  if (!secret) return null;
  const sessionId = randomBytes(24).toString("hex");
  const csrfToken = randomBytes(18).toString("hex");
  const sidCookie = signToken(secret, "sid", sessionId, "");
  const csrfCookie = signToken(secret, "csrf", csrfToken, sessionId);
  const common = `Path=/; Max-Age=${SESSION_MAX_AGE_S}; SameSite=Lax`;
  const cookies = [
    `${SID_COOKIE}=${sidCookie}; HttpOnly; ${common}`,
    `${CSRF_COOKIE}=${csrfCookie}; ${common}`,
  ];
  return { sessionId, csrfToken, cookies };
}

/**
 * Verify the session cookie AND that the request carries its bound CSRF token
 * (either in the echo header or the readable cookie — the browser sends both).
 * Fail closed on any missing piece, a bad signature, or a token bound to a
 * different session id.
 */
export function verifyDashboardSession(headers: Headers, env: EnvMap = process.env): SessionProof {
  const secret = readSecret(env, "AHOS_DASHBOARD_SESSION_SECRET");
  if (!secret) return { ok: false, reason: "NO_SERVER_SECRET" };
  const cookies = readCookies(headers.get("cookie"));
  const sidRaw = cookies.get(SID_COOKIE);
  if (!sidRaw) return { ok: false, reason: "NO_SESSION_COOKIE" };
  const sessionId = verifySignedToken(secret, "sid", sidRaw, "");
  if (!sessionId) return { ok: false, reason: "BAD_SESSION_SIGNATURE" };
  const csrfRaw = headers.get(CSRF_HEADER) || cookies.get(CSRF_COOKIE);
  if (!csrfRaw) return { ok: false, reason: "NO_CSRF_TOKEN" };
  const csrfId = verifySignedToken(secret, "csrf", csrfRaw, sessionId);
  if (!csrfId) return { ok: false, reason: "BAD_CSRF_TOKEN" };
  return { ok: true, sessionId };
}

// ------------------------------------------------------- route integration --

/**
 * Resolve the caller's identity for /api/chat, in trust order:
 *   1. verified Telegram HMAC  -> channel "telegram", the signed user id
 *   2. verified dashboard session -> channel "dashboard", the session id
 *      (per-session, so two dashboard tabs/two browsers never share a
 *      pending-action identity or conversation memory)
 *   3. anything else -> the body's asserted channel/user id, `proven: false`
 *
 * `bodySha256` must be the sha256 of the exact request body the HMAC covers.
 */
export function resolveChatIdentity(args: {
  headers: Headers;
  bodySha256: string;
  body: Record<string, unknown>;
  env?: EnvMap;
}): ResolvedIdentity {
  const env = args.env ?? process.env;
  const tg = verifyTelegramIdentity(args.headers, args.bodySha256, env);
  if (tg.ok) {
    return { channel: "telegram", userId: tg.userId, proven: true, proof: "telegram_hmac", proofReason: null };
  }
  const reasons: string[] = [];
  if (tg.reason !== "NO_HMAC_HEADERS") reasons.push(`telegram:${tg.reason}`);
  const sess = verifyDashboardSession(args.headers, env);
  if (sess.ok) {
    return {
      channel: "dashboard",
      userId: sess.sessionId,
      proven: true,
      proof: "dashboard_session",
      proofReason: null,
    };
  }
  if (sess.reason !== "NO_SESSION_COOKIE") reasons.push(`session:${sess.reason}`);
  const claimedChannel = typeof args.body.channel === "string" ? args.body.channel.trim() : null;
  const claimedUid = typeof args.body.user_id === "string" ? args.body.user_id.trim() : null;
  return {
    channel: claimedChannel || null,
    userId: claimedUid || null,
    proven: false,
    proof: "none",
    proofReason: reasons.length ? reasons.join(";") : "unverified_client_assertion",
  };
}

/** True when the request arrived over the loopback dashboard listener. */
export function isLoopbackRequest(req: Request): boolean {
  if (req.headers.get("x-forwarded-for")) return false;
  const host = String(req.headers.get("host") ?? "").toLowerCase();
  if (host.startsWith("127.0.0.1") || host.startsWith("localhost") || host.startsWith("[::1]")) return true;
  // The Host header is absent on a bare Request object; fall back to the URL.
  try {
    const u = new URL(req.url);
    return u.hostname === "127.0.0.1" || u.hostname === "localhost" || u.hostname === "[::1]";
  } catch {
    return false;
  }
}
