/**
 * Web opportunity banner gate.
 * Reads the Python/TS alert state file but re-checks the live canonical
 * read model. A stored BUY payload cannot keep the banner hot if identity,
 * overlay, or alerts_allowed later fail closed.
 *
 * Does not mint BUY. Does not treat WATCH/UNKNOWN as an opportunity alert.
 */
import {
  alertsAllowedFromCanonical,
  lookupCanonicalRow,
  type CanonicalReadModel,
} from "./canonical_read_model";
import { canonicalSecurityAllowsSideEffect } from "./canonical_security";

export const WEB_ALERT_HOT_WINDOW_SEC = 180;

export type WebAlertPayload = {
  tokenKey?: unknown;
  symbol?: unknown;
  chain?: unknown;
  address?: unknown;
  decision?: unknown;
  canonicalSecurityState?: unknown;
  disclaimerFa?: unknown;
};

export type WebAlertStateFile = {
  last_alert_at?: unknown;
  last_token?: unknown;
  sent?: unknown;
  last_payload?: WebAlertPayload | null;
};

export type WebAlertBanner = {
  active: boolean;
  reason: string;
  ageSec: number | null;
  lastToken: string | null;
  lastAlertAt: number | null;
  recentCount: number;
  payload: {
    tokenKey: string | null;
    symbol: string | null;
    chain: string | null;
    address: string | null;
    decision: string | null;
    canonicalSecurityState: string | null;
  } | null;
  disclaimerFa: string;
};

const DISCLAIMER_FA =
  "هشدار فرصت پایش است — سیگنال خرید واقعی نیست. PAPER ONLY.";

function asFiniteNumber(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function asText(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const s = v.trim();
  return s ? s : null;
}

function inactive(
  reason: string,
  extra: Partial<WebAlertBanner> = {},
): WebAlertBanner {
  return {
    active: false,
    reason,
    ageSec: extra.ageSec ?? null,
    lastToken: extra.lastToken ?? null,
    lastAlertAt: extra.lastAlertAt ?? null,
    recentCount: extra.recentCount ?? 0,
    payload: extra.payload ?? null,
    disclaimerFa: DISCLAIMER_FA,
  };
}

export function evaluateWebAlertBanner(
  state: WebAlertStateFile | null | undefined,
  model: CanonicalReadModel,
  nowSec = Date.now() / 1000,
  hotWindowSec = WEB_ALERT_HOT_WINDOW_SEC,
): WebAlertBanner {
  const sent =
    state && state.sent && typeof state.sent === "object" && !Array.isArray(state.sent)
      ? Object.keys(state.sent as Record<string, unknown>).length
      : 0;
  const lastAlertAt = asFiniteNumber(state?.last_alert_at);
  const lastToken = asText(state?.last_token);
  const ageSec =
    lastAlertAt != null ? Math.max(0, nowSec - lastAlertAt) : null;
  const raw = state?.last_payload && typeof state.last_payload === "object"
    ? state.last_payload
    : null;
  const payload = raw
    ? {
        tokenKey: asText(raw.tokenKey),
        symbol: asText(raw.symbol),
        chain: asText(raw.chain),
        address: asText(raw.address),
        decision: asText(raw.decision),
        canonicalSecurityState: asText(raw.canonicalSecurityState),
      }
    : null;
  const base = {
    ageSec,
    lastToken,
    lastAlertAt,
    recentCount: sent,
    payload,
  };

  if (lastAlertAt == null || payload == null) {
    return inactive("NO_ALERT_STATE", base);
  }
  if (ageSec == null || ageSec >= hotWindowSec) {
    return inactive("EXPIRED", base);
  }
  if (model.status !== "AVAILABLE") {
    return inactive(
      model.status === "STALE" ? "MODEL_STALE" : "MODEL_UNAVAILABLE",
      base,
    );
  }
  if (!alertsAllowedFromCanonical(model, payload.chain, payload.address)) {
    return inactive("ALERTS_NOT_ALLOWED", base);
  }
  const row = lookupCanonicalRow(model, payload.chain, payload.address);
  if (!row || String(row.outcome || "").toUpperCase() !== "BUY") {
    return inactive("NOT_LIVE_BUY", base);
  }
  if (String(payload.decision || "").toUpperCase() !== "BUY") {
    return inactive("STORED_DECISION_NOT_BUY", base);
  }
  if (!canonicalSecurityAllowsSideEffect(row.security_state)) {
    return inactive("SECURITY_NOT_PASS", base);
  }
  if (!canonicalSecurityAllowsSideEffect(payload.canonicalSecurityState)) {
    return inactive("STORED_SECURITY_NOT_PASS", base);
  }
  return {
    active: true,
    reason: "CANONICAL_BUY_PASS",
    ageSec,
    lastToken,
    lastAlertAt,
    recentCount: sent,
    payload,
    disclaimerFa: DISCLAIMER_FA,
  };
}
