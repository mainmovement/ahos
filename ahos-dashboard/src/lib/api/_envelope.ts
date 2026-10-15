/**
 * Envelope helpers shared by all `src/lib/api/*` modules.
 * Swap `fromMock` for a real fetcher (Next route / Python read model) per
 * function — components never change because the contract is DataEnvelope<T>.
 */
import type { DataEnvelope, Localized } from "./types";
import { mockMeta } from "@/mock/_seed";

export function fromMock<T>(data: T, source: string, label: Localized, retrievedSecondsAgo = 30, ttlSec = 300): DataEnvelope<T> {
  return { data, meta: mockMeta(source, label, retrievedSecondsAgo, ttlSec) };
}

export const label = (fa: string, en: string): Localized => ({ fa, en });
