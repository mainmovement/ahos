import fa from "../i18n/fa.json";
import en from "../i18n/en.json";

/** Single source of UI copy: the AHOS content pack (src/i18n/{fa,en}.json). */
export type Lang = "fa" | "en";
const bundles: Record<Lang, unknown> = { fa, en };

/** Dot-path lookup, e.g. tr("fa", "status.UNKNOWN.label"). Falls back to the key's English text, then the key. */
export function tr(lang: Lang, path: string): string {
  for (const l of lang === "fa" ? (["fa", "en"] as const) : (["en"] as const)) {
    let cur: unknown = bundles[l];
    for (const part of path.split(".")) {
      cur = cur && typeof cur === "object" ? (cur as Record<string, unknown>)[part] : undefined;
    }
    if (typeof cur === "string") return cur;
  }
  return path;
}