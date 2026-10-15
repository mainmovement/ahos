"use client";

import { useCallback, useMemo } from "react";
import { useSettings } from "@/lib/settings/provider";
import type { Localized } from "@/lib/api/types";
import { en } from "./en";
import { fa, type Dict } from "./fa";

const DICTS = { fa, en } as const;

export interface I18n {
  locale: "fa" | "en";
  dir: "rtl" | "ltr";
  t: Dict;
  /** Pick the current-locale string from a Localized pair. */
  l: (value: Localized | null | undefined) => string;
  /** Inline bilingual copy: tx("فارسی", "English"). */
  tx: (faText: string, enText: string) => string;
}

export function useI18n(): I18n {
  const { settings, dir } = useSettings();
  const locale = settings.locale;
  const l = useCallback((value: Localized | null | undefined) => (value ? value[locale] : ""), [locale]);
  const tx = useCallback((faText: string, enText: string) => (locale === "fa" ? faText : enText), [locale]);
  return useMemo(() => ({ locale, dir, t: DICTS[locale], l, tx }), [locale, dir, l, tx]);
}

export type { Dict };
