import "dotenv/config";
import { db, pool } from "./index";
import {
  tokens,
  opportunityScores,
  securityChecks,
  councilTeams,
  councilOpinions,
  evidenceItems,
  newsItems,
  socialSignals,
  onchainEvents,
  paperTrades,
  tradeEvents,
  alerts,
  systemComponents,
  systemLogs,
  learningLogs,
  chatMessages,
  settings,
} from "./schema";

async function seed() {
  console.log("Seeding AHOS database...");

  // Clean slate (idempotent re-seed)
  await db.execute(
    `TRUNCATE TABLE
      trade_events, paper_trades, learning_logs, alerts, evidence_items,
      council_opinions, council_teams, onchain_events, social_signals,
      news_items, security_checks, opportunity_scores, chat_messages,
      system_logs, system_components, settings, tokens
    RESTART IDENTITY CASCADE`
  );

  const teamSeed = [
    { code: "T01", name: "Mathematical Intelligence", focus: "Statistics, Bayesian reasoning, anomaly detection, quantitative modeling.", icon: "sigma", sortOrder: 1 },
    { code: "T02", name: "Crypto Market Intelligence", focus: "Tokenomics, market cycles, liquidity structure, price action.", icon: "line-chart", sortOrder: 2 },
    { code: "T03", name: "Blockchain & On-Chain Intelligence", focus: "Wallet analysis, whale tracking, smart money, holder distribution.", icon: "link", sortOrder: 3 },
    { code: "T04", name: "Cybersecurity & Hacker Intelligence", focus: "Contract exploits, honeypots, malicious code, red-team analysis.", icon: "shield-alert", sortOrder: 4 },
    { code: "T05", name: "Investigative Intelligence", focus: "OSINT, entity investigation, contradiction detection.", icon: "search", sortOrder: 5 },
    { code: "T06", name: "News & Journalism Intelligence", focus: "News verification, source evaluation, narrative detection.", icon: "newspaper", sortOrder: 6 },
    { code: "T07", name: "Social & Narrative Intelligence", focus: "Sentiment, narrative velocity, influencer & community analysis.", icon: "message-circle", sortOrder: 7 },
    { code: "T08", name: "Technology & Software Engineering", focus: "Architecture, APIs, automation, GitHub, DevOps.", icon: "code", sortOrder: 8 },
    { code: "T09", name: "AI Research & Self-Evolution", focus: "Model comparison, reasoning methods, agent architecture, RAG.", icon: "brain-circuit", sortOrder: 9 },
    { code: "T10", name: "Strategic Decision & Red-Team Council", focus: "Contrarian analysis, bias detection, worst-case simulation.", icon: "swords", sortOrder: 10 },
  ];
  const insertedTeams = await db.insert(councilTeams).values(teamSeed).returning();
  const teamByCode = Object.fromEntries(insertedTeams.map((t) => [t.code, t]));

  const tokenSeed = [
    {
      name: "Solvent Protocol", symbol: "SOLV", chain: "Solana", contractAddress: "SoLv9k...E3q1", status: "new" as const,
      narrative: "DePIN", logoEmoji: "🛰️", launchDate: daysAgo(6), priceUsd: "0.0421", priceChange24h: "38.4",
      marketCapUsd: "4820000", liquidityUsd: "612000", volume24hUsd: "1980000", holders: 3120,
      summary: "Decentralized compute marketplace with rapid holder growth and rising whale accumulation since launch.",
    },
    {
      name: "Aurora Mesh", symbol: "AURM", chain: "Base", contractAddress: "0xA0ur...92fD", status: "existing" as const,
      narrative: "AI", logoEmoji: "🌌", launchDate: daysAgo(94), priceUsd: "0.148", priceChange24h: "12.1",
      marketCapUsd: "18200000", liquidityUsd: "2100000", volume24hUsd: "3650000", holders: 9840,
      summary: "AI-agent coordination layer, undervalued relative to comparable narratives, fresh catalyst forming.",
    },
    {
      name: "Nightshade", symbol: "NSHD", chain: "Ethereum", contractAddress: "0xNS44...11ab", status: "new" as const,
      narrative: "Meme", logoEmoji: "🐍", launchDate: daysAgo(2), priceUsd: "0.000091", priceChange24h: "212.6",
      marketCapUsd: "910000", liquidityUsd: "88000", volume24hUsd: "1450000", holders: 2210,
      summary: "Extremely high velocity meme launch. Explosive social growth but concentrated holder base.",
    },
    {
      name: "Ferrum Chain", symbol: "FERM", chain: "BNB Chain", contractAddress: "0xFe11...c0de", status: "pre_launch" as const,
      narrative: "Infrastructure", logoEmoji: "⚙️", launchDate: daysAhead(4), priceUsd: "0", priceChange24h: "0",
      marketCapUsd: "0", liquidityUsd: "0", volume24hUsd: "0", holders: 0,
      summary: "Modular L2 rollout with growing developer commit activity ahead of confirmed TGE.",
    },
    {
      name: "Glimmer RWA", symbol: "GLMR2", chain: "Ethereum", contractAddress: "0xG11m...9902", status: "existing" as const,
      narrative: "RWA", logoEmoji: "💎", launchDate: daysAgo(210), priceUsd: "0.62", priceChange24h: "-3.2",
      marketCapUsd: "52000000", liquidityUsd: "5200000", volume24hUsd: "2100000", holders: 15200,
      summary: "Real-world-asset tokenization protocol with steady on-chain growth, low social buzz.",
    },
    {
      name: "Cobalt Fox", symbol: "CBFX", chain: "Solana", contractAddress: "Cbft8...ZZq7", status: "new" as const,
      narrative: "Meme", logoEmoji: "🦊", launchDate: daysAgo(1), priceUsd: "0.0000038", priceChange24h: "-64.2",
      marketCapUsd: "210000", liquidityUsd: "31000", volume24hUsd: "740000", holders: 980,
      summary: "Flagged by security layer — sell function heavily restricted for non-whitelisted wallets.",
    },
    {
      name: "Vector Grid", symbol: "VGRD", chain: "Base", contractAddress: "0xVGrd...4471", status: "new" as const,
      narrative: "DePIN", logoEmoji: "🔌", launchDate: daysAgo(11), priceUsd: "0.0091", priceChange24h: "18.7",
      marketCapUsd: "2650000", liquidityUsd: "410000", volume24hUsd: "890000", holders: 4210,
      summary: "Energy-grid oracle network showing organic whale accumulation and stable liquidity growth.",
    },
    {
      name: "Halcyon", symbol: "HLCY", chain: "Solana", contractAddress: "HLcy9...q0p2", status: "existing" as const,
      narrative: "Gaming", logoEmoji: "🎮", launchDate: daysAgo(150), priceUsd: "0.0245", priceChange24h: "7.8",
      marketCapUsd: "9800000", liquidityUsd: "1300000", volume24hUsd: "1120000", holders: 7650,
      summary: "Gaming ecosystem token re-igniting attention around a new title announcement.",
    },
  ];

  const insertedTokens = await db.insert(tokens).values(tokenSeed).returning();
  const byName = Object.fromEntries(insertedTokens.map((t) => [t.symbol, t]));

  await db.insert(opportunityScores).values([
    scoreRow(byName.SOLV.id, { opportunityScore: 88, securityScore: 74, liquidityScore: 66, socialMomentum: 82, whaleScore: 79, narrativeScore: 85, evidenceScore: 71, confidence: 76, councilDecision: "watch",
      bull: "DePIN narrative accelerates, compute demand rises, liquidity doubles within 2 weeks.",
      base: "Steady holder growth continues, price consolidates with moderate upside.",
      bear: "Narrative rotation away from DePIN causes momentum to fade within days.",
      extreme: "Deployer wallet moves majority holdings to an exchange, triggering a rapid sell-off.",
      why: ["Whale wallets accumulated 4.2% of supply in 72 hours", "Liquidity grew 3.1x since launch with no single LP dominance", "GitHub commit velocity is unusually high for a 6-day-old project", "Independent social mentions across X and Telegram corroborate organic growth"],
      risks: ["Still within first two weeks — survivorship data is limited", "Top 10 wallets hold 24% of circulating supply", "No formal audit published yet"],
      reject: ["If top holder concentration exceeds 40%", "If liquidity is unlocked and removed", "If deployer wallet begins distributing to CEX deposit addresses"] }),
    scoreRow(byName.AURM.id, { opportunityScore: 79, securityScore: 91, liquidityScore: 84, socialMomentum: 58, whaleScore: 61, narrativeScore: 74, evidenceScore: 88, confidence: 82, councilDecision: "watch",
      bull: "New agent-framework partnership announcement drives renewed attention and re-rating.",
      base: "Gradual accumulation continues as AI narrative remains active market-wide.",
      bear: "Broader AI-token narrative cools, volume drifts lower.",
      extreme: "Macro risk-off event drags liquidity out of mid-cap AI tokens broadly.",
      why: ["Security audit passed with zero critical findings", "Liquidity is time-locked for 18 more months", "On-chain dev wallet activity shows continuous protocol upgrades", "Currently undervalued vs. comparable AI-agent tokens by ~40%"],
      risks: ["Social momentum is comparatively low — could indicate limited near-term catalysts", "Token unlock schedule releases 6% of supply next month"],
      reject: ["If a critical vulnerability is discovered in the upgraded contract", "If unlock event causes liquidity to drop below $1M"] }),
    scoreRow(byName.NSHD.id, { opportunityScore: 54, securityScore: 38, liquidityScore: 41, socialMomentum: 96, whaleScore: 45, narrativeScore: 60, evidenceScore: 33, confidence: 40, councilDecision: "insufficient_evidence",
      bull: "Viral momentum continues, CEX listing rumor gets confirmed.",
      base: "Attention fades within 48-72 hours as is typical for meme velocity spikes.",
      bear: "Early holders exit into retail demand, price halves within a day.",
      extreme: "Top wallets dump simultaneously — classic pump-and-dump signature detected.",
      why: ["Mentions grew 18x in 24 hours across X and Telegram", "Multiple mid-tier influencers posted independently (not a single coordinated push)"],
      risks: ["Top 5 wallets hold 37% of supply", "No liquidity lock detected", "CEX listing is an unverified rumor, not confirmed by any exchange"],
      reject: ["If liquidity lock cannot be verified within 24 hours", "If deployer wallet has prior rug history"] }),
    scoreRow(byName.FERM.id, { opportunityScore: 63, securityScore: 0, liquidityScore: 0, socialMomentum: 47, whaleScore: 0, narrativeScore: 66, evidenceScore: 58, confidence: 44, councilDecision: "insufficient_evidence",
      bull: "TGE executes cleanly with strong exchange support and immediate liquidity depth.",
      base: "Launch proceeds on schedule with moderate initial volume.",
      bear: "TGE delayed again, community attention decays.",
      extreme: "Pre-launch contract exploited before liquidity is even seeded.",
      why: ["GitHub commit frequency up 210% over the last 30 days", "Three independent testnet reports corroborate stable rollup performance", "Team has verifiable prior shipped project (cross-checked via investigative team)"],
      risks: ["No live contract to analyze yet — all security data is provisional", "TGE date has slipped once already"],
      reject: ["If TGE slips beyond 30 more days without explanation", "If contract audit is not published before launch"] }),
    scoreRow(byName.GLMR2.id, { opportunityScore: 47, securityScore: 86, liquidityScore: 88, socialMomentum: 24, whaleScore: 52, narrativeScore: 40, evidenceScore: 80, confidence: 70, councilDecision: "watch",
      bull: "RWA narrative gets renewed institutional attention, re-rating occurs.",
      base: "Slow steady on-chain growth continues with muted price action.",
      bear: "Continues to be ignored by the market despite fundamentals.",
      extreme: "Regulatory action against RWA tokenization broadly impacts the sector.",
      why: ["Consistent on-chain growth for 7 months straight", "Security posture is exceptionally clean", "Deep, well-distributed liquidity"],
      risks: ["Extremely low social attention — could stay undervalued indefinitely", "RWA narrative is currently out of favor market-wide"],
      reject: ["If on-chain growth trend reverses for 3+ consecutive weeks"] }),
    scoreRow(byName.CBFX.id, { opportunityScore: 12, securityScore: 8, liquidityScore: 22, socialMomentum: 71, whaleScore: 30, narrativeScore: 35, evidenceScore: 20, confidence: 91, councilDecision: "reject",
      bull: "N/A — security gate has already rejected this candidate.",
      base: "N/A",
      bear: "Sell function confirmed restricted for 90%+ of simulated wallets.",
      extreme: "Total loss of capital for any buyer unable to exit.",
      why: ["Flagged automatically by honeypot simulation"],
      risks: ["Confirmed honeypot characteristics", "Sell tax simulated at 100% for non-whitelisted wallets", "Deployer wallet matches a cluster with 3 prior rug pulls"],
      reject: ["Immediate reject — critical security risk overrides opportunity score entirely"] }),
    scoreRow(byName.VGRD.id, { opportunityScore: 81, securityScore: 77, liquidityScore: 70, socialMomentum: 64, whaleScore: 84, narrativeScore: 72, evidenceScore: 75, confidence: 79, councilDecision: "watch",
      bull: "Energy-grid oracle partnership confirmed, real-world integration announced.",
      base: "Whale accumulation continues at current pace, price grinds higher.",
      bear: "Momentum stalls as broader DePIN sector cools off.",
      extreme: "Oracle data feed exploited, protocol credibility damaged.",
      why: ["Smart money wallets net-bought for 9 consecutive days", "Liquidity has grown without a single large withdrawal", "Independent GitHub review shows active, multi-contributor development"],
      risks: ["Oracle mechanism has not yet been third-party audited", "Sector-wide DePIN rotation risk"],
      reject: ["If whale wallets begin net-selling for 3+ consecutive days"] }),
    scoreRow(byName.HLCY.id, { opportunityScore: 69, securityScore: 80, liquidityScore: 73, socialMomentum: 55, whaleScore: 58, narrativeScore: 62, evidenceScore: 68, confidence: 65, councilDecision: "watch",
      bull: "New title announcement drives fresh user acquisition and volume.",
      base: "Gradual re-rating as gaming narrative slowly returns.",
      bear: "Announcement underwhelms, attention fades again.",
      extreme: "Title launch delayed indefinitely, community trust erodes.",
      why: ["Renewed development activity ahead of announcement", "Historical holder base remains largely intact (low churn)"],
      risks: ["Gaming narrative has disappointed markets multiple times before", "Announcement details remain vague"],
      reject: ["If announced title is cancelled or indefinitely delayed"] }),
  ]);

  await db.insert(securityChecks).values([
    secRow(byName.SOLV.id, { riskLevel: "medium", honeypot: false, buyTax: "0", sellTax: "0", mint: false, freeze: false, renounced: true, locked: true, lpLock: "82", topHolder: "24.1", rugHistory: false, hiddenAdmin: false, flags: ["Audit pending"], notes: "No audit published yet; monitor closely over next 14 days." }),
    secRow(byName.AURM.id, { riskLevel: "low", honeypot: false, buyTax: "1", sellTax: "1", mint: false, freeze: false, renounced: true, locked: true, lpLock: "100", topHolder: "11.4", rugHistory: false, hiddenAdmin: false, flags: [], notes: "Passed third-party audit with zero critical findings." }),
    secRow(byName.NSHD.id, { riskLevel: "high", honeypot: false, buyTax: "0", sellTax: "5", mint: false, freeze: false, renounced: false, locked: false, lpLock: "0", topHolder: "37.2", rugHistory: false, hiddenAdmin: true, flags: ["No liquidity lock", "Ownership not renounced", "Hidden admin function detected"], notes: "Contract owner retains a function capable of altering trading limits post-launch." }),
    secRow(byName.FERM.id, { riskLevel: "medium", honeypot: false, buyTax: "0", sellTax: "0", mint: false, freeze: false, renounced: false, locked: false, lpLock: "0", topHolder: "0", rugHistory: false, hiddenAdmin: false, flags: ["Pre-launch — provisional data only"], notes: "No live contract yet; assessment based on testnet code review." }),
    secRow(byName.GLMR2.id, { riskLevel: "low", honeypot: false, buyTax: "0", sellTax: "0", mint: false, freeze: false, renounced: true, locked: true, lpLock: "100", topHolder: "9.8", rugHistory: false, hiddenAdmin: false, flags: [], notes: "Clean security posture sustained across 7 months of monitoring." }),
    secRow(byName.CBFX.id, { riskLevel: "critical", honeypot: true, buyTax: "0", sellTax: "100", mint: true, freeze: true, renounced: false, locked: false, lpLock: "0", topHolder: "61.4", rugHistory: true, hiddenAdmin: true, flags: ["Confirmed honeypot", "Sell disabled for non-whitelisted wallets", "Deployer linked to 3 prior rugs", "Mint authority active"], notes: "Automatic REJECT — critical security risk overrides opportunity score." }),
    secRow(byName.VGRD.id, { riskLevel: "medium", honeypot: false, buyTax: "0", sellTax: "0", mint: false, freeze: false, renounced: true, locked: true, lpLock: "90", topHolder: "18.6", rugHistory: false, hiddenAdmin: false, flags: ["Oracle mechanism not yet audited"], notes: "Token contract is clean; oracle logic pending third-party review." }),
    secRow(byName.HLCY.id, { riskLevel: "low", honeypot: false, buyTax: "0", sellTax: "0", mint: false, freeze: false, renounced: true, locked: true, lpLock: "95", topHolder: "14.2", rugHistory: false, hiddenAdmin: false, flags: [], notes: "Long operating history with no security incidents on record." }),
  ]);

  const stances: Record<string, { code: string; stance: "bullish" | "bearish" | "neutral" | "risk_flag" | "insufficient_evidence"; summary: string; confidence: number }[]> = {
    SOLV: [
      { code: "T01", stance: "bullish", summary: "Anomaly detection shows accumulation pattern statistically inconsistent with organic retail-only buying — consistent with informed accumulation.", confidence: 78 },
      { code: "T02", stance: "bullish", summary: "Liquidity-to-market-cap ratio is healthy for a 6-day-old token; volume is not solely wash trading.", confidence: 74 },
      { code: "T03", stance: "bullish", summary: "Whale wallets with prior profitable DePIN entries have accumulated meaningfully.", confidence: 80 },
      { code: "T04", stance: "neutral", summary: "No exploitable functions found in decompiled bytecode; audit still pending, so residual risk remains.", confidence: 60 },
      { code: "T05", stance: "neutral", summary: "Team identity partially doxxed; no contradictions found across cross-referenced claims so far.", confidence: 55 },
      { code: "T06", stance: "neutral", summary: "Coverage limited to two mid-tier crypto news outlets; nothing beyond that yet.", confidence: 50 },
      { code: "T07", stance: "bullish", summary: "Organic, non-coordinated mention growth across X and Telegram — not driven by a single influencer.", confidence: 72 },
      { code: "T08", stance: "bullish", summary: "GitHub activity shows real multi-contributor commits, not placeholder code.", confidence: 68 },
      { code: "T09", stance: "neutral", summary: "Historical pattern-match against similar past DePIN launches is inconclusive at this sample size.", confidence: 45 },
      { code: "T10", stance: "risk_flag", summary: "Two-week track record is too short for high confidence; recommend WATCH, not aggressive entry.", confidence: 65 },
    ],
    NSHD: [
      { code: "T01", stance: "risk_flag", summary: "Mention growth curve matches signatures seen in prior coordinated pump campaigns.", confidence: 66 },
      { code: "T04", stance: "risk_flag", summary: "Hidden admin function can alter trading limits without timelock — material risk.", confidence: 85 },
      { code: "T07", stance: "bullish", summary: "Engagement is extremely high, but quality-adjusted engagement (real accounts) is only moderate.", confidence: 40 },
      { code: "T10", stance: "insufficient_evidence", summary: "CEX listing rumor is unverified; do not treat as fact. Recommend INSUFFICIENT EVIDENCE, not action.", confidence: 70 },
    ],
    CBFX: [
      { code: "T04", stance: "risk_flag", summary: "Confirmed honeypot via simulated sell transaction failure for 9/10 test wallets.", confidence: 97 },
      { code: "T05", stance: "risk_flag", summary: "Deployer wallet cross-referenced to 3 previously rugged tokens on the same chain.", confidence: 93 },
      { code: "T10", stance: "risk_flag", summary: "Immediate REJECT recommended — this is a textbook scam signature.", confidence: 96 },
    ],
    VGRD: [
      { code: "T02", stance: "bullish", summary: "Liquidity growth trend is one of the healthiest in the current DePIN cohort.", confidence: 76 },
      { code: "T03", stance: "bullish", summary: "9 consecutive days of net whale accumulation with no distribution events.", confidence: 81 },
      { code: "T04", stance: "neutral", summary: "Token contract clean; oracle logic still pending independent audit.", confidence: 58 },
      { code: "T10", stance: "neutral", summary: "Solid setup, but recommend confirming oracle audit before increasing conviction.", confidence: 62 },
    ],
  };

  for (const [symbol, opinions] of Object.entries(stances)) {
    const token = byName[symbol];
    await db.insert(councilOpinions).values(
      opinions.map((o) => ({
        tokenId: token.id,
        teamId: teamByCode[o.code].id,
        stance: o.stance,
        summary: o.summary,
        confidence: o.confidence,
      }))
    );
  }

  await db.insert(evidenceItems).values([
    ev(byName.SOLV.id, "onchain", "Chain Explorer", "4.2% of supply accumulated by 6 wallets in 72h", "verified", "positive"),
    ev(byName.SOLV.id, "development", "GitHub", "17 commits across 4 contributors in the last week", "verified", "positive"),
    ev(byName.SOLV.id, "social", "X / Twitter", "Independent mentions from 40+ distinct accounts, low bot overlap", "verified", "positive"),
    ev(byName.SOLV.id, "security", "Automated Contract Scanner", "No mint/freeze authority detected, ownership renounced", "verified", "positive"),
    ev(byName.NSHD.id, "rumor", "Telegram", "Unconfirmed claim of upcoming Tier-1 CEX listing", "rumor", "positive"),
    ev(byName.NSHD.id, "security", "Automated Contract Scanner", "Hidden admin function can alter trading limits", "verified", "negative"),
    ev(byName.CBFX.id, "security", "Honeypot Simulator", "Sell transaction fails for 9 of 10 simulated wallets", "verified", "negative"),
    ev(byName.CBFX.id, "onchain", "Chain Explorer", "Deployer wallet matches cluster with 3 historical rugs", "verified", "negative"),
    ev(byName.AURM.id, "security", "Third-Party Audit", "Zero critical findings in latest audit report", "verified", "positive"),
    ev(byName.FERM.id, "development", "GitHub", "Commit velocity up 210% over trailing 30 days", "verified", "positive"),
    ev(byName.VGRD.id, "onchain", "Chain Explorer", "9 consecutive days of net whale accumulation", "verified", "positive"),
    ev(byName.GLMR2.id, "news", "Financial News Wire", "RWA tokenization coverage mentions protocol as case study", "verified", "positive"),
  ]);

  await db.insert(newsItems).values([
    { tokenId: byName.SOLV.id, title: "Solvent Protocol compute marketplace sees surging demand post-launch", summary: "Independent trackers note usage of the compute marketplace has tripled in a week, aligning with holder growth.", source: "ChainWire", url: "https://example.com/news/solv-1", sentiment: "positive" as const, credibility: 72, tags: ["DePIN", "Solana"] },
    { tokenId: byName.AURM.id, title: "Aurora Mesh completes third-party security audit with zero critical issues", summary: "The audit, conducted by an independent firm, found no critical or high-severity vulnerabilities.", source: "SecurityDesk", url: "https://example.com/news/aurm-1", sentiment: "positive" as const, credibility: 88, tags: ["AI", "Security", "Audit"] },
    { tokenId: byName.NSHD.id, title: "Unverified rumor: Nightshade eyeing exchange listing", summary: "Community chatter references a possible listing; no exchange has confirmed this claim.", source: "Community Telegram", url: null, sentiment: "neutral" as const, credibility: 20, tags: ["Meme", "Rumor"] },
    { tokenId: null, title: "DePIN sector volume up 34% week-over-week across tracked tokens", summary: "Aggregate on-chain volume across DePIN-narrative tokens increased sharply this week.", source: "Market Desk Weekly", url: "https://example.com/news/depin-sector", sentiment: "positive" as const, credibility: 80, tags: ["DePIN", "Market"] },
    { tokenId: byName.CBFX.id, title: "Security researchers flag Cobalt Fox as high-risk honeypot", summary: "Multiple automated scanners independently confirmed sell-side restrictions in the token contract.", source: "SecurityDesk", url: "https://example.com/news/cbfx-1", sentiment: "negative" as const, credibility: 90, tags: ["Security", "Scam"] },
    { tokenId: null, title: "AHOS Weekly Intelligence Digest", summary: "Summary of newly discovered candidates, rejected tokens, and open paper trades for the week.", source: "AHOS Internal", url: null, sentiment: "neutral" as const, credibility: 100, tags: ["AHOS", "Report"] },
  ]);

  const platforms = ["X", "Telegram", "Reddit", "Discord"];
  const socialRows = [];
  for (const [symbol, base] of Object.entries({ SOLV: 70, AURM: 45, NSHD: 95, VGRD: 55, HLCY: 48, CBFX: 60, GLMR2: 20, FERM: 38 })) {
    const token = byName[symbol];
    for (const platform of platforms) {
      socialRows.push({
        tokenId: token.id,
        platform,
        mentions: Math.round(base * (0.6 + Math.random() * 0.8) * 10),
        engagementScore: Math.min(100, Math.round(base * (0.7 + Math.random() * 0.5))),
        sentiment: Math.round(-20 + Math.random() * 90),
        narrativeVelocity: Math.min(100, Math.round(base * (0.5 + Math.random() * 0.7))),
        influencerActivity: Math.min(100, Math.round(base * (0.3 + Math.random() * 0.6))),
        isSynthetic: symbol === "NSHD" && Math.random() > 0.5,
      });
    }
  }
  await db.insert(socialSignals).values(socialRows);

  await db.insert(onchainEvents).values([
    oc(byName.SOLV.id, "whale_accumulation", "7xK9...m2Pq", 84000, "Wallet accumulated $84k of SOLV over 6 hours"),
    oc(byName.SOLV.id, "liquidity_add", "Pool", 120000, "Liquidity pool received an additional $120k"),
    oc(byName.VGRD.id, "whale_accumulation", "0xVw8...21ff", 61000, "Smart-money-labeled wallet added to position"),
    oc(byName.NSHD.id, "large_transfer", "0xN29...ff01", 42000, "Top holder transferred 12% of supply to a new wallet"),
    oc(byName.CBFX.id, "deployer_transfer", "Cbft...dep1", 15000, "Deployer wallet moved funds to a wallet linked to prior rugs"),
    oc(byName.AURM.id, "contract_upgrade", "0xAur...gov1", 0, "Governance-approved contract upgrade executed transparently"),
    oc(byName.GLMR2.id, "holder_growth", "Network", 0, "Holder count crossed 15,000 with steady weekly growth"),
  ]);

  const trades = await db.insert(paperTrades).values([
    trade(byName.SOLV.id, { status: "open", outcome: "pending", entry: "0.0421", exit: null, capital: "1000", size: "150", stop: "0.0362", t1: "0.0490", t2: "0.0560", t3: "0.0680", hold: 96, reason: "Council WATCH with strong on-chain + dev evidence convergence.", opened: daysAgo(1) }),
    trade(byName.VGRD.id, { status: "open", outcome: "pending", entry: "0.0091", exit: null, capital: "1000", size: "120", stop: "0.0079", t1: "0.0105", t2: "0.0122", t3: "0.0145", hold: 120, reason: "Sustained whale accumulation with clean contract.", opened: daysAgo(3) }),
    trade(byName.AURM.id, { status: "closed", outcome: "win", entry: "0.132", exit: "0.151", capital: "1000", size: "180", stop: "0.118", t1: "0.145", t2: "0.160", t3: "0.180", hold: 168, reason: "Undervalued vs. peers with clean audit.", opened: daysAgo(14), closed: daysAgo(7), pnlUsd: "25.90", pnlPercent: "14.4", post: "Thesis played out: audit clarity plus peer re-rating drove the move. Evidence from T02 and T04 was decisive." }),
    trade(byName.HLCY.id, { status: "closed", outcome: "loss", entry: "0.0261", exit: "0.0233", capital: "1000", size: "100", stop: "0.0233", t1: "0.0300", t2: "0.0330", t3: "0.0370", hold: 72, reason: "Anticipated announcement momentum.", opened: daysAgo(20), closed: daysAgo(18), pnlUsd: "-10.73", pnlPercent: "-10.7", post: "Announcement underwhelmed; T07 overweighted social hype without enough T06 news corroboration. Lesson: require independent news confirmation before entries driven by anticipation." }),
    trade(byName.NSHD.id, { status: "closed", outcome: "skip", entry: "0.000091", exit: null, capital: "1000", size: "0", stop: null, t1: null, t2: null, t3: null, hold: 0, reason: "Security layer flagged hidden admin function; council overridden to SKIP despite high social score.", opened: daysAgo(2), closed: daysAgo(2), pnlUsd: "0", pnlPercent: "0", post: "Correct SKIP: token price fell 46% within 24 hours after admin function was exploited to raise sell tax to 40%." }),
    trade(byName.CBFX.id, { status: "closed", outcome: "skip", entry: "0.0000038", exit: null, capital: "1000", size: "0", stop: null, t1: null, t2: null, t3: null, hold: 0, reason: "Automatic REJECT from Risk Gate — confirmed honeypot.", opened: daysAgo(1), closed: daysAgo(1), pnlUsd: "0", pnlPercent: "0", post: "Correct REJECT: token liquidity was removed 4 hours after launch, confirming honeypot classification." }),
  ]).returning();

  const tradeBySymbol = Object.fromEntries(trades.map((t, i) => [Object.keys(byName)[i], t]));
  await db.insert(tradeEvents).values([
    { paperTradeId: trades[0].id, eventType: "opened", note: "Position opened at council WATCH decision with 15% position sizing." },
    { paperTradeId: trades[0].id, eventType: "monitor", note: "Stop-loss and targets unchanged; whale accumulation continues." },
    { paperTradeId: trades[2].id, eventType: "opened", note: "Position opened after audit confirmation." },
    { paperTradeId: trades[2].id, eventType: "target_hit", note: "Target 1 reached; trailing stop moved up." },
    { paperTradeId: trades[2].id, eventType: "closed", note: "Closed for +14.4% after 7 days — thesis validated." },
    { paperTradeId: trades[3].id, eventType: "opened", note: "Position opened ahead of anticipated announcement." },
    { paperTradeId: trades[3].id, eventType: "stopped_out", note: "Stop-loss triggered after announcement underwhelmed the market." },
    { paperTradeId: trades[4].id, eventType: "skipped", note: "Security override — SKIP recorded instead of entry." },
    { paperTradeId: trades[5].id, eventType: "rejected", note: "Risk Gate rejection — confirmed honeypot signature." },
  ]);

  await db.insert(learningLogs).values([
    { tokenId: byName.AURM.id, paperTradeId: trades[2].id, patternType: "success", title: "Audit clarity + peer undervaluation converged correctly", description: "Security score (T04) and market structure comparison (T02) both independently pointed to mispricing. Confidence weighting on convergent evidence proved reliable — pattern reinforced." },
    { tokenId: byName.HLCY.id, paperTradeId: trades[3].id, patternType: "failure", title: "Overweighted anticipation without independent news confirmation", description: "Social momentum team (T07) flagged bullish sentiment, but no verified news (T06) confirmed the announcement's scope. New rule proposed: require T06 verification tier ≥ 60 before sizing entries around anticipated announcements." },
    { tokenId: byName.NSHD.id, paperTradeId: trades[4].id, patternType: "skip", title: "Security override correctly prevented a loss", description: "Despite a 96-point social momentum score, the hidden admin function flagged by T04 was sufficient to SKIP. Outcome confirmed the override was correct — reinforces Risk Gate priority over Opportunity Score." },
    { tokenId: byName.CBFX.id, paperTradeId: trades[5].id, patternType: "skip", title: "Honeypot simulation prevented total capital loss", description: "Automated sell-simulation caught the honeypot before any capital was risked. Deployer-cluster cross-reference (T05) added independent confirmation." },
  ]);

  await db.insert(alerts).values([
    { tokenId: byName.SOLV.id, type: "discovery", severity: "info", title: "New candidate discovered: Solvent Protocol (SOLV)", message: "Opportunity score 88/100. Whale accumulation and dev activity converge within the first week of launch.", isRead: false, sentToTelegram: true },
    { tokenId: byName.CBFX.id, type: "security", severity: "critical", title: "Critical security risk: Cobalt Fox (CBFX)", message: "Confirmed honeypot. Sell function restricted. Risk Gate rejected this candidate automatically.", isRead: false, sentToTelegram: true },
    { tokenId: byName.VGRD.id, type: "whale", severity: "warning", title: "Whale accumulation streak: Vector Grid (VGRD)", message: "9 consecutive days of net whale accumulation detected with no distribution events.", isRead: true, sentToTelegram: true },
    { tokenId: byName.AURM.id, type: "exit", severity: "info", title: "Paper trade closed: Aurora Mesh (AURM)", message: "Closed +14.4% after 7 days. Target 1 hit, thesis validated by audit + peer comparison.", isRead: true, sentToTelegram: true },
    { tokenId: null, type: "daily_report", severity: "info", title: "Daily Intelligence Report ready", message: "2 new candidates discovered, 1 rejected, 1 trade closed in profit, 1 correct skip confirmed.", isRead: false, sentToTelegram: true },
    { tokenId: byName.NSHD.id, type: "news", severity: "warning", title: "Unverified rumor detected: Nightshade (NSHD)", message: "Listing rumor circulating on Telegram is UNVERIFIED. No independent source has confirmed it.", isRead: false, sentToTelegram: false },
  ]);

  await db.insert(systemComponents).values([
    { name: "Market Data Provider (Primary)", category: "Market Data", status: "operational", latencyMs: 142, uptimePercent: "99.94", message: "DEX Screener + GeckoTerminal aggregation nominal." },
    { name: "Market Data Provider (Fallback)", category: "Market Data", status: "operational", latencyMs: 210, uptimePercent: "99.80", message: "CoinGecko fallback on standby." },
    { name: "On-Chain Indexer — Solana", category: "Blockchain", status: "operational", latencyMs: 305, uptimePercent: "99.61", message: "Wallet & holder indexing nominal." },
    { name: "On-Chain Indexer — EVM", category: "Blockchain", status: "degraded", latencyMs: 940, uptimePercent: "97.20", message: "Elevated latency from a public RPC fallback endpoint." },
    { name: "Security Scanner (Honeypot Sim)", category: "Security", status: "operational", latencyMs: 480, uptimePercent: "99.98", message: "All simulations completing within SLA." },
    { name: "Social Listener — X/Telegram", category: "Social", status: "operational", latencyMs: 260, uptimePercent: "99.10", message: "Rate limits nominal." },
    { name: "News Aggregator", category: "News", status: "operational", latencyMs: 190, uptimePercent: "99.87", message: "12 sources syncing normally." },
    { name: "AI Council Orchestrator", category: "AI", status: "operational", latencyMs: 620, uptimePercent: "99.40", message: "10/10 teams responding within budget." },
    { name: "Telegram Bot Gateway", category: "Interface", status: "operational", latencyMs: 88, uptimePercent: "99.99", message: "Webhook healthy." },
    { name: "n8n Automation Layer", category: "Automation", status: "operational", latencyMs: 55, uptimePercent: "99.95", message: "14 workflows active, 0 failing executions in last 24h." },
    { name: "Learning Engine", category: "AI", status: "operational", latencyMs: 340, uptimePercent: "99.50", message: "Post-mortem queue empty; last run 6 minutes ago." },
    { name: "Scheduler", category: "Core", status: "operational", latencyMs: 12, uptimePercent: "100.00", message: "All cron jobs on schedule." },
  ]);

  await db.insert(systemLogs).values([
    { level: "info", component: "Scheduler", message: "Discovery cycle completed — 1,204 candidates screened, 8 promoted to full analysis." },
    { level: "warning", component: "On-Chain Indexer — EVM", message: "Public RPC endpoint latency exceeded 800ms threshold; failover candidate queued." },
    { level: "error", component: "Social Listener — X/Telegram", message: "Rate limit hit on secondary API key; automatically rotated to backup key." },
    { level: "info", component: "AI Council Orchestrator", message: "Council debate completed for SOLV in 8.2s across 10 teams." },
    { level: "info", component: "Learning Engine", message: "Post-mortem generated for closed trade HLCY — failure pattern logged." },
    { level: "info", component: "n8n Automation Layer", message: "Workflow 'daily-report-builder' executed successfully." },
  ]);

  await db.insert(chatMessages).values([
    { role: "user", content: "بهترین فرصت امروز چیه؟" },
    { role: "assistant", content: "بر اساس آخرین تحلیل شورا، توکن Solvent Protocol (SOLV) با Opportunity Score 88 و Confidence 76 در صدر قرار دارد. دلایل اصلی: تجمع نهنگ‌ها طی ۷۲ ساعت گذشته، رشد نقدینگی ۳.۱ برابری، و فعالیت غیرعادی توسعه‌دهندگان در GitHub. توجه: توکن هنوز ۶ روز از لانچ آن گذشته و Audit آن هنوز منتشر نشده — این یک ریسک باقی‌مانده است." },
  ]);

  await db.insert(settings).values([
    { key: "telegram", value: { botConnected: false, chatId: "", dailyReportEnabled: true, alertTypes: ["discovery", "security", "exit", "daily_report"] } },
    { key: "notifications", value: { minOpportunityScore: 70, minConfidence: 60, criticalSecurityOnly: false } },
    { key: "ai_providers", value: { primary: "local-reasoning-engine", fallbacks: ["openai", "anthropic", "gemini"] } },
    { key: "risk_gate", value: { maxAcceptableRisk: "medium", autoRejectCritical: true } },
    { key: "budget", value: { monthlyUsd: 0, infrastructure: "local + free tiers only" } },
  ]);

  console.log("Seed complete.");
}

function daysAgo(n: number) {
  return new Date(Date.now() - n * 86400000);
}
function daysAhead(n: number) {
  return new Date(Date.now() + n * 86400000);
}

function scoreRow(
  tokenId: number,
  o: {
    opportunityScore: number; securityScore: number; liquidityScore: number; socialMomentum: number;
    whaleScore: number; narrativeScore: number; evidenceScore: number; confidence: number;
    councilDecision: "strong_buy" | "watch" | "insufficient_evidence" | "reject" | "skip";
    bull: string; base: string; bear: string; extreme: string; why: string[]; risks: string[]; reject: string[];
  }
) {
  return {
    tokenId,
    opportunityScore: o.opportunityScore,
    securityScore: o.securityScore,
    liquidityScore: o.liquidityScore,
    socialMomentum: o.socialMomentum,
    whaleScore: o.whaleScore,
    narrativeScore: o.narrativeScore,
    evidenceScore: o.evidenceScore,
    confidence: o.confidence,
    councilDecision: o.councilDecision,
    bullScenario: o.bull,
    baseScenario: o.base,
    bearScenario: o.bear,
    extremeRiskScenario: o.extreme,
    whyPoints: o.why,
    riskPoints: o.risks,
    rejectConditions: o.reject,
  };
}

function secRow(
  tokenId: number,
  s: {
    riskLevel: "low" | "medium" | "high" | "critical"; honeypot: boolean; buyTax: string; sellTax: string;
    mint: boolean; freeze: boolean; renounced: boolean; locked: boolean; lpLock: string; topHolder: string;
    rugHistory: boolean; hiddenAdmin: boolean; flags: string[]; notes: string;
  }
) {
  return {
    tokenId,
    riskLevel: s.riskLevel,
    honeypot: s.honeypot,
    buyTaxPercent: s.buyTax,
    sellTaxPercent: s.sellTax,
    mintAuthority: s.mint,
    freezeAuthority: s.freeze,
    ownershipRenounced: s.renounced,
    liquidityLocked: s.locked,
    lpLockPercent: s.lpLock,
    topHolderConcentration: s.topHolder,
    deployerRugHistory: s.rugHistory,
    hiddenAdminFunctions: s.hiddenAdmin,
    flags: s.flags,
    notes: s.notes,
  };
}

function ev(
  tokenId: number,
  sourceType: "market" | "onchain" | "social" | "news" | "development" | "rumor" | "security",
  sourceName: string,
  title: string,
  verification: "verified" | "unverified" | "rumor" | "conflicted",
  impact: "positive" | "negative" | "neutral"
) {
  return { tokenId, sourceType, sourceName, title, url: null, verification, impact };
}

function oc(tokenId: number, eventType: string, wallet: string, amountUsd: number, description: string) {
  return { tokenId, eventType, walletAddress: wallet, amountUsd: String(amountUsd), description };
}

function trade(
  tokenId: number,
  t: {
    status: "open" | "closed"; outcome: "pending" | "win" | "loss" | "skip"; entry: string; exit: string | null;
    capital: string; size: string; stop: string | null; t1: string | null; t2: string | null; t3: string | null;
    hold: number; reason: string; opened: Date; closed?: Date; pnlUsd?: string; pnlPercent?: string; post?: string;
  }
) {
  return {
    tokenId,
    status: t.status,
    outcome: t.outcome,
    entryPrice: t.entry,
    exitPrice: t.exit,
    virtualCapitalUsd: t.capital,
    positionSizeUsd: t.size,
    stopLoss: t.stop,
    target1: t.t1,
    target2: t.t2,
    target3: t.t3,
    maxHoldingHours: t.hold,
    pnlUsd: t.pnlUsd ?? "0",
    pnlPercent: t.pnlPercent ?? "0",
    reason: t.reason,
    postMortem: t.post ?? null,
    openedAt: t.opened,
    closedAt: t.closed ?? null,
  };
}

seed()
  .then(async () => {
    await pool.end();
    process.exit(0);
  })
  .catch(async (err) => {
    console.error(err);
    await pool.end();
    process.exit(1);
  });
