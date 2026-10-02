/**
 * Shared response composer: the ONE place where chat replies become user text,
 * for every chat surface (Windows dashboard chat via /api/chat `reply`,
 * Telegram via `answer_html`). Pure module: no I/O, no decisions.
 *
 *   verified structured data ──(chat_replies.ts builders)──▶ ReplyBlock[]
 *        ──▶ GroundedDraft ──▶ [optional ReplyPhraser seam] ──▶ ComposedReply
 *
 * Phase 6: the ReplyPhraser seam is filled by gemini_phraser.ts (cloud free
 * tier, key in Windows Credential Manager, read only inside a Python helper).
 * The phraser only *rewrites the grounded draft* in the same style. It is
 * never a source of facts: its output is accepted only if validatePhrased()
 * passes (no new numbers, no internal jargon, length limit, footer kept);
 * otherwise the deterministic draft is used. Locked drafts (e.g. GM-04
 * refusals) are never rephrased.
 */
import {
  REPLY_BUDGET_CHARS,
  TELEGRAM_MAX_CHARS,
  escapeHtml,
  renderPlain,
  renderTelegramHtml,
  type ReplyBlock,
} from "./reply_format";

/** House style, shared by the deterministic composer and any future phraser prompt. */
export const RESPONSE_STYLE_FA: readonly string[] = Object.freeze([
  "فارسی روان، کوتاه و ساختارمند؛ یک عنوان کوتاه، سپس چند خط یا بولت.",
  "اول جواب اصلی (مثلاً قیمت و حال بازار)، بعد جزئیات اختیاری.",
  "هیچ عدد، قیمت یا خبری که در پیش‌نویس نیست اضافه نکن.",
  "داده ناموجود را «نامشخص» یا یک‌بار «داده کافی نیست» بگو؛ حدس نزن.",
  "اصطلاحات داخلی (GM-xx، canonical، کدهای انگلیسی) ممنوع.",
  "ایموجی کم؛ حداکثر یکی در عنوان.",
  "پانویس «تصمیم نهایی با کاربر است.» فقط یک‌بار در انتها.",
  "فقط معامله کاغذی؛ هرگز توصیه خرید واقعی.",
]);

export type GroundedDraft = {
  intent: string;
  /** Deterministic, grounded content (the only source of facts). */
  blocks: ReplyBlock[];
  footer: string;
  /** true = must be shown verbatim (security/control decisions). */
  locked?: boolean;
};

export type PhrasedReply = { plain: string; html?: string | null };

/** Seam for an LLM rewriter (implementation: gemini_phraser.ts). Output is untrusted. */
export interface ReplyPhraser {
  readonly name: string;
  phrase(draft: GroundedDraft, deterministic: { plain: string; html: string }, style: readonly string[]): Promise<PhrasedReply | null>;
}

export type ComposedReply = {
  plain: string;
  html: string;
  /** "deterministic" or the phraser name that produced accepted text. */
  composer: string;
  /** Why a phraser output was rejected (fallback reason), if any. */
  phraserRejected?: string;
};

export function composeDeterministic(draft: GroundedDraft): ComposedReply {
  return {
    plain: renderPlain(draft.blocks, draft.footer, REPLY_BUDGET_CHARS),
    html: renderTelegramHtml(draft.blocks, draft.footer, REPLY_BUDGET_CHARS),
    composer: "deterministic",
  };
}

const JARGON = [/GM-\d/i, /canonical/i, /کانونیکال/, /\bUNKNOWN\b/];
const DIGITS_FA = "۰۱۲۳۴۵۶۷۸۹";
const DIGITS_AR = "٠١٢٣٤٥٦٧٨٩";

function numberTokens(s: string): Set<string> {
  const ascii = String(s ?? "").replace(/[۰-۹٠-٩]/g, (c) => {
    const i = DIGITS_FA.indexOf(c);
    return String(i >= 0 ? i : DIGITS_AR.indexOf(c));
  });
  const out = new Set<string>();
  for (const m of ascii.match(/\d+/g) || []) out.add(m.replace(/^0+(?=\d)/, ""));
  return out;
}

/** Grounding guard for phraser output. Returns null when acceptable, else a reason. */
export function validatePhrased(draftPlain: string, phrased: string, footer: string): string | null {
  const t = String(phrased ?? "").trim();
  if (!t) return "EMPTY";
  if (t.length > TELEGRAM_MAX_CHARS - 96) return "TOO_LONG";
  if (t.split(footer).length - 1 !== 1) return "FOOTER_NOT_EXACTLY_ONCE";
  for (const re of JARGON) if (re.test(t)) return `JARGON:${re.source}`;
  const allowed = numberTokens(draftPlain);
  for (const n of numberTokens(t)) if (!allowed.has(n)) return `NEW_NUMBER:${n}`;
  return null;
}

/**
 * HTML for accepted phrased text. The phrased text is untrusted: every line is
 * escaped; the only markup we add is <b> on a short first line (when a body
 * follows) and <i> on the footer line.
 */
export function phrasedHtml(plain: string, footer: string): string {
  const lines = String(plain ?? "").trim().split("\n");
  const footerLine = `— ${footer}`;
  const isFooter = (l: string) => l.trim() === footerLine || l.trim() === footer;
  const bodyLines = lines.filter((l) => !isFooter(l) && l.trim() !== "");
  return lines
    .map((l, i) => {
      const e = escapeHtml(l);
      if (isFooter(l)) return `<i>${e}</i>`;
      if (i === 0 && bodyLines.length >= 2 && l.trim().length > 0 && l.trim().length <= 60) return `<b>${e}</b>`;
      return e;
    })
    .join("\n");
}

/**
 * Final step for every chat reply. Without a phraser this is exactly
 * composeDeterministic(). Never throws; any phraser failure falls back.
 */
export async function finalizeReply(draft: GroundedDraft, phraser?: ReplyPhraser | null): Promise<ComposedReply> {
  const det = composeDeterministic(draft);
  if (!phraser || draft.locked) return det;
  try {
    const out = await phraser.phrase(draft, { plain: det.plain, html: det.html }, RESPONSE_STYLE_FA);
    if (!out) return { ...det, phraserRejected: "NO_OUTPUT" };
    const reason = validatePhrased(det.plain, out.plain, draft.footer);
    if (reason) return { ...det, phraserRejected: reason };
    // Phrased text is untrusted: any phraser-supplied HTML is ignored and HTML is
    // rebuilt from escaped plain text (phrasedHtml).
    const plain = out.plain.trim();
    return { plain, html: phrasedHtml(plain, draft.footer), composer: phraser.name };
  } catch {
    return { ...det, phraserRejected: "PHRASER_ERROR" };
  }
}
