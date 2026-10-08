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
 *  2. Dashboard browser -> gateway. `POST /api/auth/session` — gated on a
 *     launcher-issued one-time bootstrap token (REDTEAM-19 F1) — issues an
 *     httpOnly + SameSite=Strict session cookie plus a CSRF token in the
 *     response body that the browser echoes in the `X-AHOS-CSRF` header.
 *     Both are HMAC-signed with AHOS_DASHBOARD_SESSION_SECRET.
 *
 * Everything else — a bare bearer from a script, a body-asserted channel, a
 * header without a valid signature — resolves to `proven: false` and can never
 * be the owner (see `chat_actions.isOwner`). The client-asserted `channel` and
 * `user_id` are still carried through to the audit as `channel_claimed` /
 * hashed id, exactly as before; they are simply no longer a grant.
 *
 * Pure apart from `issueDashboardSession` (random tokens) and
 * `consumeBootstrapToken` (reads/rewrites the boot-token file). No network,
 * no DB. Run: npm run test:chat-auth
 */
import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const TG_UID_HEADER = "x-ahos-tg-uid";
export const TG_TS_HEADER = "x-ahos-tg-ts";
export const TG_SIG_HEADER = "x-ahos-tg-sig";
export const CSRF_HEADER = "x-ahos-csrf";
export const SID_COOKIE = "AHOS_SID";

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

/**
 * The session cookie name is namespaced per server instance: a short tag
 * derived from AHOS_DASHBOARD_SESSION_SECRET (REDTEAM-19 F6). Cookies are not
 * port-scoped, so a page or another AHOS checkout on a different 127.0.0.1
 * port could otherwise plant or collide with a bare `AHOS_SID` cookie. A cookie
 * issued under another secret has another name and is never even read; a
 * forged value under our name still fails the HMAC.
 */
export function sessionCookieName(secret: string): string {
  return `${SID_COOKIE}_${hmacHex(secret, "cookie-namespace").slice(0, 12)}`;
}

export type IssuedSession = { sessionId: string; csrfToken: string; cookies: string[] };

/**
 * Mint a dashboard session: ONE httpOnly session id cookie (namespaced, see
 * `sessionCookieName`) plus a CSRF token returned in the response BODY only.
 * The browser keeps the token in origin-scoped storage (localStorage is
 * per host:port, unlike cookies) and echoes it in the `X-AHOS-CSRF` header.
 *
 * There is deliberately no readable CSRF cookie any more (REDTEAM-19 F6):
 * cookies are sent to every 127.0.0.1 port, so a local server on another port
 * that the owner's browser talked to received BOTH the session and the CSRF
 * cookie and could replay them. The session cookie alone is useless without
 * the header token. Returns null when the secret is unset/short (fail closed).
 *
 * Callers must gate this on `checkSessionIssuance` + `consumeBootstrapToken`;
 * it does no request checks itself.
 */
export function issueDashboardSession(env: EnvMap = process.env): IssuedSession | null {
  const secret = readSecret(env, "AHOS_DASHBOARD_SESSION_SECRET");
  if (!secret) return null;
  const sessionId = randomBytes(24).toString("hex");
  const csrfToken = signToken(secret, "csrf", randomBytes(18).toString("hex"), sessionId);
  const sidCookie = signToken(secret, "sid", sessionId, "");
  const cookies = [
    `${sessionCookieName(secret)}=${sidCookie}; HttpOnly; Path=/; Max-Age=${SESSION_MAX_AGE_S}; SameSite=Strict`,
  ];
  return { sessionId, csrfToken, cookies };
}

/**
 * Verify the session cookie AND that the request carries its bound CSRF token
 * in the `X-AHOS-CSRF` header. Fail closed on any missing piece, a bad
 * signature, or a token bound to a different session id.
 *
 * The header is mandatory: a cross-origin page cannot set a custom header
 * without a CORS preflight, which this server never answers with
 * Access-Control-Allow-Origin, and it cannot read the token (it lives in the
 * dashboard origin's localStorage, not in a cookie).
 */
export function verifyDashboardSession(headers: Headers, env: EnvMap = process.env): SessionProof {
  const secret = readSecret(env, "AHOS_DASHBOARD_SESSION_SECRET");
  if (!secret) return { ok: false, reason: "NO_SERVER_SECRET" };
  const cookies = readCookies(headers.get("cookie"));
  const sidRaw = cookies.get(sessionCookieName(secret));
  if (!sidRaw) return { ok: false, reason: "NO_SESSION_COOKIE" };
  const sessionId = verifySignedToken(secret, "sid", sidRaw, "");
  if (!sessionId) return { ok: false, reason: "BAD_SESSION_SIGNATURE" };
  const csrfRaw = headers.get(CSRF_HEADER);
  if (!csrfRaw) return { ok: false, reason: "NO_CSRF_TOKEN" };
  const csrfId = verifySignedToken(secret, "csrf", csrfRaw.trim(), sessionId);
  if (!csrfId) return { ok: false, reason: "BAD_CSRF_TOKEN" };
  return { ok: true, sessionId };
}

// --------------------------------------------- session bootstrap (F1) --

/**
 * REDTEAM-19 F1: reaching 127.0.0.1 is NOT proof of being the owner. Any local
 * process, another OS user, a local service with SSRF, or a TCP forwarder can
 * reach the loopback listener, and the old issuance (loopback + an
 * x-forwarded-for value the client controls) minted owner sessions for all of
 * them. Issuance now needs a ONE-TIME bootstrap token that only the launcher
 * (or `python -m launcher bootstrap-url`) creates and hands to the owner's
 * browser in the URL fragment it opens.
 *
 * Server side only the sha256 of each token is stored, in a JSON file in the
 * launcher state dir (`AHOS_DASHBOARD_BOOT_FILE`, default
 * `<AHOS_DATA_DIR|./data>/launcher/dashboard_boot.json`). Tokens expire after a
 * short TTL and are removed on first use. The token is never logged, never a
 * NEXT_PUBLIC value, and never in a status report.
 */
export const BOOT_FILE_ENV = "AHOS_DASHBOARD_BOOT_FILE";

export function defaultBootFile(env: EnvMap = process.env): string {
  const explicit = String(env.AHOS_DASHBOARD_BOOT_FILE ?? "").trim();
  if (explicit) return explicit;
  const dataDir = String(env.AHOS_DATA_DIR ?? "").trim() || join(process.cwd(), "data");
  return join(dataDir, "launcher", "dashboard_boot.json");
}

type BootEntry = { sha256: string; expires_ts: number; issued_ts?: number };

function sha256Hex(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

export type BootResult = { ok: true } | { ok: false; reason: string };

/**
 * Consume a bootstrap token: true exactly once per token, before expiry.
 * Fails closed on a missing/corrupt file, a malformed token, an unknown or
 * expired token. The matched entry (and every expired one) is removed with an
 * atomic rewrite; the read-modify-write is synchronous, so two requests in this
 * process cannot both consume the same token.
 */
export function consumeBootstrapToken(
  token: unknown,
  opts: { file?: string; now?: number; env?: EnvMap } = {},
): BootResult {
  const raw = typeof token === "string" ? token.trim() : "";
  if (!/^[0-9a-f]{32,128}$/.test(raw)) return { ok: false, reason: "NO_BOOT_TOKEN" };
  const file = opts.file ?? defaultBootFile(opts.env ?? process.env);
  const nowS = (opts.now ?? Date.now()) / 1000;
  let entries: BootEntry[];
  try {
    const doc = JSON.parse(readFileSync(file, "utf8")) as { tokens?: unknown };
    entries = Array.isArray(doc.tokens) ? (doc.tokens as BootEntry[]) : [];
  } catch {
    return { ok: false, reason: "BOOT_STORE_UNAVAILABLE" };
  }
  const want = sha256Hex(raw);
  let hit = false;
  const keep: BootEntry[] = [];
  for (const e of entries) {
    if (!e || typeof e.sha256 !== "string" || typeof e.expires_ts !== "number") continue;
    if (e.expires_ts <= nowS) continue; // expired: drop
    if (!hit && constTimeEqual(e.sha256, want)) {
      hit = true; // single use: drop it
      continue;
    }
    keep.push(e);
  }
  try {
    const tmp = `${file}.${process.pid}.tmp`;
    writeFileSync(tmp, JSON.stringify({ version: 1, tokens: keep }), { encoding: "utf8", mode: 0o600 });
    renameSync(tmp, file);
  } catch {
    // A token we could not remove must not be accepted (it would stay replayable).
    return { ok: false, reason: "BOOT_STORE_UNWRITABLE" };
  }
  return hit ? { ok: true } : { ok: false, reason: "BAD_OR_EXPIRED_BOOT_TOKEN" };
}

const LOOPBACK_HOST = /^(127\.0\.0\.1|localhost|\[::1\])(:\d{1,5})?$/;

/**
 * Request-shape checks for POST /api/auth/session (all must pass):
 *  - a Host header that is exactly a loopback name (+ optional port), so a
 *    DNS-rebinding page (`evil.example`, `127.0.0.1.evil.example`) is refused;
 *  - `Sec-Fetch-Site` present and `same-origin` or `none`: every current
 *    browser sends it, and a cross-site or same-site-other-port page gets
 *    `cross-site`/`same-site`;
 *  - `Origin`, when present, exactly `http://<Host>`.
 * x-forwarded-for is deliberately NOT consulted: Next copies a client-supplied
 * value verbatim, so it proves nothing (REDTEAM-19 F1). These checks narrow the
 * browser attack surface; the bootstrap token is what proves the owner.
 */
export function checkSessionIssuance(req: Request): BootResult {
  const host = String(req.headers.get("host") ?? "").trim().toLowerCase();
  if (!host || !LOOPBACK_HOST.test(host)) return { ok: false, reason: "HOST_NOT_LOOPBACK" };
  const site = String(req.headers.get("sec-fetch-site") ?? "").trim().toLowerCase();
  if (site !== "same-origin" && site !== "none") return { ok: false, reason: "SEC_FETCH_SITE_REFUSED" };
  const origin = req.headers.get("origin");
  if (origin !== null && origin.trim().toLowerCase() !== `http://${host}`) {
    return { ok: false, reason: "ORIGIN_MISMATCH" };
  }
  return { ok: true };
}

/**
 * True when the request arrived over the loopback dashboard listener — the trust
 * boundary for `/api/launcher`'s read-only and control endpoints.
 *
 * `0638643` defined this; `d9492cb` deleted the definition while keeping the
 * route that imports it, so every launcher request threw on import and this gate
 * never ran. `f6c4f20` restored six sibling orphans from that same merge and
 * filed the resulting tsc error as "pre-existing unrelated" — it is the same
 * defect, seventh of seven. Restored here.
 *
 * The Host header is consulted first, the request URL is the fallback: a bare
 * `Request` carries no Host header, and under a real server the socket *bind* —
 * not a client-controlled header — is the boundary. So a loopback URL with a
 * spoofed off-loopback Host stays `true`, and an off-host URL with a matching
 * Host stays `false`. `scripts/m481_host_header_probe.mjs` is the record of which
 * framing is which, and M48.1 changes zero application code — this is a BL
 * restoration, not a version-bump deliverable.
 *
 * Both checks use the anchored `LOOPBACK_HOST`, not `startsWith`: the owner's own
 * rebinding note in `checkSessionIssuance` names `127.0.0.1.evil.example`, which
 * `startsWith("127.0.0.1")` — the original body — would have accepted.
 *
 * `x-forwarded-for` is deliberately NOT consulted, not even to fail closed: the
 * `0638643` body read it, but REDTEAM-19 F1 removed every consultation from this
 * module because Next copies a client-supplied value verbatim, so it proves
 * nothing — and the module's blanket "never consulted" invariant is source-greped
 * by the self-test. `checkSessionIssuance` is the sibling that sets the posture;
 * this function matches it.
 */
export function isLoopbackRequest(req: Request): boolean {
  const host = String(req.headers.get("host") ?? "").trim().toLowerCase();
  if (host && LOOPBACK_HOST.test(host)) return true;
  try {
    return LOOPBACK_HOST.test(new URL(req.url).hostname);
  } catch {
    return false;
  }
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

/**
 * Parse the raw /api/chat body into a plain object; anything else -> {}.
 *
 * The route hashes the exact bytes first (Telegram HMAC), then parses. It used
 * `await JSON.parse(raw).catch(...)`, but JSON.parse is synchronous and returns
 * a plain value with no .catch, so EVERY chat request threw "JSON.parse(...)
 * .catch is not a function" and answered with an internal-error reply (since
 * 0638643). Malformed JSON, arrays, null and primitives all map to {}.
 */
export function parseChatBody(raw: string): Record<string, unknown> {
  try {
    const v: unknown = JSON.parse(raw);
    return v !== null && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

const BOOT_HINT =
  "Open the dashboard from the AHOS launcher, or run `python -m launcher bootstrap-url` and open the printed URL.";

/**
 * The whole POST /api/auth/session decision, kept here (not in the route) so
 * the attack reproductions in scripts/chat_auth_selftest.ts exercise exactly
 * what the server runs. Order: request shape (403) -> server secret (503,
 * checked before the token so a misconfigured server never burns it) ->
 * one-time bootstrap token (401) -> session.
 */
export async function handleSessionIssuance(
  req: Request,
  opts: { env?: EnvMap; bootFile?: string; now?: number } = {},
): Promise<Response> {
  const env = opts.env ?? process.env;
  const shape = checkSessionIssuance(req);
  if (!shape.ok) {
    return Response.json({ ok: false, error: "SESSION_ISSUANCE_REFUSED", reason: shape.reason }, { status: 403 });
  }
  let boot: unknown = null;
  try {
    const body = (await req.json()) as { boot?: unknown } | null;
    boot = body && typeof body === "object" ? body.boot : null;
  } catch {
    boot = null;
  }
  const issued = issueDashboardSession(env);
  if (!issued) {
    return Response.json(
      {
        ok: false,
        error: "SESSION_SECRET_UNAVAILABLE",
        hint: "AHOS_DASHBOARD_SESSION_SECRET must be set server-side (>= 16 chars).",
      },
      { status: 503 },
    );
  }
  const consumed = consumeBootstrapToken(boot, { file: opts.bootFile, now: opts.now, env });
  if (!consumed.ok) {
    // A fixed reason code; the token itself is never echoed or logged.
    return Response.json(
      { ok: false, error: "BOOTSTRAP_TOKEN_REQUIRED", reason: consumed.reason, hint: BOOT_HINT },
      { status: 401 },
    );
  }
  const headers = new Headers({ "Cache-Control": "no-store" });
  for (const c of issued.cookies) headers.append("Set-Cookie", c);
  return Response.json({ ok: true, csrfToken: issued.csrfToken, csrfHeader: CSRF_HEADER }, { headers });
}
