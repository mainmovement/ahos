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

export function numberTokens(s: string): Set<string> {
  const ascii = String(s ?? "").replace(/[۰-۹٠-٩]/g, (c) => {
    const i = DIGITS_FA.indexOf(c);
    return String(i >= 0 ? i : DIGITS_AR.indexOf(c));
  });
  const out = new Set<string>();
  for (const m of ascii.match(/\d+/g) || []) out.add(m.replace(/^0+(?=\d)/, ""));
  return out;
}

/**
 * Mission 9.6 (MJ-11): the ordered sequence of digit tokens, Persian/Arabic
 * digits normalized. Used as an ordered-subsequence check so a phraser cannot
 * swap two numbers between assets even when both appear somewhere in the draft.
 */
export function numberSequence(s: string): string[] {
  const ascii = String(s ?? "").replace(/[۰-۹٠-٩]/g, (c) => {
    const i = DIGITS_FA.indexOf(c);
    return String(i >= 0 ? i : DIGITS_AR.indexOf(c));
  });
  return (ascii.match(/\d+(?:[.,]\d+)?/g) || []).map((m) => m.replace(/^0+(?=\d)/, ""));
}

/** Direction vocabulary the phraser must not invent or flip. Mapped to a
 * polarity class so a rewording may swap synonyms (صعودی ↔ رشد) but may never
 * change the polarity (صعودی ↔ نزولی). */
const DIRECTION_UP = ["رو به بالا", "صعودی", "مثبت", "رشد", "افزایش", "صعود"];
const DIRECTION_DOWN = ["رو به پایین", "نزولی", "منفی", "افت", "کاهش", "نزول"];
const DIRECTION_WORDS = [...DIRECTION_UP, ...DIRECTION_DOWN];
/** Negation markers that flip a direction word's meaning within a segment. */
const NEGATION_WORDS = [
  "نداشت",
  "ندارند",
  "نشده",
  "نشده‌اند",
  "نشست",
  "نیست",
  "نیستند",
  "نمی",
  "بدون",
  "هرگز",
];
// Persian word edges: \b is ASCII-only, so use script-aware lookarounds.
const EDGE = "(?<![؀-ۿ])";
const NO_EDGE = "(?![؀-ۿ])";
const DIRECTION_RE = new RegExp(
  `${EDGE}(?:${DIRECTION_WORDS.join("|")})${NO_EDGE}`,
  "gu",
);
const NEGATION_RE = new RegExp(
  `${EDGE}(?:${NEGATION_WORDS.join("|")})${NO_EDGE}`,
  "gu",
);

/** Buy/sell imperatives: a phraser may never add trading advice. */
const BUY_ADVICE_RE =
  /(?:بخر|بفروش|بخرید|بفروشید|خرید کن|فروش کن|توصیه می‌کنم|پیشنهاد می‌کنم|الان بخر|اکنون بخر)/u;

/** Split Persian/English text into segments (lines and sentence punctuation). */
function segments(s: string): string[] {
  return String(s ?? "")
    .split(/[\n۔.،؛؟!?]+/u)
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

function multiset<T>(items: Iterable<T>): Map<T, number> {
  const m = new Map<T, number>();
  for (const i of items) m.set(i, (m.get(i) ?? 0) + 1);
  return m;
}

/** True when `sub` is a sub-multiset of `sup` (every item count is covered). */
function coveredBy<T>(sub: Map<T, number>, sup: Map<T, number>): boolean {
  for (const [k, n] of sub) if ((sup.get(k) ?? 0) < n) return false;
  return true;
}

/** Polarity token for one direction word: "UP"/"DOWN", prefixed with "NEG:" when
 * a negation marker sits within 18 chars before OR after the word. The word is
 * kept alongside so a rejection can name the offending phrase. */
type DirToken = { token: string; word: string; negated: boolean };

/** `search()` rather than `test()`: NEGATION_RE is global, and a global regex's
 * `lastIndex` would otherwise leak from one segment into the next. */
function hasNegation(s: string): boolean {
  return String(s ?? "").search(NEGATION_RE) >= 0;
}

function directionTokens(seg: string): DirToken[] {
  const out: DirToken[] = [];
  for (const m of seg.matchAll(DIRECTION_RE)) {
    const w = m[0];
    const cls = DIRECTION_UP.includes(w) ? "UP" : "DOWN";
    const start = m.index ?? 0;
    const before = seg.slice(Math.max(0, start - 18), start);
    const after = seg.slice(start + w.length, start + w.length + 18);
    const negated = hasNegation(before) || hasNegation(after);
    out.push({ token: negated ? `NEG:${cls}` : cls, word: w, negated });
  }
  return out;
}

/** True when `seq` appears in `hay` as an ordered subsequence. */
function subsequenceOf(seq: string[], hay: string[]): boolean {
  let i = 0;
  for (const v of hay) {
    if (i < seq.length && v === seq[i]) i++;
  }
  return i >= seq.length;
}

/**
 * Ordered grounding guard for phraser output. Returns null when acceptable, else
 * a reason. The phraser may reword, drop, split or reorder lines, but it may never:
 *   - invent a number (global membership) or reorder numbers within a segment
 *     (per-segment ordered subsequence),
 *   - attach one asset's number to another asset's direction: each phrased
 *     segment's numbers and direction polarities must be covered by a single
 *     draft segment (the review's swap/flip attack),
 *   - flip a polarity via a negation (a negated direction is its own token),
 *   - add buy/sell advice.
 * Conservative by design: a merge the guard cannot verify is rejected and the
 * grounded deterministic draft is shown instead.
 */
export function validatePhrased(draftPlain: string, phrased: string, footer: string): string | null {
  const t = String(phrased ?? "").trim();
  if (!t) return "EMPTY";
  if (t.length > TELEGRAM_MAX_CHARS - 96) return "TOO_LONG";
  if (t.split(footer).length - 1 !== 1) return "FOOTER_NOT_EXACTLY_ONCE";
  for (const re of JARGON) if (re.test(t)) return `JARGON:${re.source}`;
  if (BUY_ADVICE_RE.test(t)) return "BUY_ADVICE";
  // No number may appear that the draft does not contain somewhere.
  const allowed = numberTokens(draftPlain);
  for (const n of numberTokens(t)) if (!allowed.has(n)) return `NEW_NUMBER:${n}`;
  // Per-segment coverage: the numbers of a phrased segment must be an ordered
  // subsequence of one draft segment's numbers, and its direction polarities
  // must be covered by the same draft segment.
  const draftSegs = segments(draftPlain).map((s) => {
    const dt = directionTokens(s);
    return { nums: numberSequence(s), dirs: multiset(dt.map((d) => d.token)) };
  });
  for (const seg of segments(t)) {
    const dt = directionTokens(seg);
    const nums = numberSequence(seg);
    if (nums.length === 0 && dt.length === 0) continue;
    // Step 1: the numbers must be an ordered subsequence of some draft segment.
    // If none covers them, that is the reason — otherwise the numbers are fine and
    // any rejection below is about direction, not about the numbers.
    const cover = draftSegs.filter((d) => subsequenceOf(nums, d.nums));
    if (cover.length === 0) {
      if (nums.length) return `SEGMENT_NUMBERS_NOT_GROUNDED:${nums.join(",")}`;
      return `DIRECTION_NOT_GROUNDED:${dt.map((d) => d.word).join(",")}`;
    }
    // Step 2: in one of those covering segments, every direction polarity must be
    // present (a flip or an added negation is its own token and so is uncovered).
    if (!cover.some((d) => coveredBy(multiset(dt.map((x) => x.token)), d.dirs))) {
      return `DIRECTION_NOT_GROUNDED:${dt.map((d) => (d.negated ? "NEG:" : "") + d.word).join(",")}`;
    }
  }
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
