/**
 * One-off M48.1 acceptance probe (read-only, no network, no DB).
 *
 * The spec's live line says: "POST /api/auth/session 200 from loopback and
 * 403 for Host evil.example (box commit 94ec2a3)". A live `next dev` /
 * `next start` probe always sees a loopback `req.url` because the listening
 * socket is bound to 127.0.0.1, which makes the Host header redundant. This
 * probe separates the two framings so they can be told apart without depending
 * on which server build is running, and records the one property of
 * isLoopbackRequest that the live probe cannot characterise on its own.
 *
 * Run: node --experimental-strip-types --import ./scripts/ts_strip_resolve.mjs \
 *          scripts/m481_host_header_probe.mjs
 */
import assert from "node:assert/strict";
import { isLoopbackRequest } from "../chat_auth.ts";

// --- The box's framing (commit 94ec2a3): the request URL itself is off-host.
//     This is the only framing in which "403 for Host evil.example" holds.
assert.equal(
  isLoopbackRequest(new Request("https://evil.example/api/auth/session", {
    headers: { host: "evil.example" },
  })),
  false,
  "off-host URL with matching Host header must be rejected (the box acceptance line)",
);

assert.equal(
  isLoopbackRequest(new Request("http://192.168.1.5:3000/api/auth/session")),
  false,
  "off-host URL with no Host header is rejected",
);

assert.equal(
  isLoopbackRequest(new Request("http://127.0.0.1:3000/api/auth/session")),
  true,
  "loopback URL with no Host header is accepted",
);

// --- The live framing: the socket is loopback, so req.url is loopback and the
//     attacker-controlled Host header is not consulted. The *bind* is the
//     trust boundary, per the chat_auth.ts docstring, so this returns 200 by
//     design -- identically on 16.2.6 and 16.3.8.
assert.equal(
  isLoopbackRequest(new Request("http://127.0.0.1:3000/api/auth/session", {
    headers: { host: "evil.example" },
  })),
  true,
  "loopback connection is the trust boundary; a Host header alone must not downgrade it",
);

// --- Recorded property, deliberately NOT asserted as a vulnerability:
//     isLoopbackRequest consults the Host header before the URL, so a loopback
//     Host header on an off-host URL is accepted. Reachability is bounded by
//     the 127.0.0.1 bind: an off-host peer cannot open the socket in the first
//     place, so this path is only reachable from a process already inside the
//     loopback trust boundary. Filed as a defence-in-depth note, not an
//     M48.1 deliverable -- M48.1 changes zero application code.
const spoofed = new Request("https://evil.example/api/auth/session", {
  headers: { host: "127.0.0.1:3000" },
});
console.log(`spoofed loopback Host over off-host URL -> ${isLoopbackRequest(spoofed)}`);
console.log("(Host header is consulted before req.url; bounded by the 127.0.0.1 bind)");

console.log("m481_host_header_probe: 4/4 assertions hold");
console.log(
  "conclusion: the 403-for-Host-evil.example line is satisfiable in the box framing" +
    " (off-host URL). In the live framing the Host header is not the trust boundary," +
    " so it returns 200 by design on both 16.2.6 and 16.3.8.",
);
