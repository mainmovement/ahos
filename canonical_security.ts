/**
 * Lane B side-effect gate: consume canonical Python overlay state.
 *
 * This module does not evaluate honeypot/tax/mint/etc. It only accepts the
 * overlay vocabulary (PASS/REJECT/INCOMPLETE/STALE) and allows side effects
 * when the state is exactly PASS. Local TS labels (OBSERVED, UNKNOWN,
 * HONEYPOT, empty) are not substitutes.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import type { PairObservation, SecurityAssessment, ScoredOpportunity } from "./types";

export const CANONICAL_SECURITY_STATES = [
  "PASS",
  "REJECT",
  "INCOMPLETE",
  "STALE",
] as const;
export type CanonicalSecurityState = (typeof CANONICAL_SECURITY_STATES)[number];

export function parseCanonicalSecurityState(
  raw: unknown,
): CanonicalSecurityState | null {
  if (typeof raw !== "string") return null;
  const s = raw.trim().toUpperCase();
  if (s === "PASS" || s === "REJECT" || s === "INCOMPLETE" || s === "STALE") {
    return s;
  }
  return null;
}

export function canonicalSecurityAllowsSideEffect(raw: unknown): boolean {
  return parseCanonicalSecurityState(raw) === "PASS";
}

export function paperOpenDecision(raw: unknown): {
  ok: boolean;
  error?: "SECURITY_GATE";
  canonicalSecurityState: CanonicalSecurityState | "UNAVAILABLE" | "MALFORMED";
} {
  if (raw === undefined || raw === null || raw === "") {
    return {
      ok: false,
      error: "SECURITY_GATE",
      canonicalSecurityState: "UNAVAILABLE",
    };
  }
  const parsed = parseCanonicalSecurityState(raw);
  if (parsed === "PASS") {
    return { ok: true, canonicalSecurityState: "PASS" };
  }
  if (parsed) {
    return { ok: false, error: "SECURITY_GATE", canonicalSecurityState: parsed };
  }
  return {
    ok: false,
    error: "SECURITY_GATE",
    canonicalSecurityState: "MALFORMED",
  };
}

function yn(value: string | null | undefined): boolean | null {
  if (value === "YES") return true;
  if (value === "NO") return false;
  return null;
}

export function assessmentToOverlaySignals(
  security: SecurityAssessment | null | undefined,
  token?: PairObservation | null,
): Record<string, unknown> {
  const sellable = security?.sellable;
  let cannotSell: boolean | null = null;
  if (sellable === "NO") cannotSell = true;
  else if (sellable === "YES") cannotSell = false;
  let ownerRenounced: boolean | null = null;
  if (security?.ownership === "RENOUNCED") ownerRenounced = true;
  else if (security?.ownership === "OPEN") ownerRenounced = false;
  return {
    is_honeypot: yn(security?.honeypot),
    has_mint_authority: yn(security?.mintable),
    has_freeze_authority: yn(security?.freezeable),
    is_ownership_renounced: ownerRenounced,
    cannot_sell_all: cannotSell,
    pair_created_at: token?.pairCreatedAt ?? null,
  };
}

export type OverlayQueryItem = {
  tokenKey: string;
  signals: Record<string, unknown>;
  pair_created_ts: number | null;
  retrieved_ts: number | null;
};

export function opportunityToOverlayItem(
  opp: ScoredOpportunity,
  nowSec: number,
): OverlayQueryItem {
  const pairTs =
    opp.token.pairCreatedAt != null
      ? Date.parse(opp.token.pairCreatedAt) / 1000
      : null;
  const signals = assessmentToOverlaySignals(opp.security, opp.token);
  delete signals.pair_created_at;
  return {
    tokenKey: opp.token.tokenKey,
    signals,
    pair_created_ts: Number.isFinite(pairTs as number) ? (pairTs as number) : null,
    retrieved_ts: nowSec,
  };
}

export type OverlayQueryFn = (
  items: OverlayQueryItem[],
  nowSec: number,
) => Promise<Record<string, string>>;

function pythonBin(): string {
  const venv = path.join(process.cwd(), ".venv", "bin", "python");
  if (existsSync(venv)) return venv;
  return "python3";
}

/** Spawn Lane B overlay_query. Fail closed: errors → empty map (no PASS). */
export function queryPythonOverlayStates(
  items: OverlayQueryItem[],
  nowSec: number,
): Promise<Record<string, string>> {
  if (!items.length) return Promise.resolve({});
  const payload = JSON.stringify({ now: nowSec, tokens: items });
  return new Promise((resolve) => {
    const child = spawn(
      pythonBin(),
      ["-B", "-m", "architecture.security.overlay_query"],
      {
        cwd: process.cwd(),
        stdio: ["pipe", "pipe", "ignore"],
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", PYTHONUNBUFFERED: "1" },
      },
    );
    let stdout = "";
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      resolve({});
    }, 12_000);
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      stdout += chunk;
    });
    child.on("error", () => {
      clearTimeout(timer);
      resolve({});
    });
    child.on("close", () => {
      clearTimeout(timer);
      try {
        const parsed = JSON.parse(stdout) as { states?: Record<string, string> };
        const states = parsed.states;
        if (!states || typeof states !== "object") {
          resolve({});
          return;
        }
        const out: Record<string, string> = {};
        for (const [k, v] of Object.entries(states)) {
          if (typeof v === "string") out[k] = v;
        }
        resolve(out);
      } catch {
        resolve({});
      }
    });
    try {
      child.stdin.write(payload);
      child.stdin.end();
    } catch {
      clearTimeout(timer);
      child.kill("SIGKILL");
      resolve({});
    }
  });
}

export async function attachCanonicalSecurityStates(
  ranked: ScoredOpportunity[],
  query: OverlayQueryFn = queryPythonOverlayStates,
  nowSec: number = Date.now() / 1000,
): Promise<void> {
  const items = ranked.map((opp) => opportunityToOverlayItem(opp, nowSec));
  let states: Record<string, string> = {};
  try {
    states = await query(items, nowSec);
  } catch {
    states = {};
  }
  for (const opp of ranked) {
    const raw = states[opp.token.tokenKey];
    opp.canonicalSecurityState = parseCanonicalSecurityState(raw);
  }
}
