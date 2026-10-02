/**
 * Presentation-only reply formatting for chat / Telegram.
 *
 * A reply is a small list of blocks rendered two ways:
 *  - renderPlain(): plain text (dashboard chat, Telegram fallback)
 *  - renderTelegramHtml(): Telegram parse_mode=HTML with every dynamic value escaped
 *
 * Never invents data: blocks carry only what the caller passes. Pure module
 * (no I/O) so it is unit-testable with node --experimental-strip-types.
 */

export const TELEGRAM_MAX_CHARS = 4096;
/** Room for the footer the Python edge may append and for safety. */
export const REPLY_BUDGET_CHARS = 3600;

export type ReplyLink = { label: string; url: string };

export type ReplyBlock =
  | { kind: "title"; text: string }
  | { kind: "line"; text: string }
  | { kind: "bullet"; text: string; link?: ReplyLink | null }
  | { kind: "note"; text: string }
  | { kind: "gap" };

export const title = (text: string): ReplyBlock => ({ kind: "title", text });
export const line = (text: string): ReplyBlock => ({ kind: "line", text });
export const bullet = (text: string, link?: ReplyLink | null): ReplyBlock => ({ kind: "bullet", text, link: link ?? null });
export const note = (text: string): ReplyBlock => ({ kind: "note", text });
export const gap = (): ReplyBlock => ({ kind: "gap" });

/** Telegram HTML escaping: &, <, > (and " for attribute values). */
export function escapeHtml(s: string): string {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Only http(s) links are rendered as links; anything else is dropped. */
export function safeUrl(url: string | null | undefined): string | null {
  const u = String(url ?? "").trim();
  if (!/^https?:\/\/[^\s<>"]+$/i.test(u) || u.length > 500) return null;
  return u;
}

function clean(s: string): string {
  return String(s ?? "").replace(/[\r\t]+/g, " ").replace(/ {2,}/g, " ").trim();
}

function plainBlock(b: ReplyBlock): string {
  switch (b.kind) {
    case "title":
      return clean(b.text);
    case "line":
      return clean(b.text);
    case "note":
      return `ℹ️ ${clean(b.text)}`;
    case "gap":
      return "";
    case "bullet": {
      const url = safeUrl(b.link?.url);
      return `• ${clean(b.text)}${url ? `\n  ${url}` : ""}`;
    }
  }
}

function htmlBlock(b: ReplyBlock): string {
  switch (b.kind) {
    case "title":
      return `<b>${escapeHtml(clean(b.text))}</b>`;
    case "line":
      return escapeHtml(clean(b.text));
    case "note":
      return `<i>${escapeHtml(clean(b.text))}</i>`;
    case "gap":
      return "";
    case "bullet": {
      const url = safeUrl(b.link?.url);
      const label = clean(b.link?.label || "");
      const link = url ? ` — <a href="${escapeHtml(url)}">${escapeHtml(label || "لینک")}</a>` : label ? ` — ${escapeHtml(label)}` : "";
      return `• ${escapeHtml(clean(b.text))}${link}`;
    }
  }
}

function joinWithinBudget(parts: string[], budget: number, more: string): string {
  const out: string[] = [];
  let used = 0;
  for (let i = 0; i < parts.length; i++) {
    const add = parts[i].length + (out.length ? 1 : 0);
    if (used + add > budget) {
      out.push(more);
      break;
    }
    out.push(parts[i]);
    used += add;
  }
  // collapse runs of empty lines and trim edges
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/**
 * Whole blocks only are kept (never cut inside an HTML tag or entity), so the
 * HTML stays well-formed even when the budget is hit.
 */
export function renderPlain(blocks: ReplyBlock[], footer?: string, budget = REPLY_BUDGET_CHARS): string {
  const body = joinWithinBudget(blocks.map(plainBlock), budget, "…");
  return footer ? `${body}\n\n— ${footer}` : body;
}

export function renderTelegramHtml(blocks: ReplyBlock[], footer?: string, budget = REPLY_BUDGET_CHARS): string {
  const body = joinWithinBudget(blocks.map(htmlBlock), budget, "…");
  return footer ? `${body}\n\n<i>— ${escapeHtml(footer)}</i>` : body;
}

/** Wrap legacy multi-line text as blocks (each line kept, "• " lines become bullets). */
export function blocksFromText(text: string): ReplyBlock[] {
  return String(text ?? "")
    .split("\n")
    .map((l) => l.trim())
    .map((l) => (l === "" ? gap() : l.startsWith("• ") ? bullet(l.slice(2)) : line(l)));
}

/** True when most letters are Persian/Arabic script (used to avoid half-translated titles). */
export function isMostlyPersian(s: string, threshold = 0.6): boolean {
  const letters = String(s ?? "").match(/[A-Za-z\u0600-\u06FF]/g) || [];
  if (letters.length < 3) return false;
  const fa = letters.filter((c) => /[\u0600-\u06FF]/.test(c)).length;
  return fa / letters.length >= threshold;
}

/** Relative age in Persian, or null when the timestamp is missing/invalid. */
export function faAge(at: string | Date | null | undefined, now: Date = new Date()): string | null {
  if (!at) return null;
  const t = at instanceof Date ? at.getTime() : Date.parse(String(at));
  if (!Number.isFinite(t)) return null;
  const mins = Math.max(0, Math.round((now.getTime() - t) / 60000));
  const fa = (n: number) => new Intl.NumberFormat("fa-IR").format(n);
  if (mins < 1) return "همین الان";
  if (mins < 60) return `${fa(mins)} دقیقه پیش`;
  const h = Math.round(mins / 60);
  if (h < 48) return `${fa(h)} ساعت پیش`;
  return `${fa(Math.round(h / 24))} روز پیش`;
}
