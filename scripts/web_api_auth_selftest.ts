/**
 * Unit self-test for web_api_auth.ts (no Next server required).
 * Run: npm run test:web-api-auth
 */
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  authorizeWebApi,
  sanitizePublicError,
  webApiGateMode,
} from "../web_api_auth.ts";

const KEYS = [
  "AHOS_WEB_API_TOKEN",
  "AHOS_WEB_API_ALLOW_OPEN_ACCESS",
] as const;

afterEach(() => {
  for (const k of KEYS) delete process.env[k];
});

function req(headers: Record<string, string> = {}): Request {
  return new Request("http://127.0.0.1:3000/api/chat", {
    method: "POST",
    headers,
  });
}

describe("webApiGateMode", () => {
  it("locks when token unset and open access unset", () => {
    assert.equal(webApiGateMode(), "LOCKED_NO_TOKEN");
  });

  it("opens only with explicit opt-in", () => {
    process.env.AHOS_WEB_API_ALLOW_OPEN_ACCESS = "1";
    assert.equal(webApiGateMode(), "OPEN_ACCESS");
  });

  it("restricts when token set", () => {
    process.env.AHOS_WEB_API_TOKEN = "secret-token-value-01";
    process.env.AHOS_WEB_API_ALLOW_OPEN_ACCESS = "1";
    assert.equal(webApiGateMode(), "RESTRICTED");
  });
});

describe("authorizeWebApi", () => {
  it("rejects locked mode with 401", async () => {
    const denied = authorizeWebApi(req());
    assert.ok(denied);
    assert.equal(denied!.status, 401);
    const body = (await denied!.json()) as { error: string };
    assert.equal(body.error, "WEB_API_LOCKED_NO_TOKEN");
  });

  it("allows open access without token", () => {
    process.env.AHOS_WEB_API_ALLOW_OPEN_ACCESS = "true";
    assert.equal(authorizeWebApi(req()), null);
  });

  it("accepts matching Bearer token", () => {
    process.env.AHOS_WEB_API_TOKEN = "secret-token-value-01";
    assert.equal(
      authorizeWebApi(req({ Authorization: "Bearer secret-token-value-01" })),
      null,
    );
  });

  it("accepts matching X-AHOS-Web-Token", () => {
    process.env.AHOS_WEB_API_TOKEN = "secret-token-value-01";
    assert.equal(
      authorizeWebApi(req({ "X-AHOS-Web-Token": "secret-token-value-01" })),
      null,
    );
  });

  it("rejects wrong token", async () => {
    process.env.AHOS_WEB_API_TOKEN = "secret-token-value-01";
    const denied = authorizeWebApi(req({ Authorization: "Bearer wrong" }));
    assert.ok(denied);
    assert.equal(denied!.status, 401);
    const body = (await denied!.json()) as { error: string };
    assert.equal(body.error, "WEB_API_UNAUTHORIZED");
  });
});

describe("sanitizePublicError", () => {
  it("redacts bearer and postgres DSN", () => {
    const msg = sanitizePublicError(
      new Error(
        "Authorization: Bearer abcdefghijklmnop1234 failed postgresql://ahos_user:pass@127.0.0.1:5432/ahos",
      ),
    );
    assert.ok(!msg.includes("abcdefghijklmnop1234"));
    assert.ok(!msg.includes("postgresql://"));
    assert.ok(msg.includes("[REDACTED_SECRET]"));
  });
});
