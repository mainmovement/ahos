import type { Metadata } from "next";
import { getTokenDossiers } from "@/lib/api/tokens";
import { TokensView } from "@/components/views/tokens-view";

export const metadata: Metadata = { title: "هوش توکن · Token Intelligence" };

export default async function TokensPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const [{ token }, dossiers] = await Promise.all([searchParams, getTokenDossiers()]);
  return <TokensView dossiers={dossiers} initialToken={token} />;
}
