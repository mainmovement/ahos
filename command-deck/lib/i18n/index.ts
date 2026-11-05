import type { AppLocale } from "./config";
import { fa, type Dictionary } from "./dictionaries/fa";
import { en } from "./dictionaries/en";

const dictionaries: Record<AppLocale, Dictionary> = { fa, en };

export function getDictionary(locale: AppLocale): Dictionary {
  return dictionaries[locale];
}

export type { Dictionary };
