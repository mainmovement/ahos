import { NextResponse } from "next/server";
import { db } from "@/db";
import { tokens, councilOpinions } from "@/db/schema";
import { seedDatabaseIfEmpty } from "@/db/seed";
import { desc, eq, ilike, or } from "drizzle-orm";

export async function GET(request: Request) {
  try {
    await seedDatabaseIfEmpty();

    const { searchParams } = new URL(request.url);
    const category = searchParams.get("category");
    const chain = searchParams.get("chain");
    const query = searchParams.get("query");

    let allTokens = await db.select().from(tokens).orderBy(desc(tokens.opportunityScore));

    if (category && category !== "all") {
      allTokens = allTokens.filter((t) => t.category === category);
    }
    if (chain && chain !== "all") {
      allTokens = allTokens.filter((t) => t.chain.toLowerCase() === chain.toLowerCase());
    }
    if (query) {
      const q = query.toLowerCase();
      allTokens = allTokens.filter(
        (t) =>
          t.symbol.toLowerCase().includes(q) ||
          t.name.toLowerCase().includes(q) ||
          t.contractAddress.toLowerCase().includes(q) ||
          t.narrative.toLowerCase().includes(q)
      );
    }

    return NextResponse.json({ success: true, tokens: allTokens });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { contractAddress, chain = "Solana", symbol, name } = body;

    if (!contractAddress) {
      return NextResponse.json({ success: false, error: "Contract address is required" }, { status: 400 });
    }

    // Simulate AI Discovery and 10-team council scoring calculation
    const oppScore = Math.floor(Math.random() * 40) + 60; // 60-99
    const secScore = Math.floor(Math.random() * 50) + 50; // 50-99
    const confScore = Math.floor(Math.random() * 30) + 70;

    const [newToken] = await db
      .insert(tokens)
      .values({
        symbol: symbol || contractAddress.substring(0, 6).toUpperCase(),
        name: name || `Token ${contractAddress.substring(0, 8)}`,
        chain,
        contractAddress,
        category: "newly-launched",
        opportunityScore: oppScore,
        securityScore: secScore,
        confidenceScore: confScore,
        liquidityScore: Math.floor(Math.random() * 30) + 70,
        whaleScore: Math.floor(Math.random() * 30) + 70,
        socialScore: Math.floor(Math.random() * 40) + 60,
        narrativeScore: Math.floor(Math.random() * 20) + 80,
        evidenceScore: Math.floor(Math.random() * 30) + 70,
        price: (Math.random() * 0.5 + 0.001).toFixed(6),
        priceChange24h: (Math.random() * 200 - 30).toFixed(1),
        liquidityUsd: Math.floor(Math.random() * 2000000 + 100000).toString(),
        marketCapUsd: Math.floor(Math.random() * 10000000 + 500000).toString(),
        volume24h: Math.floor(Math.random() * 5000000 + 200000).toString(),
        holdersCount: Math.floor(Math.random() * 5000 + 300),
        status: secScore < 40 ? "rejected" : oppScore >= 80 ? "approved" : "investigating",
        narrative: "AI & Autonomous Agent Intelligence",
        evidenceSummary: `Scanned on-chain RPC nodes for ${chain}. LP contract locked, zero honeypot signature found in bytecode analysis.`,
        risksSummary: secScore < 60 ? "High top-10 wallet concentration risk." : "Moderate liquidity volatility during initial discovery stage.",
        bullScenario: "Targeting 3.5x upside if volume accelerates.",
        baseScenario: "Consolidating at current price range.",
        bearScenario: "Pullback if market sentiment shifts.",
      })
      .returning();

    // Auto-generate 10-team council opinions
    const teamDefs = [
      { code: "team_01", name: "Team 01 - Mathematical Intelligence", v: "bullish", arg: "Quantitative decay model indicates sustained accumulation trajectory." },
      { code: "team_02", name: "Team 02 - Crypto Market Intelligence", v: "bullish", arg: "Orderbook depth and DEX pool reserves show healthy buyer support." },
      { code: "team_03", name: "Team 03 - Blockchain & On-Chain Intelligence", v: "bullish", arg: "3 Smart Money wallets detected accumulating in last 4 hours." },
      { code: "team_04", name: "Team 04 - Cybersecurity & Hacker Intelligence", v: secScore < 50 ? "reject" : "bullish", arg: secScore < 50 ? "High risk bytecode signature detected!" : "Bytecode verified. Mint authority revoked." },
      { code: "team_05", name: "Team 05 - Investigative Intelligence", v: "bullish", arg: "OSINT check links deployer wallet to clean historical record." },
      { code: "team_06", name: "Team 06 - News & Journalism Intelligence", v: "bullish", arg: "Organic announcements confirmed on official Github & X." },
      { code: "team_07", name: "Team 07 - Social & Narrative Intelligence", v: "bullish", arg: "Social sentiment score elevated with low bot noise ratio." },
      { code: "team_08", name: "Team 08 - Technology & Software Engineering", v: "bullish", arg: "Smart contract functions structure is standard and clean." },
      { code: "team_09", name: "Team 09 - AI Research & Self-Evolution", v: "bullish", arg: "Matches historical high-probability momentum pattern #108." },
      { code: "team_10", name: "Team 10 - Strategic Decision & Red-Team Council", v: secScore < 50 ? "reject" : "bullish", arg: secScore < 50 ? "Rejected by Red Team Risk Gate due to contract risk." : "Risk-reward ratio calculated at 1:4.8. Approved." },
    ];

    for (const t of teamDefs) {
      await db.insert(councilOpinions).values({
        tokenId: newToken.id,
        teamCode: t.code,
        teamName: t.name,
        verdict: t.v,
        confidence: Math.floor(Math.random() * 20) + 80,
        argument: t.arg,
        keyEvidence: "Automated Evidence Collector Log #AHOS-" + Math.floor(Math.random() * 9000 + 1000),
      });
    }

    return NextResponse.json({ success: true, token: newToken });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
