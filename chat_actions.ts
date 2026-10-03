/**
 * Phase 7b / Mission 9.5: confirm-gated chat commands (OWNER AUTHORITY DECISION
 * 2026-10-02, pending independent review by سپهر / قاسم / رضا).
 *
 * Replaces the blanket GM-04 chat refusal with:
 *   model or whole-message command → PROPOSAL (Persian summary + one-time code,
 *   5 min expiry, bound to the requesting identity) → the owner sends
 *   «تایید <code>» (or presses the dashboard button) → EXECUTED through the same
 *   functions the dashboard buttons use (/api/engine → startEngine/stopEngine,
 *   /api/paper → canonical BUY check + addPaper, /api/watch → addWatch) →
 *   every step appended to the hash-chained control audit.
 *
 * Invariants:
 *  - PAPER_ONLY: the only actions are engine start/stop, paper buy (still
 *    requires a canonical BUY), watchlist add. No live trading, no keys/secrets,
 *    no authority/constitution changes, nothing in Lane A.
 *  - Non-owners are refused (no proposal is created).
 *  - Nothing executes without an explicit whole-message confirmation carrying
 *    the exact code from the same identity before expiry. Codes are single use.
 *  - Free text never executes anything ("stop loss" can at most produce a
 *    proposal, which still needs «تایید <code>»).
 *
 * Mission 9.5 (corrective security, reviews REDTEAM-19 + Agent-16 QA):
 *  - `isOwner` no longer trusts the client-asserted channel/user id. It requires
 *    `identity.proven`: a Telegram HMAC verified by the gateway
 *    (chat_auth.ts, secret AHOS_TELEGRAM_GATEWAY_SECRET) or a verified
 *    dashboard session cookie + CSRF. A bare bearer or a body-asserted
 *    `channel: "web"` is NOT the owner. The `channel` default of "web" is gone.
 *  - Telegram owner = TELEGRAM_ADMIN_USER_IDS only (not the reader allowlist).
 *  - An EXECUTING audit record is written BEFORE the action and a missing record
 *    aborts the action (write-ahead; the audit can no longer be skipped).
 *  - Wrong confirm codes are counted per identity and lock out after 5 tries.
 *  - Paper-buy quantity is capped.
 */
import { randomInt } from "node:crypto";
import { recordControlAudit, sha256Hex, type Capability } from "./chat_control_gate";
import { cleanDevMissionSummary } from "./dev_missions";

export type ActionKind = "engine_start" | "engine_stop" | "paper_buy" | "watch_add" | "dev_mission";

export type ActionParams = {
  symbol?: string | null;
  tokenKey?: string | null;
  chain?: string | null;
  address?: string | null;
  quantity?: number | null;
  /** dev_mission only: the owner-confirmed engineering request summary. */
  missionSummaryFa?: string | null;
};

export type Identity = {
  channel: string | null;
  userId: string | null;
  /**
   * Server-side proof (Mission 9.5): true only for a verified Telegram HMAC or
   * a verified dashboard session. A client-asserted channel is never an owner.
   */
  proven?: boolean;
};

export type PendingAction = {
  code: string;
  kind: ActionKind;
  params: ActionParams;
  identityKey: string;
  createdAt: number;
  expiresAt: number;
  summaryFa: string;
  /** dev_mission: sha256 of the exact summary the owner was shown and confirms. */
  summaryHash: string | null;
};

export type PublicPendingAction = { code: string; kind: ActionKind; summaryFa: string; expiresAt: string };

export const ACTION_TTL_MS = 5 * 60 * 1000;
const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
/** Mission 9.5 m5: a caller who cannot guess the code is locked out. */
export const MAX_WRONG_ATTEMPTS = 5;
export const LOCKOUT_MS = 5 * 60 * 1000;
/** Mission 9.5 m6: paper buys proposed from chat are capped (paper only). */
export const MAX_PAPER_QUANTITY = 1000;
export const MAX_MISSION_SUMMARY_LEN = 280;

const CAPABILITY: Record<ActionKind, Capability> = {
  engine_start: "ENGINE_CONTROL",
  engine_stop: "ENGINE_CONTROL",
  paper_buy: "PAPER_WRITE",
  watch_add: "WATCH_WRITE",
  dev_mission: "MISSION_WRITE",
};

type EnvMap = Record<string, string | undefined>;

function ids(raw: string | undefined): Set<string> {
  return new Set(
    String(raw ?? "")
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean),
  );
}

/**
 * Owner authorization (Mission 9.5 rewrite).
 *
 * Requires `identity.proven` — a server-side proof from chat_auth.ts:
 *  - channel "telegram": the Telegram bot's HMAC over user_id|ts|sha256(body),
 *    verified by the gateway. The user id must then be in
 *    TELEGRAM_ADMIN_USER_IDS (the *admin* list — the chat-reader allowlist
 *    TELEGRAM_ALLOWED_CHAT_IDS no longer grants control). Empty → nobody.
 *  - channel "dashboard": a verified httpOnly session cookie + CSRF header.
 *    The session id is per-browser-session, so two dashboards never share an
 *    identity or a pending code.
 *  - anything else (a body-asserted channel, a bare bearer, a missing channel):
 *    NOT the owner. There is deliberately no default to an owner channel.
 */
export function isOwner(id: Identity, env: EnvMap = process.env): boolean {
  if (!id.proven) return false;
  const ch = String(id.channel ?? "").toLowerCase();
  if (ch === "telegram") {
    const uid = String(id.userId ?? "").trim();
    if (!uid) return false;
    return ids(env.TELEGRAM_ADMIN_USER_IDS).has(uid);
  }
  return ch === "dashboard";
}

export function identityKey(id: Identity): string {
  const ch = String(id.channel ?? "").toLowerCase();
  const uid = String(id.userId ?? "").trim();
  return `${ch}:${uid || "anonymous"}`;
}

/** Persian summary shown to the owner AND stored verbatim (M3/MJ-7: what the
 * owner confirms is exactly what is queued — no hidden tail). */
export function summaryFaFor(kind: ActionKind, p: ActionParams): string {
  const sym = p.symbol ? String(p.symbol).toUpperCase() : "نامشخص";
  switch (kind) {
    case "engine_start":
      return "روشن کردن موتور تحلیل (فقط کاغذی)";
    case "engine_stop":
      return "خاموش کردن موتور تحلیل";
    case "paper_buy":
      return `ثبت خرید کاغذی ${sym}${p.quantity ? ` به مقدار ${p.quantity}` : ""} (فقط اگر حکم سیستم «خرید» باشد)`;
    case "watch_add":
      return `افزودن ${sym} به واچ‌لیست`;
    case "dev_mission": {
      // The FULL cleaned summary is shown, capped at the stored length, so the
      // owner never approves text they did not see.
      const s = String(p.missionSummaryFa ?? "").trim().slice(0, MAX_MISSION_SUMMARY_LEN);
      return `ثبت ماموریت توسعه${s ? `: ${s}` : ""}`;
    }
  }
}

export class PendingActionStore {
  private readonly items = new Map<string, PendingAction>();
  private readonly now: () => number;
  /** Mission 9.5 m5: wrong-code attempts per identity → lockout. */
  private readonly attempts = new Map<string, { wrong: number; lockedUntil: number }>();
  constructor(now: () => number = Date.now) {
    this.now = now;
  }

  private sweep(): void {
    const t = this.now();
    for (const [k, v] of this.items) if (v.expiresAt <= t - ACTION_TTL_MS) this.items.delete(k);
  }

  create(kind: ActionKind, params: ActionParams, id: Identity): PendingAction {
    this.sweep();
    let code = "";
    do {
      code = Array.from({ length: 6 }, () => CODE_ALPHABET[randomInt(CODE_ALPHABET.length)]).join("");
    } while (this.items.has(code));
    const t = this.now();
    const a: PendingAction = {
      code,
      kind,
      params,
      identityKey: identityKey(id),
      createdAt: t,
      expiresAt: t + ACTION_TTL_MS,
      summaryFa: summaryFaFor(kind, params),
      // dev_mission: bind the pending action to the exact summary the owner sees.
      summaryHash: kind === "dev_mission" ? sha256Hex(String(params.missionSummaryFa ?? "").trim()) : null,
    };
    this.items.set(code, a);
    return a;
  }

  get(code: string): PendingAction | undefined {
    return this.items.get(code);
  }

  take(code: string): PendingAction | undefined {
    const a = this.items.get(code);
    if (a) this.items.delete(code);
    return a;
  }

  latestFor(id: Identity): PendingAction | undefined {
    const k = identityKey(id);
    let best: PendingAction | undefined;
    for (const a of this.items.values()) if (a.identityKey === k && (!best || a.createdAt > best.createdAt)) best = a;
    return best;
  }

  isExpired(a: PendingAction): boolean {
    return this.now() >= a.expiresAt;
  }

  isLocked(id: Identity): boolean {
    const s = this.attempts.get(identityKey(id));
    return Boolean(s && s.lockedUntil > this.now());
  }

  /** Register one wrong/expired/mismatched confirm attempt; returns lock state. */
  registerFailure(id: Identity): { locked: boolean; wrong: number } {
    const k = identityKey(id);
    const s = this.attempts.get(k) ?? { wrong: 0, lockedUntil: 0 };
    s.wrong += 1;
    if (s.wrong >= MAX_WRONG_ATTEMPTS) {
      s.lockedUntil = this.now() + LOCKOUT_MS;
      s.wrong = 0; // the lock is the penalty; the counter resets on release
    }
    this.attempts.set(k, s);
    return { locked: s.lockedUntil > this.now(), wrong: s.wrong };
  }

  /** A resolved confirmation clears the counter. */
  registerSuccess(id: Identity): void {
    this.attempts.delete(identityKey(id));
  }
}

/** Whole-message confirmation / cancellation. Anything else returns null. */
export function parseConfirmation(text: string): { op: "confirm" | "cancel"; code: string | null } | null {
  const t = String(text ?? "")
    .normalize("NFKC")
    .replace(/[\u200b-\u200f\u202a-\u202e\u2060\ufeff]/g, "")
    .replace(/\u200c/g, " ")
    .replace(/[.!؟?]+$/g, "")
    .trim();
  const m = t.match(/^(تایید|تأیید|تائید|confirm|yes)\s+([A-Za-z0-9]{6})$/i);
  if (m) return { op: "confirm", code: m[2].toUpperCase() };
  const c = t.match(/^(لغو|کنسل|cancel|انصراف)(?:\s+([A-Za-z0-9]{6}))?$/i);
  if (c) return { op: "cancel", code: c[2] ? c[2].toUpperCase() : null };
  return null;
}

export function toPublic(a: PendingAction): PublicPendingAction {
  return { code: a.code, kind: a.kind, summaryFa: a.summaryFa, expiresAt: new Date(a.expiresAt).toISOString() };
}

export const DEV_MISSION_INTRO_FA =
  "حتماً! من خودم کد نمی‌نویسم، اما این درخواست را می‌توانم به‌عنوان یک ماموریت توسعه برای تیم مهندسی ثبت کنم.";

export function proposalTextFa(a: PendingAction): string {
  const isMission = a.kind === "dev_mission";
  return [
    ...(isMission ? [DEV_MISSION_INTRO_FA, ""] : []),
    isMission ? "📝 این ماموریت توسعه آماده ثبت است (هنوز ثبت نشده):" : "📝 درخواست شما آماده اجراست (هنوز اجرا نشده):",
    `• ${a.summaryFa}`,
    "",
    `برای ثبت: تایید ${a.code}`,
    `برای انصراف: لغو ${a.code}`,
    "این کد ۵ دقیقه اعتبار دارد و فقط یک‌بار قابل استفاده است.",
  ].join("\n");
}

export type ActionDeps = {
  startEngine: () => Promise<unknown>;
  stopEngine: () => Promise<unknown>;
  addWatch: (input: { tokenKey: string; symbol: string; chain: string; address?: string | null; thesisFa?: string }) => Promise<unknown>;
  /** Canonical gate + addPaper, exactly as /api/paper. Returns a Persian result line. */
  paperBuy: (p: ActionParams) => Promise<{ ok: boolean; messageFa: string }>;
  /** Append one QUEUED mission to the hash-chained dev-mission queue. Never executes work. */
  recordDevMission: (input: {
    summaryFa: string;
    confirmCode?: string | null;
    channel: string | null;
    userId: string | null;
  }) => Promise<{ ok: boolean; messageFa: string }>;
};

/** Lazily bind the same functions the dashboard routes use (keeps this module DB-free in tests). */
export async function defaultActionDeps(): Promise<ActionDeps> {
  const engine = await import("./engine");
  const canon = await import("./canonical_read_model");
  const dm = await import("./dev_missions");
  return {
    startEngine: () => engine.startEngine(),
    stopEngine: () => engine.stopEngine(),
    addWatch: (input) =>
      engine.addWatch({ ...input, address: input.address ?? undefined, thesisFa: input.thesisFa ?? "از گفتگو (تأییدشده)" }),
    paperBuy: async (p) => {
      if (!p.tokenKey || !p.symbol || !p.chain) return { ok: false, messageFa: "نماد در فهرست سیستم پیدا نشد؛ خرید کاغذی ثبت نشد." };
      const model = await canon.loadCanonicalReadModel();
      if (!canon.paperAllowedFromCanonical(model, p.chain, p.address || null)) {
        return { ok: false, messageFa: "خرید کاغذی ثبت نشد: فقط وقتی حکم سیستم «خرید» باشد ثبت کاغذی مجاز است." };
      }
      try {
        const row = (await engine.addPaper({
          tokenKey: p.tokenKey,
          symbol: p.symbol,
          chain: p.chain,
          address: p.address ?? undefined,
          quantity: p.quantity ?? undefined,
          thesisFa: "خرید کاغذی از گفتگو (تأییدشده)",
        })) as { id?: number };
        return { ok: true, messageFa: `ثبت شد — فقط کاغذی. شناسه ${row?.id ?? "نامشخص"}. هیچ سفارشی به صرافی نرفت.` };
      } catch (err) {
        if (err instanceof engine.PaperSecurityDenied) return { ok: false, messageFa: "خرید کاغذی ثبت نشد: بررسی امنیت تأیید نشده." };
        return { ok: false, messageFa: "خرید کاغذی ثبت نشد — خطا در ثبت." };
      }
    },
    recordDevMission: async (input) => {
      const summary = String(input.summaryFa ?? "").trim();
      if (!summary) return { ok: false, messageFa: "ماموریت توسعه ثبت نشد: متن درخواست خالی بود." };
      const rec = dm.getDevMissionStore().append({
        summaryFa: summary,
        confirmCode: input.confirmCode ?? null,
        channel: input.channel,
        userId: input.userId,
      });
      if (!rec) return { ok: false, messageFa: "ماموریت توسعه ثبت نشد — خطا در نوشتن فایل صف." };
      return {
        ok: true,
        messageFa: `✅ ماموریت توسعه ثبت شد (شناسه ${rec.id}) و در صف تیم مهندسی است. کاری هنوز انجام نشده است.`,
      };
    },
  };
}

export type AuditFn = typeof recordControlAudit;

export type ConfirmDecision = "PROPOSED" | "CONFIRMED" | "CANCELLED" | "EXPIRED" | "DENIED" | "FAILED" | "EXECUTING";

/**
 * Append one audit record. Returns the record, or null when the sink failed —
 * Mission 9.5 MJ-1: callers must check this and abort an action when the
 * write-ahead record is missing (the audit may no longer be skipped).
 */
export function auditAction(
  a: { kind: ActionKind },
  decision: ConfirmDecision,
  reason: string,
  id: Identity,
  text: string | null,
  audit: AuditFn = recordControlAudit,
): ReturnType<AuditFn> {
  return audit({
    surface: "chat_confirm",
    intent: a.kind,
    capability: CAPABILITY[a.kind],
    decision,
    reason,
    channelClaimed: id.channel,
    userId: id.userId,
    text,
  });
}

/** Clamp a paper-buy quantity proposed from chat (paper only, m6). */
function clampQuantity(q: number | null | undefined): number | null {
  if (q == null || !Number.isFinite(q)) return null;
  if (q <= 0) return null;
  return Math.min(q, MAX_PAPER_QUANTITY);
}

/** Audit a confirm-path denial when no pending action could be resolved (so the
 * honest intent is `confirm`, not a guessed action kind). */
function auditConfirmDenial(
  reason: string,
  id: Identity,
  text: string | null,
  audit: AuditFn | undefined,
): void {
  if (!audit) return;
  audit({
    surface: "chat_confirm",
    intent: "confirm",
    capability: null,
    decision: "DENIED",
    reason,
    channelClaimed: id.channel,
    userId: id.userId,
    text,
  });
}

/** Create a proposal for an owner, or refuse (and audit) for anyone else. */
export function propose(
  store: PendingActionStore,
  kind: ActionKind,
  params: ActionParams,
  id: Identity,
  text: string | null,
  opts: { env?: EnvMap; audit?: AuditFn } = {},
): { ok: true; action: PendingAction } | { ok: false; reason: "NOT_OWNER" | "MISSING_TOKEN" | "EMPTY_SUMMARY" } {
  if (!isOwner(id, opts.env)) {
    auditAction({ kind }, "DENIED", "NOT_OWNER", id, text, opts.audit);
    return { ok: false, reason: "NOT_OWNER" };
  }
  if ((kind === "paper_buy" || kind === "watch_add") && !(params.tokenKey && params.chain && params.symbol)) {
    auditAction({ kind }, "DENIED", "TOKEN_NOT_RESOLVED", id, text, opts.audit);
    return { ok: false, reason: "MISSING_TOKEN" };
  }
  // M3/MJ-7: clean and redact the mission summary at proposal time, so the text
  // the owner reads in the proposal is byte-for-byte the text that will be
  // queued, and a hidden tail can never ride past the confirmation.
  if (kind === "dev_mission") {
    const cleaned = cleanDevMissionSummary(params.missionSummaryFa);
    if (!cleaned) {
      auditAction({ kind }, "DENIED", "EMPTY_SUMMARY", id, text, opts.audit);
      return { ok: false, reason: "EMPTY_SUMMARY" };
    }
    params = { ...params, missionSummaryFa: cleaned };
  }
  if (kind === "paper_buy") params = { ...params, quantity: clampQuantity(params.quantity) };
  const action = store.create(kind, params, id);
  auditAction(action, "PROPOSED", "OWNER_PROPOSAL_AWAITING_CONFIRMATION", id, text, opts.audit);
  return { ok: true, action };
}

/** Handle «تایید CODE» / «لغو [CODE]». Returns Persian reply text, never throws. */
export async function handleConfirmation(
  store: PendingActionStore,
  parsed: { op: "confirm" | "cancel"; code: string | null },
  id: Identity,
  text: string,
  opts: { env?: EnvMap; audit?: AuditFn; deps?: ActionDeps } = {},
): Promise<{ replyFa: string; executed: boolean; kind: ActionKind | null }> {
  const audit = opts.audit;
  if (parsed.op === "cancel") {
    const a = parsed.code ? store.get(parsed.code) : store.latestFor(id);
    if (!a || a.identityKey !== identityKey(id)) return { replyFa: "درخواست در انتظاری برای لغو پیدا نشد.", executed: false, kind: null };
    store.take(a.code);
    store.registerSuccess(id);
    auditAction(a, "CANCELLED", "USER_CANCELLED", id, text, audit);
    return { replyFa: `لغو شد: ${a.summaryFa}. هیچ تغییری اعمال نشد.`, executed: false, kind: a.kind };
  }
  // Mission 9.5 m5: a locked-out identity gets no hints about pending codes.
  if (store.isLocked(id)) {
    auditConfirmDenial("RATE_LIMIT_LOCKED_OUT", id, text, audit);
    return { replyFa: "به دلیل تلاش‌های ناموفق مکرر، تأییدها برای شما موقتاً مسدود شد. کمی بعد دوباره درخواست بده. هیچ تغییری اعمال نشد.", executed: false, kind: null };
  }
  const code = parsed.code ?? "";
  const a = store.get(code);
  if (!a || a.identityKey !== identityKey(id)) {
    const f = store.registerFailure(id);
    auditConfirmDenial(f.locked ? "RATE_LIMIT_LOCKED_OUT" : "UNKNOWN_OR_FOREIGN_CODE", id, text, audit);
    return { replyFa: "این کد معتبر نیست یا متعلق به شما نیست. هیچ کاری انجام نشد.", executed: false, kind: null };
  }
  if (!isOwner(id, opts.env)) {
    store.take(code);
    store.registerFailure(id);
    auditAction(a, "DENIED", "NOT_OWNER_AT_CONFIRM", id, text, audit);
    return { replyFa: "⛔ اجازه این کار را ندارید. هیچ تغییری اعمال نشد.", executed: false, kind: a.kind };
  }
  if (store.isExpired(a)) {
    store.take(code);
    store.registerFailure(id);
    auditAction(a, "EXPIRED", "CONFIRMATION_EXPIRED", id, text, audit);
    return { replyFa: "این کد منقضی شده است. اگر هنوز لازم است، دوباره درخواست بده. هیچ تغییری اعمال نشد.", executed: false, kind: a.kind };
  }
  store.take(code); // single use, even if execution fails
  // Mission 9.5 MJ-1: write an EXECUTING record FIRST. If the audit cannot be
  // written, the action does not run — an un-audited execution is refused.
  if (!auditAction(a, "EXECUTING", "AUDIT_WRITE_AHEAD", id, text, audit)) {
    auditAction(a, "FAILED", "AUDIT_WRITE_AHEAD_FAILED", id, text, audit);
    return { replyFa: "ثبت امنیتی این عملیات نوشته نشد؛ اجرا متوقف شد. هیچ تغییری اعمال نشده و این کد باطل شد.", executed: false, kind: a.kind };
  }
  try {
    const deps = opts.deps ?? (await defaultActionDeps());
    let replyFa = "";
    if (a.kind === "engine_start") {
      await deps.startEngine();
      replyFa = "✅ موتور تحلیل روشن شد (فقط کاغذی).";
    } else if (a.kind === "engine_stop") {
      await deps.stopEngine();
      replyFa = "✅ موتور تحلیل خاموش شد.";
    } else if (a.kind === "watch_add") {
      await deps.addWatch({
        tokenKey: String(a.params.tokenKey),
        symbol: String(a.params.symbol),
        chain: String(a.params.chain),
        address: a.params.address ?? null,
      });
      replyFa = `✅ ${String(a.params.symbol).toUpperCase()} به واچ‌لیست اضافه شد.`;
    } else if (a.kind === "dev_mission") {
      // Not an execution: one QUEUED line is appended to the hash-chained queue.
      const r = await deps.recordDevMission({
        summaryFa: String(a.params.missionSummaryFa ?? ""),
        confirmCode: a.code,
        channel: id.channel,
        userId: id.userId,
      });
      if (r.ok) store.registerSuccess(id);
      else store.registerFailure(id);
      auditAction(a, r.ok ? "CONFIRMED" : "FAILED", r.ok ? "MISSION_QUEUED" : "QUEUE_WRITE_FAILED", id, text, audit);
      return { replyFa: (r.ok ? "" : "⛔ ") + r.messageFa, executed: r.ok, kind: a.kind };
    } else {
      const r = await deps.paperBuy(a.params);
      if (r.ok) store.registerSuccess(id);
      auditAction(a, r.ok ? "CONFIRMED" : "FAILED", r.ok ? "EXECUTED_VIA_DASHBOARD_PATH" : "PAPER_GATE_DENIED", id, text, audit);
      return { replyFa: (r.ok ? "✅ " : "⛔ ") + r.messageFa, executed: r.ok, kind: a.kind };
    }
    store.registerSuccess(id);
    auditAction(a, "CONFIRMED", "EXECUTED_VIA_DASHBOARD_PATH", id, text, audit);
    return { replyFa, executed: true, kind: a.kind };
  } catch {
    store.registerFailure(id);
    auditAction(a, "FAILED", "EXECUTION_ERROR", id, text, audit);
    return { replyFa: "اجرای درخواست با خطا روبه‌رو شد. وضعیت را از داشبورد بررسی کن.", executed: false, kind: a.kind };
  }
}

/** Process-wide store (in memory; a gateway restart drops pending proposals — safe default). */
let defaultStore: PendingActionStore | null = null;
export function getPendingStore(): PendingActionStore {
  if (!defaultStore) defaultStore = new PendingActionStore();
  return defaultStore;
}
