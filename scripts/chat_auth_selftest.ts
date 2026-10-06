/**
 * Mission 9.5 + REDTEAM-19 F1/F6: self-test for the server-side identity module
 * (chat_auth.ts). No network, no DB, no secrets read; synthetic secrets only.
 * File writes are confined to a mkdtemp() boot-token store that is removed.
 * Run: npm run test:chat-auth   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createHmac } from "node:crypto";
import { describe, it } from "node:test";
import { mkdtempSync, rmSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  CSRF_HEADER,
  SID_COOKIE,
  checkSessionIssuance,
  consumeBootstrapToken,
  defaultBootFile,
  handleSessionIssuance,
  sessionCookieName,
  TG_SIG_HEADER,
  TG_TS_HEADER,
  TG_UID_HEADER,
  issueDashboardSession,
  parseChatBody,
  readCookies,
  resolveChatIdentity,
  verifyDashboardSession,
  verifyTelegramIdentity,
} from "../chat_auth.ts";
import type { IssuedSession } from "../chat_auth.ts";

const SECRET = "test-gateway-secret-0123456789abcdef";
const ENV = { AHOS_TELEGRAM_GATEWAY_SECRET: SECRET, AHOS_DASHBOARD_SESSION_SECRET: SECRET };
const NO_SECRET_ENV = {};

function bodySha(body: string): string {
  return createHash("sha256").update(body, "utf8").digest("hex");
}

function sign(uid: string, body: string, secret = SECRET, ts = Date.now()): Headers {
  const headers = new Headers();
  const b64 = bodySha(body);
  const sig = createHmac("sha256", secret).update(`${uid}|${ts}|${b64}`, "utf8").digest("hex");
  headers.set(TG_UID_HEADER, uid);
  headers.set(TG_TS_HEADER, String(ts));
  headers.set(TG_SIG_HEADER, sig);
  return headers;
}

describe("telegram HMAC identity", () => {
  it("accepts a correctly signed request", () => {
    const body = '{"message":"سلام"}';
    const r = verifyTelegramIdentity(sign("111", body), bodySha(body), ENV);
    assert.equal(r.ok, true);
    if (r.ok) assert.equal(r.userId, "111");
  });
  it("rejects a signature over a DIFFERENT body (user_id cannot be swapped)", () => {
    const headers = sign("111", '{"message":"الف"}');
    const r = verifyTelegramIdentity(headers, bodySha('{"message":"ب"}'), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_SIGNATURE");
  });
  it("rejects a wrong secret", () => {
    const body = '{"message":"x"}';
    const r = verifyTelegramIdentity(sign("111", body, "other-secret-aaaaaaaaaaaaa"), bodySha(body), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_SIGNATURE");
  });
  it("rejects a replay outside the window", () => {
    const body = '{"message":"x"}';
    const old = Date.now() - 400_000;
    const r = verifyTelegramIdentity(sign("111", body, SECRET, old), bodySha(body), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "TIMESTAMP_OUTSIDE_WINDOW");
  });
  it("rejects a future timestamp", () => {
    const body = '{"message":"x"}';
    const r = verifyTelegramIdentity(sign("111", body, SECRET, Date.now() + 400_000), bodySha(body), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "TIMESTAMP_OUTSIDE_WINDOW");
  });
  it("fails closed when the server secret is missing or short", () => {
    const body = '{"message":"x"}';
    assert.equal(verifyTelegramIdentity(sign("111", body), bodySha(body), NO_SECRET_ENV).ok, false);
    const short = { AHOS_TELEGRAM_GATEWAY_SECRET: "short" };
    assert.equal(verifyTelegramIdentity(sign("111", body), bodySha(body), short).ok, false);
  });
  it("fails closed when the headers are absent", () => {
    const body = '{"message":"x"}';
    const r = verifyTelegramIdentity(new Headers(), bodySha(body), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "NO_HMAC_HEADERS");
  });
  it("rejects a bad timestamp", () => {
    const headers = sign("111", "x");
    headers.set(TG_TS_HEADER, "not-a-number");
    const r = verifyTelegramIdentity(headers, bodySha("x"), ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_TIMESTAMP");
  });
  it("a spoofed uid with a stolen signature still fails the body binding", () => {
    // A signature for uid 111 cannot be replayed as uid 999: the message
    // includes the uid, so the recomputed HMAC differs.
    const body = '{"message":"x"}';
    const headers = sign("111", body);
    headers.set(TG_UID_HEADER, "999");
    const r = verifyTelegramIdentity(headers, bodySha(body), ENV);
    assert.equal(r.ok, false);
  });
});

describe("dashboard session", () => {
  /** What the browser sends: the httpOnly cookie, plus the body-delivered token in the header. */
  function echoHeaders(issued: IssuedSession): Headers {
    const headers = new Headers({ cookie: issued.cookies[0]!.split(";")[0] });
    headers.set(CSRF_HEADER, issued.csrfToken);
    return headers;
  }
  it("issues ONE namespaced httpOnly Strict cookie and a body CSRF token; they verify together", () => {
    const issued = issueDashboardSession(ENV);
    assert.ok(issued);
    if (!issued) return;
    assert.equal(issued.cookies.length, 1, "no readable CSRF cookie any more (F6)");
    const c = issued.cookies[0]!;
    assert.ok(c.startsWith(`${sessionCookieName(SECRET)}=`));
    assert.ok(sessionCookieName(SECRET).startsWith(`${SID_COOKIE}_`));
    assert.ok(c.includes("HttpOnly") && c.includes("SameSite=Strict"));
    const r = verifyDashboardSession(echoHeaders(issued), ENV);
    assert.equal(r.ok, true);
    if (r.ok) assert.equal(r.sessionId, issued.sessionId);
  });
  it("fails closed when the server secret is missing", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    assert.equal(verifyDashboardSession(echoHeaders(issued), NO_SECRET_ENV).ok, false);
    assert.equal(issueDashboardSession(NO_SECRET_ENV), null);
  });
  it("rejects a session cookie with no CSRF header", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const headers = new Headers({ cookie: issued.cookies[0]!.split(";")[0] });
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "NO_CSRF_TOKEN");
  });
  it("rejects a CSRF token carried only in a cookie (no echo header)", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const headers = new Headers({ cookie: `${issued.cookies[0]!.split(";")[0]}; AHOS_CSRF=${issued.csrfToken}` });
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "NO_CSRF_TOKEN");
  });
  it("rejects a CSRF header that is not a signed token", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const headers = echoHeaders(issued);
    headers.set(CSRF_HEADER, issued.csrfToken.split(".")[0]!); // id without signature
    assert.equal(verifyDashboardSession(headers, ENV).ok, false);
  });
  it("rejects a forged session cookie", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const forged = issued.cookies[0]!.split(";")[0]!.replace(/\.[0-9a-f]+$/, "." + "0".repeat(64));
    const headers = echoHeaders(issued);
    headers.set("cookie", forged);
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_SESSION_SIGNATURE");
  });
  it("rejects a CSRF token bound to a different session", () => {
    const a = issueDashboardSession(ENV);
    const b = issueDashboardSession(ENV);
    if (!a || !b) return;
    const headers = new Headers({ cookie: a.cookies[0]!.split(";")[0] });
    headers.set(CSRF_HEADER, b.csrfToken);
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_CSRF_TOKEN");
  });
  it("session ids are unique per issuance", () => {
    const a = issueDashboardSession(ENV);
    const b = issueDashboardSession(ENV);
    if (!a || !b) return;
    assert.notEqual(a.sessionId, b.sessionId);
    assert.notEqual(a.csrfToken, b.csrfToken);
  });
  it("F6: a cookie from another server instance (other secret) or a bare AHOS_SID is never read", () => {
    const other = { AHOS_DASHBOARD_SESSION_SECRET: "another-instance-secret-0123456789" };
    const foreign = issueDashboardSession(other);
    const ours = issueDashboardSession(ENV);
    if (!foreign || !ours) return;
    assert.notEqual(sessionCookieName(SECRET), sessionCookieName(other.AHOS_DASHBOARD_SESSION_SECRET));
    const h1 = new Headers({ cookie: foreign.cookies[0]!.split(";")[0] });
    h1.set(CSRF_HEADER, foreign.csrfToken);
    const r1 = verifyDashboardSession(h1, ENV);
    assert.equal(r1.ok, false);
    if (!r1.ok) assert.equal(r1.reason, "NO_SESSION_COOKIE");
    // A planted cookie under the legacy bare name does not shadow the real one.
    const h2 = new Headers({ cookie: `AHOS_SID=planted; ${ours.cookies[0]!.split(";")[0]}` });
    h2.set(CSRF_HEADER, ours.csrfToken);
    assert.equal(verifyDashboardSession(h2, ENV).ok, true);
  });
});

describe("session issuance: REDTEAM-19 F1 attack reproductions now fail", () => {
  const dir = mkdtempSync(join(tmpdir(), "ahos-boot-"));
  const bootFile = join(dir, "dashboard_boot.json");
  const HOST = "127.0.0.1:3000";
  const shaHex = (s: string) => createHash("sha256").update(s, "utf8").digest("hex");
  /** Same file format the launcher writes (launcher/components.issue_dashboard_boot_token). */
  function plant(token: string, ttlS = 300): void {
    let tokens: unknown[] = [];
    try {
      tokens = (JSON.parse(readFileSync(bootFile, "utf8")) as { tokens: unknown[] }).tokens;
    } catch {
      tokens = [];
    }
    tokens.push({ sha256: shaHex(token), expires_ts: Date.now() / 1000 + ttlS, issued_ts: Date.now() / 1000 });
    writeFileSync(bootFile, JSON.stringify({ version: 1, tokens }));
  }
  function req(headers: Record<string, string>, body?: unknown): Request {
    return new Request(`http://${HOST}/api/auth/session`, {
      method: "POST",
      headers: { host: HOST, ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  }
  const BROWSER = { "sec-fetch-site": "same-origin", origin: `http://${HOST}`, "content-type": "application/json" };
  const issue = (r: Request) => handleSessionIssuance(r, { env: ENV, bootFile });
  const T1 = "a".repeat(64);

  it("plain `curl -X POST /api/auth/session` (no Sec-Fetch-Site, no token) -> 403", async () => {
    plant(T1);
    const r = await issue(req({}));
    assert.equal(r.status, 403);
    assert.equal(r.headers.get("set-cookie"), null);
  });
  it("curl that fakes the browser headers but has no bootstrap token -> 401, no cookie", async () => {
    const r = await issue(req(BROWSER, {}));
    assert.equal(r.status, 401);
    assert.equal(r.headers.get("set-cookie"), null);
    assert.equal(((await r.json()) as { error: string }).error, "BOOTSTRAP_TOKEN_REQUIRED");
  });
  it("spoofed `X-Forwarded-For: 127.0.0.1` grants nothing (no token -> 401; no Sec-Fetch -> 403)", async () => {
    assert.equal((await issue(req({ "x-forwarded-for": "127.0.0.1" }))).status, 403);
    assert.equal((await issue(req({ ...BROWSER, "x-forwarded-for": "127.0.0.1" }, {}))).status, 401);
    assert.equal((await issue(req({ ...BROWSER, "x-forwarded-for": "::1" }, { boot: "f".repeat(64) }))).status, 401);
  });
  it("cross-site Origin / Sec-Fetch-Site are refused even WITH a valid token, and the token survives", async () => {
    const T = "b".repeat(64);
    plant(T);
    for (const h of [
      { "sec-fetch-site": "cross-site", origin: "http://evil.example" },
      { "sec-fetch-site": "same-site", origin: "http://127.0.0.1:8080" }, // another local port
      { "sec-fetch-site": "same-origin", origin: "http://evil.example" },
      { "sec-fetch-site": "same-origin", origin: "http://127.0.0.1:8080" },
      { "sec-fetch-site": "none", origin: "null" },
    ]) {
      const r = await issue(req({ ...h, "content-type": "application/json" }, { boot: T }));
      assert.equal(r.status, 403, JSON.stringify(h));
    }
    const ok = await issue(req(BROWSER, { boot: T }));
    assert.equal(ok.status, 200, "a refused request must not burn the owner's token");
  });
  it("DNS-rebinding Hosts are refused", async () => {
    for (const host of ["evil.example", "evil.example:3000", "127.0.0.1.evil.example", "localhost.evil.example:3000", "0.0.0.0:3000"]) {
      const r = new Request(`http://${HOST}/api/auth/session`, {
        method: "POST",
        headers: { ...BROWSER, host, origin: `http://${host}` },
        body: JSON.stringify({ boot: T1 }),
      });
      assert.equal((await issue(r)).status, 403, host);
    }
  });
  it("the launcher's token mints exactly one session; the CSRF token from the body works", async () => {
    const T = "c".repeat(64);
    plant(T);
    const r = await issue(req(BROWSER, { boot: T }));
    assert.equal(r.status, 200);
    const json = (await r.json()) as { ok: boolean; csrfToken: string };
    assert.equal(json.ok, true);
    const cookie = String(r.headers.get("set-cookie")).split(";")[0]!;
    const h = new Headers({ cookie });
    h.set(CSRF_HEADER, json.csrfToken);
    assert.equal(verifyDashboardSession(h, ENV).ok, true);
    const replay = await issue(req(BROWSER, { boot: T }));
    assert.equal(replay.status, 401, "single use");
  });
  it("Sec-Fetch-Site: none (typed/launcher navigation context) without Origin is accepted with a token", async () => {
    const T = "d".repeat(64);
    plant(T);
    const r = await issue(req({ "sec-fetch-site": "none", "content-type": "application/json" }, { boot: T }));
    assert.equal(r.status, 200);
  });
  it("an expired token is refused and pruned", async () => {
    const T = "e".repeat(64);
    plant(T, -1);
    assert.equal((await issue(req(BROWSER, { boot: T }))).status, 401);
    assert.ok(!readFileSync(bootFile, "utf8").includes(shaHex(T)));
  });
  it("no server secret -> 503 and the token is NOT consumed", async () => {
    const T = "0".repeat(64);
    plant(T);
    const r = await handleSessionIssuance(req(BROWSER, { boot: T }), { env: NO_SECRET_ENV, bootFile });
    assert.equal(r.status, 503);
    assert.ok(readFileSync(bootFile, "utf8").includes(shaHex(T)));
  });
  it("a missing boot store fails closed", () => {
    const r = consumeBootstrapToken("1".repeat(64), { file: join(dir, "absent.json") });
    assert.deepEqual(r, { ok: false, reason: "BOOT_STORE_UNAVAILABLE" });
    assert.equal(existsSync(join(dir, "absent.json")), false);
  });
  it("malformed tokens never touch the store", () => {
    for (const t of [null, 5, "", "short", "Z".repeat(64), "a".repeat(200)]) {
      assert.deepEqual(consumeBootstrapToken(t, { file: bootFile }), { ok: false, reason: "NO_BOOT_TOKEN" });
    }
  });
  it("checkSessionIssuance needs Host + Sec-Fetch-Site and never reads x-forwarded-for", () => {
    assert.equal(checkSessionIssuance(new Request("http://127.0.0.1:3000/x", { method: "POST" })).ok, false);
    const src = readFileSync(new URL("../chat_auth.ts", import.meta.url), "utf8");
    assert.ok(!/headers\.get\(\s*["']x-forwarded-for["']/i.test(src), "no XFF logic left");
    const route = readFileSync(new URL("../app/api/auth/session/route.ts", import.meta.url), "utf8");
    assert.ok(route.includes("handleSessionIssuance(req)"));
    assert.ok(!/x-forwarded-for/i.test(route.replace(/^\s*\*.*$/gm, "")));
  });
  it("boot file default follows AHOS_DASHBOARD_BOOT_FILE, then AHOS_DATA_DIR/launcher", () => {
    assert.equal(defaultBootFile({ AHOS_DASHBOARD_BOOT_FILE: "/x/b.json" }), "/x/b.json");
    assert.equal(defaultBootFile({ AHOS_DATA_DIR: "/d" }), join("/d", "launcher", "dashboard_boot.json"));
  });
  it("cleanup", () => {
    rmSync(dir, { recursive: true, force: true });
  });
});

describe("resolveChatIdentity", () => {
  it("prefers a verified Telegram HMAC", () => {
    const body = '{"message":"x"}';
    const headers = sign("7435", body);
    const id = resolveChatIdentity({ headers, bodySha256: bodySha(body), body: { channel: "web", user_id: "1" }, env: ENV });
    assert.equal(id.channel, "telegram");
    assert.equal(id.userId, "7435");
    assert.equal(id.proven, true);
    assert.equal(id.proof, "telegram_hmac");
  });
  it("falls back to a verified dashboard session", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const headers = new Headers({ cookie: issued.cookies[0]!.split(";")[0] });
    headers.set(CSRF_HEADER, issued.csrfToken);
    const id = resolveChatIdentity({ headers, bodySha256: bodySha("{}"), body: {}, env: ENV });
    assert.equal(id.channel, "dashboard");
    assert.equal(id.proven, true);
    assert.equal(id.proof, "dashboard_session");
  });
  it("an unverified caller keeps its asserted channel and is NOT the owner", () => {
    const id = resolveChatIdentity({
      headers: new Headers(),
      bodySha256: bodySha("{}"),
      body: { channel: "web", user_id: "7435" },
      env: ENV,
    });
    assert.equal(id.channel, "web");
    assert.equal(id.userId, "7435");
    assert.equal(id.proven, false);
    assert.equal(id.proof, "none");
  });
  it("a missing channel stays missing — never defaults to an owner channel", () => {
    const id = resolveChatIdentity({ headers: new Headers(), bodySha256: bodySha("{}"), body: {}, env: ENV });
    assert.equal(id.channel, null);
    assert.equal(id.userId, null);
    assert.equal(id.proven, false);
  });
  it("a bad HMAC and a bad session both land in the diagnostic reason", () => {
    const body = "{}";
    const headers = sign("1", body, "wrong-secret-aaaaaaaaaaaaaa");
    const id = resolveChatIdentity({ headers, bodySha256: bodySha(body), body: {}, env: ENV });
    assert.equal(id.proven, false);
    assert.match(String(id.proofReason), /telegram:BAD_SIGNATURE/);
  });
});

describe("helpers", () => {
  it("parses cookies", () => {
    const m = readCookies("a=1; b=22; c=xyz");
    assert.equal(m.get("a"), "1");
    assert.equal(m.get("b"), "22");
    assert.equal(m.get("c"), "xyz");
    assert.equal(readCookies(null).size, 0);
  });
});

describe("parseChatBody (/api/chat body parsing)", () => {
  it("returns the object for valid JSON", () => {
    assert.deepEqual(parseChatBody('{"message":"راهنما","channel":"dashboard"}'), {
      message: "راهنما",
      channel: "dashboard",
    });
  });
  it("maps malformed JSON, arrays, null and primitives to {} without throwing", () => {
    for (const raw of ["", "{", "not json", "[1,2]", "null", "42", '"s"']) {
      assert.deepEqual(parseChatBody(raw), {}, raw);
    }
  });
  it("the chat route uses it (regression: await JSON.parse(raw).catch threw on every request)", async () => {
    const { readFileSync } = await import("node:fs");
    const src = readFileSync(new URL("../app/api/chat/route.ts", import.meta.url), "utf8");
    assert.ok(src.includes("parseChatBody(raw)"));
    assert.ok(!/JSON\.parse\([^)]*\)\s*\.catch/.test(src));
  });
});
