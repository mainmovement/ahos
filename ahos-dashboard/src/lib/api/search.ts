import type { DataEnvelope, SearchEntry } from "./types";
import { fromMock, label } from "./_envelope";
import { mockAgents } from "@/mock/agents";
import { mockInstruments } from "@/mock/markets";
import { mockNews } from "@/mock/news";
import { mockTokenDossiers } from "@/mock/tokens";

/** Command-palette search index. Real source: a /api/search endpoint. */
export async function getSearchIndex(): Promise<DataEnvelope<SearchEntry[]>> {
  const entries: SearchEntry[] = [
    ...mockInstruments().map((i) => ({ id: `i:${i.id}`, kind: "instrument" as const, label: i.symbol, sublabel: i.name, href: `/markets?symbol=${i.id}` })),
    ...mockTokenDossiers().map((t) => ({ id: `t:${t.tokenKey}`, kind: "token" as const, label: t.symbol, sublabel: { fa: `${t.name} · ${t.chain}`, en: `${t.name} · ${t.chain}` }, href: `/tokens?token=${encodeURIComponent(t.tokenKey)}` })),
    ...mockAgents().agents.map((a) => ({ id: `a:${a.id}`, kind: "agent" as const, label: a.code, sublabel: a.name, href: `/agents?agent=${encodeURIComponent(a.id)}` })),
    ...mockNews().items.map((n) => ({ id: `n:${n.id}`, kind: "news" as const, label: n.source, sublabel: n.title, href: `/news?item=${n.id}` })),
  ];
  return fromMock(entries, "search", label("نمایه جستجو (نمایشی)", "Search index (demo)"), 0, 600);
}
