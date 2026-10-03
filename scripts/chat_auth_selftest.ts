/**
 * Mission 9.5: self-test for the server-side identity module (chat_auth.ts).
 * No network, no DB, no file writes, no secrets read. Synthetic secrets only.
 * Run: npm run test:chat-auth   (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createHmac } from "node:crypto";
import { describe, it } from "node:test";
import {
  CSRF_COOKIE,
  CSRF_HEADER,
  SID_COOKIE,
  TG_SIG_HEADER,
  TG_TS_HEADER,
  TG_UID_HEADER,
  issueDashboardSession,
  isLoopbackRequest,
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
  /** The browser echoes the signed cookie VALUE (token + signature) in the header. */
  function echoHeaders(issued: IssuedSession): Headers {
    const sidCookie = issued.cookies.find((c) => c.startsWith(`${SID_COOKIE}=`))!.split(";")[0];
    const csrfCookie = issued.cookies.find((c) => c.startsWith(`${CSRF_COOKIE}=`))!.split(";")[0];
    const csrfValue = csrfCookie.slice(`${CSRF_COOKIE}=`.length);
    const headers = new Headers({ cookie: `${sidCookie}; ${csrfCookie}` });
    headers.set(CSRF_HEADER, csrfValue);
    return headers;
  }
  it("issues a session + CSRF and verifies them together", () => {
    const issued = issueDashboardSession(ENV);
    assert.ok(issued);
    if (!issued) return;
    assert.ok(issued.cookies.length === 2);
    assert.ok(issued.cookies.some((c) => c.startsWith(`${SID_COOKIE}=`) && c.includes("HttpOnly")));
    assert.ok(issued.cookies.some((c) => c.startsWith(`${CSRF_COOKIE}=`) && !c.includes("HttpOnly")));
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
  it("rejects a session cookie with no CSRF token", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const sidCookie = issued.cookies[0]!.split(";")[0];
    const headers = new Headers({ cookie: sidCookie });
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "NO_CSRF_TOKEN");
  });
  it("rejects a CSRF header that is not the signed cookie value", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const headers = echoHeaders(issued);
    headers.set(CSRF_HEADER, issued.csrfToken); // bare token, no signature
    assert.equal(verifyDashboardSession(headers, ENV).ok, false);
  });
  it("rejects a forged session cookie", () => {
    const issued = issueDashboardSession(ENV);
    if (!issued) return;
    const sid = issued.cookies[0]!.split(";")[0];
    const forged = sid.replace(/\.[0-9a-f]+$/, "." + "0".repeat(64));
    const headers = echoHeaders(issued);
    headers.set("cookie", `${forged}; ${issued.cookies[1]!.split(";")[0]}`);
    const r = verifyDashboardSession(headers, ENV);
    assert.equal(r.ok, false);
    if (!r.ok) assert.equal(r.reason, "BAD_SESSION_SIGNATURE");
  });
  it("rejects a CSRF token bound to a different session", () => {
    const a = issueDashboardSession(ENV);
    const b = issueDashboardSession(ENV);
    if (!a || !b) return;
    const sidA = a.cookies[0]!.split(";")[0];
    const csrfB = b.cookies[1]!.split(";")[0];
    const headers = new Headers({ cookie: `${sidA}; ${csrfB}` });
    headers.set(CSRF_HEADER, csrfB.slice(`${CSRF_COOKIE}=`.length));
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
    const sidCookie = issued.cookies.find((c) => c.startsWith(`${SID_COOKIE}=`))!.split(";")[0];
    const csrfCookie = issued.cookies.find((c) => c.startsWith(`${CSRF_COOKIE}=`))!.split(";")[0];
    const headers = new Headers({ cookie: `${sidCookie}; ${csrfCookie}` });
    headers.set(CSRF_HEADER, csrfCookie.slice(`${CSRF_COOKIE}=`.length));
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
  it("loopback check rejects proxies and remote hosts", () => {
    assert.equal(isLoopbackRequest(new Request("http://127.0.0.1:3500/api/chat")), true);
    assert.equal(isLoopbackRequest(new Request("http://localhost:3500/api/chat")), true);
    assert.equal(isLoopbackRequest(new Request("http://192.168.1.5:3500/api/chat")), false);
    const proxied = new Request("http://127.0.0.1:3500/api/chat", {
      headers: { "x-forwarded-for": "10.0.0.1" },
    });
    assert.equal(isLoopbackRequest(proxied), false);
  });
});
