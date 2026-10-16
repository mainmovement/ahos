/**
 * Persian labels for the venue's vocabulary.
 *
 * Note what is *absent*: there is no word for buying or selling anywhere in this
 * file. A side is reported as بلند/کوتاه (a position direction), never as an
 * instruction, and the activity log speaks of گشایش/بستن کاغذی — paper events
 * that already happened. `findForbiddenControl()` guards the rendering path.
 */

import type { FillAction, PositionSide } from "./model";

/** طرف موقعیت — a direction, never an order. */
export const SIDE_FA: Record<PositionSide, string> = {
  LONG: "بلند",
  SHORT: "کوتاه",
};

/** رخداد دفتر کاغذی — past-tense paper events. */
export const ACTION_FA: Record<FillAction, string> = {
  PAPER_OPEN: "گشایش کاغذی",
  PAPER_CLOSE: "بستن کاغذی",
  PAPER_PARTIAL_CLOSE: "بستن جزئی کاغذی",
  PAPER_ADJUST: "تعدیل کاغذی",
  PAPER_MARK: "نشانه‌گذاری",
  SYSTEM_NOTE: "یادداشت سیستم",
};

export const TABLE_LABELS = {
  symbol: "نماد",
  side: "طرف",
  qty: "مقدار",
  entry: "ورود",
  mark: "نشانه",
  unrealized: "نتیجهٔ باز",
  paperAllowed: "مجوز کاغذی",
  evidence: "شناسهٔ شاهد",
  status: "وضعیت",
  source: "منبع",
  updated: "آخرین به‌روزرسانی",
  actions: "کارها",
  time: "زمان (تهران)",
  action: "رخداد",
  price: "قیمت",
  notional: "ارزش اسمی",
  note: "یادداشت",
} as const;

/** Column help texts (hover titles) — plain language, no promises. */
export const COLUMN_HINTS = {
  unrealized: "عدد خنثی؛ این صفحه سود و زیان را خوب/بد رنگ نمی‌کند.",
  mark: "آخرین مقدار خوانده‌شده برای نشانه‌گذاری موقعیت کاغذی.",
  paperAllowed: "اگر مجوز کاغذی نباشد، ردیف «غیرمجاز» است و در هیچ جمعی نمی‌آید.",
  evidence: "شناسهٔ شاهد فقط خواندنی است؛ با «بازکردن شاهد» جزئیات دیده می‌شود.",
} as const;

export const READ_ONLY_FA = "فقط خواندنی";
export const EXPORT_FA = "خروجی CSV";
export const EXPORT_NOTE_FA = "خروجی فقط از دادهٔ نمایشی ساخته می‌شود و برچسب DEMO دارد.";
export const NO_RANKING_FA =
  "این میز معامله‌ها را رتبه‌بندی نمی‌کند و سود/زیان را خوب یا بد رنگ نمی‌کند.";
