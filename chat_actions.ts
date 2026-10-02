/**
 * Phase 7b: confirm-gated chat commands (OWNER AUTHORITY DECISION 2026-10-02,
 * pending independent review by سپهر / قاسم / رضا).
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
 */
import { randomInt } from "node:crypto";
import { recordControlAudit, type Capability } from "./chat_control_gate";

export type ActionKind = "engine_start" | "engine_stop" | "paper_buy" | "watch_add";

export type ActionParams = {
  symbol?: string | null;
  tokenKey?: string | null;
  chain?: string | null;
  address?: string | null;
  quantity?: number | null;
};

export type Identity = { channel: string | null; userId: string | null };

export type PendingAction = {
  code: string;
  kind: ActionKind;
  params: ActionParams;
  identityKey: string;
  createdAt: number;
  expiresAt: number;
  summaryFa: string;
};

export type PublicPendingAction = { code: string; kind: ActionKind; summaryFa: string; expiresAt: string };

export const ACTION_TTL_MS = 5 * 60 * 1000;
const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

const CAPABILITY: Record<ActionKind, Capability> = {
  engine_start: "ENGINE_CONTROL",
  engine_stop: "ENGINE_CONTROL",
  paper_buy: "PAPER_WRITE",
  watch_add: "WATCH_WRITE",
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
 * Owner authorization (same identities the rest of the system already trusts):
 *  - channel "telegram": user id must be in TELEGRAM_ADMIN_USER_IDS or
 *    TELEGRAM_ALLOWED_CHAT_IDS (the bot's own allowlist; empty → nobody).
 *  - channel "web" (local dashboard, bearer-authorized by authorizeWebApi): owner.
 *  - anything else: not owner.
 * Residual (documented): any AHOS_WEB_API_TOKEN holder can claim these values,
 * which is the same exposure /api/engine already has.
 */
export function isOwner(id: Identity, env: EnvMap = process.env): boolean {
  const ch = String(id.channel ?? "web").toLowerCase();
  if (ch === "telegram") {
    const uid = String(id.userId ?? "").trim();
    if (!uid) return false;
    return ids(env.TELEGRAM_ADMIN_USER_IDS).has(uid) || ids(env.TELEGRAM_ALLOWED_CHAT_IDS).has(uid);
  }
  return ch === "web" || ch === "dashboard";
}

export function identityKey(id: Identity): string {
  return `${String(id.channel ?? "web").toLowerCase()}:${String(id.userId ?? "")}`;
}

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
  }
}

export class PendingActionStore {
  private readonly items = new Map<string, PendingAction>();
  private readonly now: () => number;
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

export function proposalTextFa(a: PendingAction): string {
  return [
    "📝 درخواست شما آماده اجراست (هنوز اجرا نشده):",
    `• ${a.summaryFa}`,
    "",
    `برای اجرا دقیقاً بفرست: تایید ${a.code}`,
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
};

/** Lazily bind the same functions the dashboard routes use (keeps this module DB-free in tests). */
export async function defaultActionDeps(): Promise<ActionDeps> {
  const engine = await import("./engine");
  const canon = await import("./canonical_read_model");
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
  };
}

export type AuditFn = typeof recordControlAudit;

export function auditAction(
  a: { kind: ActionKind },
  decision: "PROPOSED" | "CONFIRMED" | "CANCELLED" | "EXPIRED" | "DENIED" | "FAILED",
  reason: string,
  id: Identity,
  text: string | null,
  audit: AuditFn = recordControlAudit,
): void {
  audit({
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

/** Create a proposal for an owner, or refuse (and audit) for anyone else. */
export function propose(
  store: PendingActionStore,
  kind: ActionKind,
  params: ActionParams,
  id: Identity,
  text: string | null,
  opts: { env?: EnvMap; audit?: AuditFn } = {},
): { ok: true; action: PendingAction } | { ok: false; reason: "NOT_OWNER" | "MISSING_TOKEN" } {
  if (!isOwner(id, opts.env)) {
    auditAction({ kind }, "DENIED", "NOT_OWNER", id, text, opts.audit);
    return { ok: false, reason: "NOT_OWNER" };
  }
  if ((kind === "paper_buy" || kind === "watch_add") && !(params.tokenKey && params.chain && params.symbol)) {
    auditAction({ kind }, "DENIED", "TOKEN_NOT_RESOLVED", id, text, opts.audit);
    return { ok: false, reason: "MISSING_TOKEN" };
  }
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
    auditAction(a, "CANCELLED", "USER_CANCELLED", id, text, audit);
    return { replyFa: `لغو شد: ${a.summaryFa}. هیچ تغییری اعمال نشد.`, executed: false, kind: a.kind };
  }
  const code = parsed.code ?? "";
  const a = store.get(code);
  if (!a || a.identityKey !== identityKey(id)) {
    return { replyFa: "این کد معتبر نیست یا متعلق به شما نیست. هیچ کاری انجام نشد.", executed: false, kind: null };
  }
  if (!isOwner(id, opts.env)) {
    store.take(code);
    auditAction(a, "DENIED", "NOT_OWNER_AT_CONFIRM", id, text, audit);
    return { replyFa: "⛔ اجازه این کار را ندارید. هیچ تغییری اعمال نشد.", executed: false, kind: a.kind };
  }
  if (store.isExpired(a)) {
    store.take(code);
    auditAction(a, "EXPIRED", "CONFIRMATION_EXPIRED", id, text, audit);
    return { replyFa: "این کد منقضی شده است. اگر هنوز لازم است، دوباره درخواست بده. هیچ تغییری اعمال نشد.", executed: false, kind: a.kind };
  }
  store.take(code); // single use, even if execution fails
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
    } else {
      const r = await deps.paperBuy(a.params);
      auditAction(a, r.ok ? "CONFIRMED" : "FAILED", r.ok ? "EXECUTED_VIA_DASHBOARD_PATH" : "PAPER_GATE_DENIED", id, text, audit);
      return { replyFa: (r.ok ? "✅ " : "⛔ ") + r.messageFa, executed: r.ok, kind: a.kind };
    }
    auditAction(a, "CONFIRMED", "EXECUTED_VIA_DASHBOARD_PATH", id, text, audit);
    return { replyFa, executed: true, kind: a.kind };
  } catch {
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
