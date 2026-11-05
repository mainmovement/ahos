/**
 * Locale configuration — dependency-free so it can be imported from
 * middleware (edge runtime) as well as server and client components.
 */

export const locales = ["fa", "en"] as const;
export type AppLocale = (typeof locales)[number];

export const defaultLocale: AppLocale = "fa";

export function isLocale(value: string | undefined): value is AppLocale {
  return (locales as readonly string[]).includes(value ?? "");
}

export function dirFor(locale: AppLocale): "rtl" | "ltr" {
  return locale === "fa" ? "rtl" : "ltr";
}

export const localeLabel: Record<AppLocale, string> = {
  fa: "فارسی",
  en: "English",
};

/** Swap the locale segment of an app path, preserving the rest. */
export function localePath(pathname: string, next: AppLocale): string {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length > 0 && isLocale(segments[0])) {
    segments[0] = next;
  } else {
    segments.unshift(next);
  }
  return `/${segments.join("/")}`;
}
