import type { DataEnvelope, OpportunitiesOverview, TokenDossier } from "./types";
import { fromMock, label } from "./_envelope";
import { mockOpportunities, mockTokenDossiers } from "@/mock/tokens";

/** Token dossiers. Real source: Python canonical read model + DexScreener/GoPlus/RugCheck evidence. */
export async function getTokenDossiers(): Promise<DataEnvelope<TokenDossier[]>> {
  return fromMock(mockTokenDossiers(), "tokens", label("پرونده توکن نمایشی", "Demo token dossiers"), 60, 300);
}

/** Canonical decisions. Real source: `canonical_read_model.ts` → /api/decisions (Python authority). */
export async function getOpportunities(): Promise<DataEnvelope<OpportunitiesOverview>> {
  return fromMock(mockOpportunities(), "opportunities", label("تصمیم‌های کانونی نمایشی", "Demo canonical decisions"), 60, 300);
}
