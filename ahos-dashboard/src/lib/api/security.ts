import type { DataEnvelope, ProviderHealth, SecurityOverview } from "./types";
import { fromMock, label } from "./_envelope";
import { mockProviders, mockSecurity } from "@/mock/security";

/** Security center. Real source: Python security overlay (architecture/security) + GoPlus/RugCheck. */
export async function getSecurity(): Promise<DataEnvelope<SecurityOverview>> {
  return fromMock(mockSecurity(), "security", label("امنیت نمایشی", "Demo security"), 45, 300);
}

/** Provider health. Real source: `providers.ts` health probes (ProviderHealthStatus). */
export async function getProviderHealth(): Promise<DataEnvelope<ProviderHealth[]>> {
  return fromMock(mockProviders(), "providers", label("سلامت منابع نمایشی", "Demo provider health"), 30, 120);
}
