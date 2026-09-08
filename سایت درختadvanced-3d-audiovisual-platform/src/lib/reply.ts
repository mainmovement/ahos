import type { Token, TokenScore } from "@/db/schema";

type BoardRow = { token: Token; score: TokenScore | null };

export function councilReply(question: string, board: BoardRow[]) {
  const q = question.toLowerCase();
  const find = (slug: string) => board.find((b) => b.token.slug === slug);

  if (/honeypot|shadow|shdw|scam|honeypot/.test(q) || q.includes("shdw")) {
    const t = find("shadowmint");
    return `SHDW is a confirmed honeypot. Buy succeeds, sell reverts for fresh wallets. Risk gate REJECT. Confidence ${t?.score?.confidence ?? 91} on the reject. Do not open a book.`;
  }
  if (/nxai|nexus|هype|هیجان/.test(q)) {
    return "Nexus AI is loud and forbidden. Mutable tax, unlocked LP, bundled wallets, synthetic social. High opportunity + critical security = REJECT. The tape is not the truth.";
  }
  if (/best|بهترین|gldn|golden|فرصت/.test(q)) {
    const t = find("goldenfruit");
    return `Best fruit on the board is Goldenfruit (GLDN). Independent LP inflows, unclustered holders, real GitHub, freeze revoked. Residual risk: mint authority still live — that is why the decision is PAPER, not a larger book. Opportunity ${t?.score?.opportunity ?? 88}, security ${t?.score?.security ?? 81}, confidence ${t?.score?.confidence ?? 76}. Rumor of a CEX listing is tagged RUMOR.`;
  }
  if (/why|چرا/.test(q) && /gldn|golden|leaf|dcore|veil/.test(q)) {
    return "Why is always evidence. Open the dossier: confirmed sources first, rumor last, security veto anywhere. If mint is abused, the thesis dies. If social is synthetic, demand is inventory.";
  }
  if (/skip|رد|reject/.test(q)) {
    return "SKIP and REJECT are results. SHDW skip avoided a total loss. NXAI reject ignored a beautiful pump. Not losing is a lesson the book must keep.";
  }
  if (/paper|معامله|pnl|سود/.test(q)) {
    return "Open paper: GLDN +13.8% on 250 virtual USDT; DCORE +12.7% on 150. LEAF was stopped −12.5% — developer history was underweighted. ECHO took T1 and left because the audit artifact still does not exist.";
  }
  if (/unknown|نمی|what don't|چه چیزی را نمی/.test(q)) {
    return "What we do not know: ROOTNET launch venue, DEPIN CORE hardware partner, LUMINA team identities, ECHO audit PDF, AUR stealth LP intent. UNKNOWN is spoken. We do not invent soil.";
  }

  const named = board.find((b) => q.includes(b.token.symbol.toLowerCase()) || q.includes(b.token.slug) || q.includes(b.token.name.toLowerCase()));
  if (named) {
    return `${named.token.name} (${named.token.symbol}) — ${named.score?.decision?.toUpperCase() ?? named.token.status.toUpperCase()}. ${named.token.summary} Confidence ${named.score?.confidence ?? "n/a"}.`;
  }

  return "Council received the question. Evidence before decision. Name a token, ask for the best fruit, the traps, the paper book, or what we still do not know.";
}
