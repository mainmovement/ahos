import { db } from "@/db";
import {
  alerts,
  auditLog,
  chatMessages,
  councilVotes,
  dailyReports,
  evidence,
  githubItems,
  learningRecords,
  newsItems,
  onchainEvents,
  paperTrades,
  securityFindings,
  settings,
  socialSignals,
  systemComponents,
  telegramMessages,
  tokenScores,
  tokens,
  whaleMoves,
} from "@/db/schema";

const ago = (hours: number) => new Date(Date.now() - hours * 3600_000);

export async function seedAhos() {
  const inserted = await db
    .insert(tokens)
    .values([
      {
        slug: "goldenfruit",
        name: "Goldenfruit",
        symbol: "GLDN",
        chain: "Solana",
        contract: "GldnFru1tAH0sX7k9m2PqR4sT6uVwXyZaBcDeFgHiJ",
        tokenGroup: "newly_launched",
        launchDate: ago(36),
        liquidityUsd: 428000,
        marketCapUsd: 2100000,
        volumeUsd: 910000,
        priceUsd: 0.0214,
        holders: 1840,
        status: "paper",
        narrative: "AI × DePIN",
        summary:
          "Exceptional candidate. Independent liquidity inflow, organic holder growth, and a coherent DePIN narrative. Security gate passed with residual mint-authority watch.",
        accent: "#f3d5a0",
      },
      {
        slug: "rootnet",
        name: "Rootnet",
        symbol: "ROOT",
        chain: "Ethereum",
        contract: "0x4a11c8e2b7d04f9e1c6a0f3b8d2e7c91aa55e0b1",
        tokenGroup: "pre_launch",
        launchDate: ago(-72),
        liquidityUsd: 0,
        marketCapUsd: 0,
        volumeUsd: 0,
        priceUsd: 0,
        holders: 0,
        status: "investigate",
        narrative: "Infrastructure",
        summary:
          "Pre-launch. GitHub commits are real, but liquidity venue is unconfirmed. Treat all launch timing claims as UNVERIFIED.",
        accent: "#6ee7f9",
      },
      {
        slug: "veil",
        name: "Veil Protocol",
        symbol: "VEIL",
        chain: "Base",
        contract: "0x9c22d4e2a11b8f0d77c3a9e4b1f6d8c0aa12bb34",
        tokenGroup: "hidden",
        launchDate: ago(24 * 40),
        liquidityUsd: 186000,
        marketCapUsd: 740000,
        volumeUsd: 42000,
        priceUsd: 0.084,
        holders: 620,
        status: "watch",
        narrative: "Privacy",
        summary:
          "Quiet existing token with a new catalyst rumor. Volume is thin. Evidence score is limited — SKIP unless independent confirmation arrives.",
        accent: "#c4b5fd",
      },
      {
        slug: "nexus-ai",
        name: "Nexus AI",
        symbol: "NXAI",
        chain: "Solana",
        contract: "NxAiPump111111AH0sNarrativeTrap2222222222",
        tokenGroup: "newly_launched",
        launchDate: ago(8),
        liquidityUsd: 99000,
        marketCapUsd: 5600000,
        volumeUsd: 2400000,
        priceUsd: 0.112,
        holders: 4200,
        status: "reject",
        narrative: "AI Meme",
        summary:
          "Violent social velocity with clustered wallets and a sell tax that can be raised. High opportunity optics, critical security risk — REJECT.",
        accent: "#fb7185",
      },
      {
        slug: "driftleaf",
        name: "Driftleaf",
        symbol: "LEAF",
        chain: "BNB Chain",
        contract: "0x71aa00bbcd445ef00112233445566778899aabb",
        tokenGroup: "newly_launched",
        launchDate: ago(20),
        liquidityUsd: 260000,
        marketCapUsd: 980000,
        volumeUsd: 310000,
        priceUsd: 0.0091,
        holders: 1102,
        status: "investigate",
        narrative: "RWA",
        summary:
          "Whale accumulation looks real. LP lock is 6 months. Developer wallet history is mixed — one previous abandoned token.",
        accent: "#4ade80",
      },
      {
        slug: "shadowmint",
        name: "Shadowmint",
        symbol: "SHDW",
        chain: "Ethereum",
        contract: "0xdead0000honeyp0t0000ahos0000reject0001",
        tokenGroup: "newly_launched",
        launchDate: ago(5),
        liquidityUsd: 44000,
        marketCapUsd: 3100000,
        volumeUsd: 1800000,
        priceUsd: 0.33,
        holders: 890,
        status: "reject",
        narrative: "Meme",
        summary:
          "Classic honeypot pattern: buy succeeds, sell reverts for non-whitelisted wallets. Risk gate fired. Do not approach.",
        accent: "#ff4d6d",
      },
      {
        slug: "lumina",
        name: "Lumina",
        symbol: "LUMI",
        chain: "Base",
        contract: "0x55aa11bb22cc33dd44ee55ff66aa77bb88cc99",
        tokenGroup: "hidden",
        launchDate: ago(24 * 18),
        liquidityUsd: 510000,
        marketCapUsd: 1650000,
        volumeUsd: 88000,
        priceUsd: 0.041,
        holders: 2400,
        status: "investigate",
        narrative: "Gaming",
        summary:
          "Council is split. On-chain is constructive, social is quiet, news is thin. Confidence remains moderate by design.",
        accent: "#f0c27a",
      },
      {
        slug: "depin-core",
        name: "Depin Core",
        symbol: "DCORE",
        chain: "Solana",
        contract: "DpCoreAH0s111111111111111111111111111111",
        tokenGroup: "newly_launched",
        launchDate: ago(60),
        liquidityUsd: 340000,
        marketCapUsd: 1280000,
        volumeUsd: 190000,
        priceUsd: 0.016,
        holders: 1560,
        status: "paper",
        narrative: "DePIN",
        summary:
          "Hardware partnership rumor tagged UNVERIFIED. Independent holder growth and LP adds are confirmed. Paper book opened small.",
        accent: "#5ce1e6",
      },
      {
        slug: "echovault",
        name: "Echo Vault",
        symbol: "ECHO",
        chain: "Ethereum",
        contract: "0x0ec00aa11bb22cc33dd44ee55ff66aa77bb88",
        tokenGroup: "hidden",
        launchDate: ago(24 * 90),
        liquidityUsd: 720000,
        marketCapUsd: 4100000,
        volumeUsd: 125000,
        priceUsd: 0.22,
        holders: 3800,
        status: "watch",
        narrative: "DeFi",
        summary:
          "Existing protocol with a new vault design. Not early, but not crowded. Wait for the audit artifact before raising size.",
        accent: "#93c5fd",
      },
      {
        slug: "aurora-seed",
        name: "Aurora Seed",
        symbol: "AUR",
        chain: "Solana",
        contract: "AurSeedAH0sPreLaunch1111111111111111111",
        tokenGroup: "pre_launch",
        launchDate: ago(-24),
        liquidityUsd: 12000,
        marketCapUsd: 0,
        volumeUsd: 0,
        priceUsd: 0,
        holders: 48,
        status: "watch",
        narrative: "AI",
        summary:
          "Stealth LP crumbs on a new mint. Community is tiny and real. Launch window claimed for tomorrow — treat as RUMOR until the pool is live.",
        accent: "#fde68a",
      },
    ])
    .returning();

  const id = Object.fromEntries(inserted.map((t) => [t.slug, t.id]));

  await db.insert(tokenScores).values([
    { tokenId: id.goldenfruit, opportunity: 88, security: 81, liquidity: 74, social: 71, whale: 79, narrative: 84, evidence: 82, confidence: 76, decision: "paper", thesis: "Multiple independent confirmations. Residual mint authority is monitored, not ignored." },
    { tokenId: id.rootnet, opportunity: 73, security: 68, liquidity: 12, social: 44, whale: 20, narrative: 70, evidence: 51, confidence: 42, decision: "investigate", thesis: "Architecture looks serious. Launch venue and LP plan remain UNKNOWN." },
    { tokenId: id.veil, opportunity: 61, security: 77, liquidity: 48, social: 28, whale: 55, narrative: 63, evidence: 40, confidence: 38, decision: "skip", thesis: "Insufficient evidence. Quiet is not the same as undervalued." },
    { tokenId: id["nexus-ai"], opportunity: 86, security: 18, liquidity: 41, social: 92, whale: 33, narrative: 80, evidence: 36, confidence: 22, decision: "reject", thesis: "High opportunity + critical security risk = REJECT. Risk gate holds." },
    { tokenId: id.driftleaf, opportunity: 77, security: 64, liquidity: 66, social: 52, whale: 81, narrative: 69, evidence: 67, confidence: 61, decision: "investigate", thesis: "Whale flow is the lead signal. Developer history is the drag." },
    { tokenId: id.shadowmint, opportunity: 70, security: 4, liquidity: 22, social: 74, whale: 15, narrative: 40, evidence: 88, confidence: 91, decision: "reject", thesis: "Honeypot confirmed by simulated sell. Confidence is high on the REJECT." },
    { tokenId: id.lumina, opportunity: 69, security: 80, liquidity: 72, social: 35, whale: 48, narrative: 58, evidence: 57, confidence: 54, decision: "investigate", thesis: "Council debate is the signal. Do not collapse into a single score." },
    { tokenId: id["depin-core"], opportunity: 81, security: 76, liquidity: 70, social: 60, whale: 64, narrative: 83, evidence: 63, confidence: 58, decision: "paper", thesis: "Narrative is hot. Partnership claim is UNVERIFIED. Size stays small." },
    { tokenId: id.echovault, opportunity: 58, security: 84, liquidity: 78, social: 31, whale: 42, narrative: 50, evidence: 71, confidence: 64, decision: "watch", thesis: "Quality without urgency. Wait for the audit artifact." },
    { tokenId: id["aurora-seed"], opportunity: 72, security: 60, liquidity: 8, social: 26, whale: 10, narrative: 66, evidence: 34, confidence: 29, decision: "watch", thesis: "Too early. Roots just touched soil." },
  ]);

  await db.insert(evidence).values([
    { tokenId: id.goldenfruit, source: "DEX Screener", kind: "market", label: "Liquidity inflow +$180k / 12h", detail: "Two independent LP adds from unrelated wallets. Volume/MC ratio cooling after a spike — healthier than a pure pump print.", verification: "confirmed", weight: 82 },
    { tokenId: id.goldenfruit, source: "GitHub", kind: "dev", label: "14 commits / 7d from two known contributors", detail: "Repos are Apache-2.0. Commit messages match the public roadmap. Not a copied skeleton.", verification: "confirmed", weight: 74 },
    { tokenId: id.goldenfruit, source: "Telegram", kind: "social", label: "Insider launch timing claim", detail: "Anonymous claim of a CEX listing next week. Logged as RUMOR. No independent confirmation.", verification: "rumor", weight: 20 },
    { tokenId: id.rootnet, source: "GitHub", kind: "dev", label: "Original architecture, 11 contributors", detail: "Non-trivial rust + typescript monorepo. License MIT. Tests exist. Launch script is incomplete.", verification: "confirmed", weight: 70 },
    { tokenId: id.rootnet, source: "X", kind: "social", label: "Launch date tweet", detail: "A personal account claimed 'mainnet Friday'. Account age 11 days. UNVERIFIED.", verification: "unverified", weight: 15 },
    { tokenId: id.veil, source: "Explorer", kind: "onchain", label: "Top 10 holders 38%", detail: "Concentration is acceptable. No clustered deployer satellites detected in first pass.", verification: "confirmed", weight: 60 },
    { tokenId: id["nexus-ai"], source: "X", kind: "social", label: "Mention velocity +940% / 6h", detail: "Burst is real in count, fake in uniqueness. 61% of amplifying accounts created this week.", verification: "conflicted", weight: 30 },
    { tokenId: id["nexus-ai"], source: "Security heuristics", kind: "security", label: "Mutable sell tax 0–45%", detail: "Owner can change tax without timelock. This is an attack surface, not a feature.", verification: "confirmed", weight: 95 },
    { tokenId: id.driftleaf, source: "Wallet graph", kind: "whale", label: "Smart wallet 0x8c… accumulated", detail: "A wallet with prior profitable RWA entries bought 4.2% over 9 hours without bundling.", verification: "confirmed", weight: 78 },
    { tokenId: id.shadowmint, source: "Sell simulation", kind: "security", label: "Sell reverts for fresh wallets", detail: "Buy succeeds. Sell fails with a whitelist modifier. Honeypot classification is not a rumor.", verification: "confirmed", weight: 99 },
    { tokenId: id.lumina, source: "GeckoTerminal", kind: "market", label: "Range-bound, rising holders", detail: "Price quiet. Holder count +12% in 10 days. Classic hidden profile — or simply ignored.", verification: "confirmed", weight: 58 },
    { tokenId: id["depin-core"], source: "Project blog", kind: "news", label: "Hardware partner named", detail: "Blog post names a manufacturer. Manufacturer has not confirmed. UNVERIFIED catalyst.", verification: "unverified", weight: 28 },
    { tokenId: id.echovault, source: "Docs", kind: "dev", label: "New vault design published", detail: "Design is coherent. Audit is 'in progress' with no artifact. UNKNOWN until PDF exists.", verification: "confirmed", weight: 65 },
    { tokenId: id["aurora-seed"], source: "DEX", kind: "market", label: "Stealth LP $12k", detail: "Tiny pool, one LP provider, likely the deployer. Not a market yet.", verification: "confirmed", weight: 40 },
  ]);

  const stances: Record<string, { no: number; name: string; stance: string; c: number; why: string }[]> = {
    goldenfruit: [
      { no: 1, name: "Mathematical Intelligence", stance: "bullish", c: 74, why: "Volume anomaly is two-sigma but decaying — more impulse than blow-off." },
      { no: 2, name: "Crypto Market Intelligence", stance: "bullish", c: 77, why: "LP structure and MC/Liq ratio are tradable, not cartoonish." },
      { no: 3, name: "Blockchain & On-Chain", stance: "bullish", c: 80, why: "Holder growth is unclustered. Deployer sold 0 after launch." },
      { no: 4, name: "Cybersecurity & Hacker Intel", stance: "neutral", c: 71, why: "Mint authority still live. Not a honeypot. Watch, do not ignore." },
      { no: 5, name: "Investigative Intelligence", stance: "bullish", c: 69, why: "Identities on GitHub match prior non-rugged work." },
      { no: 6, name: "News & Journalism", stance: "neutral", c: 55, why: "No quality press. Silence is not confirmation." },
      { no: 7, name: "Social & Narrative", stance: "bullish", c: 68, why: "Narrative is real; amplification is not yet industrial." },
      { no: 8, name: "Technology & Engineering", stance: "bullish", c: 76, why: "Code is not a fork-and-rename." },
      { no: 9, name: "AI Research & Self-Evolution", stance: "bullish", c: 64, why: "Feature set is narrow enough to be true." },
      { no: 10, name: "Strategic Decision & Red Team", stance: "neutral", c: 72, why: "If mint is abused, thesis dies. Paper only until freeze/mint is revoked." },
    ],
    "nexus-ai": [
      { no: 1, name: "Mathematical Intelligence", stance: "bearish", c: 60, why: "Social and price series are too synchronous — manufactured." },
      { no: 2, name: "Crypto Market Intelligence", stance: "bearish", c: 66, why: "MC outran liquidity. Exit path is a story, not a market." },
      { no: 3, name: "Blockchain & On-Chain", stance: "bearish", c: 80, why: "Bundled wallets. Deployer still holds 18%." },
      { no: 4, name: "Cybersecurity & Hacker Intel", stance: "reject", c: 94, why: "Mutable tax + owner blacklist. This is a weapon." },
      { no: 5, name: "Investigative Intelligence", stance: "reject", c: 88, why: "Deployer cluster matches two prior rugs." },
      { no: 6, name: "News & Journalism", stance: "bearish", c: 50, why: "Coverage is recap of tweets, not reporting." },
      { no: 7, name: "Social & Narrative", stance: "bearish", c: 85, why: "Engagement is not users. It is inventory." },
      { no: 8, name: "Technology & Engineering", stance: "bearish", c: 70, why: "Repo is a template with README AI slop." },
      { no: 9, name: "AI Research & Self-Evolution", stance: "reject", c: 78, why: "Product claims are unfalsifiable." },
      { no: 10, name: "Strategic Decision & Red Team", stance: "reject", c: 96, why: "If every bullish team is wrong, you lose 100%. Gate." },
    ],
    lumina: [
      { no: 1, name: "Mathematical Intelligence", stance: "neutral", c: 52, why: "No statistically significant impulse. Range is honest." },
      { no: 2, name: "Crypto Market Intelligence", stance: "bullish", c: 61, why: "Liquidity is sufficient for a small book." },
      { no: 3, name: "Blockchain & On-Chain", stance: "bullish", c: 58, why: "Slow accumulation, no distribution." },
      { no: 4, name: "Cybersecurity & Hacker Intel", stance: "bullish", c: 80, why: "Renounced, LP locked, no blacklist." },
      { no: 5, name: "Investigative Intelligence", stance: "neutral", c: 50, why: "Team is pseudonymous with a thin trail." },
      { no: 6, name: "News & Journalism", stance: "neutral", c: 40, why: "No news is not good news. It is no news." },
      { no: 7, name: "Social & Narrative", stance: "bearish", c: 45, why: "Community is asleep. Narratives need oxygen." },
      { no: 8, name: "Technology & Engineering", stance: "neutral", c: 57, why: "Unity client exists. Shipping cadence is slow." },
      { no: 9, name: "AI Research & Self-Evolution", stance: "neutral", c: 48, why: "Insufficient evidence to update priors hard." },
      { no: 10, name: "Strategic Decision & Red Team", stance: "neutral", c: 66, why: "Disagreement is the signal. Do not force consensus." },
    ],
  };

  const councilRows = Object.entries(stances).flatMap(([slug, votes]) =>
    votes.map((v) => ({
      tokenId: id[slug],
      teamNo: v.no,
      teamName: v.name,
      stance: v.stance,
      confidence: v.c,
      rationale: v.why,
    })),
  );
  await db.insert(councilVotes).values(councilRows);

  await db.insert(paperTrades).values([
    { tokenId: id.goldenfruit, side: "long", entry: 0.0188, capital: 250, size: 13297, stop: 0.0141, target1: 0.026, target2: 0.034, target3: 0.05, status: "open", pnlUsd: 34.6, pnlPct: 13.84, notes: "Mint authority is the kill switch. Trail after T1." },
    { tokenId: id["depin-core"], side: "long", entry: 0.0142, capital: 150, size: 10563, stop: 0.011, target1: 0.02, target2: 0.028, target3: 0.04, status: "open", pnlUsd: 19.05, pnlPct: 12.7, notes: "Partnership remains UNVERIFIED. Size capped." },
    { tokenId: id.driftleaf, side: "long", entry: 0.0104, capital: 100, size: 9615, stop: 0.0082, target1: 0.014, target2: 0.018, target3: 0.024, status: "closed", pnlUsd: -12.5, pnlPct: -12.5, closedAt: ago(6), notes: "Stopped. Developer dump overlapped whale bid. Post-mortem filed." },
    { tokenId: id.echovault, side: "long", entry: 0.19, capital: 200, size: 1052, stop: 0.16, target1: 0.24, target2: 0.3, target3: 0.38, status: "closed", pnlUsd: 31.6, pnlPct: 15.8, closedAt: ago(48), notes: "T1 hit. Remainder skipped — audit still missing." },
  ]);

  await db.insert(securityFindings).values([
    { tokenId: id.goldenfruit, severity: "medium", title: "Mint authority still active", detail: "Owner can mint. Not currently abused. Revocation is a thesis upgrade.", gate: "watch" },
    { tokenId: id.goldenfruit, severity: "low", title: "Freeze authority revoked", detail: "Freeze is dead. Positive." , gate: "pass" },
    { tokenId: id["nexus-ai"], severity: "critical", title: "Mutable tax + blacklist", detail: "Owner can brick sellers. Risk gate REJECT.", gate: "reject" },
    { tokenId: id["nexus-ai"], severity: "high", title: "LP not locked", detail: "LP tokens sit in the deployer wallet.", gate: "reject" },
    { tokenId: id.shadowmint, severity: "critical", title: "Honeypot — sell revert", detail: "Whitelist modifier on transfer. Confirmed by simulation.", gate: "reject" },
    { tokenId: id.driftleaf, severity: "medium", title: "Prior abandoned token by deployer", detail: "Not a rug, but a stain. Reduce confidence.", gate: "watch" },
    { tokenId: id.lumina, severity: "low", title: "Renounced + LP lock 12 months", detail: "Clean enough for paper.", gate: "pass" },
    { tokenId: id.rootnet, severity: "medium", title: "Proxy not yet frozen", detail: "Upgradeable pre-launch. Expected, still a risk.", gate: "watch" },
    { tokenId: id.echovault, severity: "low", title: "Standard ERC-20, no hidden mint", detail: "Verified source. Owner limited.", gate: "pass" },
    { tokenId: id["aurora-seed"], severity: "high", title: "Single LP provider = deployer", detail: "Liquidity is a prop, not a market.", gate: "watch" },
  ]);

  await db.insert(whaleMoves).values([
    { tokenId: id.goldenfruit, wallet: "7xSmart…AH0s", action: "accumulate", amountUsd: 64000, note: "Three buys, no dump, 4h spacing." },
    { tokenId: id.driftleaf, wallet: "0x8c21…aa90", action: "accumulate", amountUsd: 41000, note: "Known RWA wallet, unbundled." },
    { tokenId: id["nexus-ai"], wallet: "bundle-17", action: "distribute", amountUsd: 120000, note: "Clustered exits into retail bid." },
    { tokenId: id.lumina, wallet: "0x44aa…1102", action: "accumulate", amountUsd: 18000, note: "Slow drip over 6 days." },
    { tokenId: id["depin-core"], wallet: "So1anaWhale9", action: "accumulate", amountUsd: 27500, note: "First touch of this mint." },
  ]);

  await db.insert(onchainEvents).values([
    { tokenId: id.goldenfruit, kind: "lp_add", wallet: "LP-2", amountUsd: 90000, note: "Second independent LP add." },
    { tokenId: id.goldenfruit, kind: "holders", wallet: "network", amountUsd: 0, note: "Holders 1.4k → 1.84k." },
    { tokenId: id.shadowmint, kind: "failed_sell", wallet: "probe", amountUsd: 50, note: "Fresh wallet sell reverted." },
    { tokenId: id.rootnet, kind: "deploy", wallet: "dev", amountUsd: 0, note: "Implementation deployed, proxy pending." },
    { tokenId: id["depin-core"], kind: "transfer", wallet: "treasury", amountUsd: 12000, note: "Treasury to LP, not to CEX." },
    { tokenId: id.echovault, kind: "contract_event", wallet: "vault", amountUsd: 0, note: "New vault initialized, unused." },
  ]);

  await db.insert(socialSignals).values([
    { tokenId: id.goldenfruit, platform: "X", metric: "mentions_1h", value: 48, velocity: 1.6, note: "Mostly builders, not raid replies.", authenticity: "organic" },
    { tokenId: id["nexus-ai"], platform: "X", metric: "mentions_1h", value: 920, velocity: 9.4, note: "Raid pattern, new accounts.", authenticity: "synthetic" },
    { tokenId: id["depin-core"], platform: "Telegram", metric: "unique_chatters", value: 210, velocity: 1.2, note: "Questions > emojis. Healthy.", authenticity: "organic" },
    { tokenId: id.lumina, platform: "Discord", metric: "daily_actives", value: 40, velocity: 0.8, note: "Quiet guild. Not dead, not alive.", authenticity: "organic" },
    { tokenId: id.veil, platform: "Reddit", metric: "posts_7d", value: 3, velocity: 0.4, note: "Almost no oxygen.", authenticity: "organic" },
    { tokenId: id.shadowmint, platform: "Telegram", metric: "join_velocity", value: 1400, velocity: 12, note: "Bought members. Classic.", authenticity: "synthetic" },
  ]);

  await db.insert(newsItems).values([
    { tokenId: id.goldenfruit, title: "Independent researcher maps Goldenfruit LP inflows", source: "On-chain desk", summary: "Two LP wallets with no prior overlap added size. Not an official announcement.", url: "#", sentiment: "bullish", verification: "confirmed" },
    { tokenId: id["depin-core"], title: "Depin Core names a hardware partner", source: "Project blog", summary: "The manufacturer has not confirmed. Catalogued as UNVERIFIED catalyst.", url: "#", sentiment: "neutral", verification: "unverified" },
    { tokenId: id["nexus-ai"], title: "Influencer wave hits NXAI", source: "X recap blogs", summary: "Syndication of the same screenshot. Not journalism.", url: "#", sentiment: "bullish", verification: "rumor" },
    { tokenId: null, title: "Solana memecoin wash-trading desk taken down", source: "Industry wire", summary: "Useful prior: synthetic social + bundled wallets remain the dominant trap.", url: "#", sentiment: "bearish", verification: "confirmed" },
    { tokenId: id.echovault, title: "Echo Vault design notes published", source: "Official docs", summary: "Technical, not promotional. Audit still missing.", url: "#", sentiment: "neutral", verification: "confirmed" },
    { tokenId: id.rootnet, title: "Anonymous 'mainnet Friday' claim", source: "X", summary: "Account age 11 days. RUMOR.", url: "#", sentiment: "bullish", verification: "rumor" },
  ]);

  await db.insert(alerts).values([
    { tokenId: id.goldenfruit, kind: "opportunity", severity: "high", title: "GLDN — paper book in profit +13.8%", body: "T1 not yet tagged. Mint authority still live. Hold rules unchanged." },
    { tokenId: id.shadowmint, kind: "security", severity: "critical", title: "SHDW classified honeypot", body: "Sell simulation reverted. Risk gate REJECT. Do not open a book." },
    { tokenId: id["nexus-ai"], kind: "security", severity: "critical", title: "NXAI risk gate fired", body: "Mutable tax + deployer LP. High opportunity ignored." },
    { tokenId: id.driftleaf, kind: "exit", severity: "medium", title: "LEAF paper stopped −12.5%", body: "Post-mortem queued. Developer dump vs whale bid." },
    { tokenId: id["depin-core"], kind: "whale", severity: "medium", title: "New smart wallet in DCORE", body: "First-touch accumulation $27.5k. Partnership still UNVERIFIED." },
    { tokenId: id["aurora-seed"], kind: "discovery", severity: "low", title: "New pre-launch crumb: AUR", body: "Stealth LP $12k. Group A. Watch only." },
    { tokenId: null, kind: "system", severity: "low", title: "Social provider degraded 14m", body: "X public path rate-limited. Fallback to Telegram export active." },
  ]);

  await db.insert(systemComponents).values([
    { key: "market.dexscreener", name: "DEX Screener", layer: "MarketData", status: "ok", provider: "DEX Screener", latencyMs: 420, note: "Primary market path." },
    { key: "market.gecko", name: "GeckoTerminal", layer: "MarketData", status: "ok", provider: "GeckoTerminal", latencyMs: 610, note: "Fallback ready." },
    { key: "chain.solana", name: "Solana RPC", layer: "Blockchain", status: "ok", provider: "Public RPC", latencyMs: 180, note: "Free tier." },
    { key: "chain.evm", name: "EVM RPC", layer: "Blockchain", status: "degraded", provider: "Public RPC", latencyMs: 1400, note: "Rate-limited. Explorer fallback on." },
    { key: "news.rss", name: "Open RSS", layer: "News", status: "ok", provider: "RSS", latencyMs: 300, note: "Local parser." },
    { key: "social.x", name: "X public", layer: "Social", status: "degraded", provider: "Public", latencyMs: 2200, note: "Rate limit. Telegram fallback." },
    { key: "social.tg", name: "Telegram ingest", layer: "Social", status: "ok", provider: "Bot API", latencyMs: 240, note: "Local bot." },
    { key: "ai.council", name: "Council engine", layer: "AI", status: "ok", provider: "Local", latencyMs: 40, note: "Deterministic council + optional cloud." },
    { key: "sec.heuristics", name: "Security heuristics", layer: "Security", status: "ok", provider: "Local", latencyMs: 25, note: "Honeypot + tax + owner checks." },
    { key: "web.dashboard", name: "Web dashboard", layer: "Web", status: "ok", provider: "Next.js", latencyMs: 12, note: "This process." },
    { key: "db.postgres", name: "PostgreSQL", layer: "Database", status: "ok", provider: "Local", latencyMs: 4, note: "Drizzle ORM." },
    { key: "git.hub", name: "GitHub hub", layer: "Engineering", status: "ok", provider: "Local ledger", latencyMs: 8, note: "Issues/PRs mirrored in AHOS." },
  ]);

  await db.insert(settings).values([
    {
      key: "workspace",
      value: {
        owner: "AHOS Prime",
        mode: "single-user",
        budgetUsd: 0,
        audio: true,
        intensity: "cinematic",
        reducedMotion: false,
        telegramEnabled: true,
        paperDefaultUsd: 150,
        riskGate: true,
        language: "en",
      },
    },
  ]);

  await db.insert(chatMessages).values([
    { role: "system", content: "AHOS council online. Evidence before decision. Rumor is not fact." },
    { role: "user", content: "Best opportunity on the board?" },
    { role: "assistant", content: "Goldenfruit (GLDN) is the only name with independent LP inflows, unclustered holders, and a passing security gate. Mint authority is still live — that is why it is PAPER, not a larger book. Nexus AI looks louder and is REJECT. Shadowmint is a honeypot. If you want the argument, open the GLDN dossier." },
  ]);

  await db.insert(telegramMessages).values([
    { direction: "out", content: "AHOS daily: 1 exceptional (GLDN), 2 rejects (NXAI, SHDW), 2 open paper books, social provider degraded." },
    { direction: "in", content: "این توکن رو بررسی کن: SHDW" },
    { direction: "out", content: "SHDW — honeypot. Sell reverts. Risk gate REJECT. Do not buy. Confidence 91 on the reject." },
    { direction: "in", content: "چرا GLDN؟" },
    { direction: "out", content: "Why GLDN: independent LP adds, real GitHub, unclustered holders, freeze revoked. Residual risk: mint authority. Paper +13.8%." },
  ]);

  await db.insert(learningRecords).values([
    { tokenId: id.echovault, kind: "win", title: "ECHO T1 — taking partials was the lesson", insight: "The win was not the +15.8%. It was leaving when the audit artifact still did not exist. Greed would have converted a lesson into a giveback." },
    { tokenId: id.driftleaf, kind: "loss", title: "LEAF stop — developer history underweighted", insight: "Whale bid was real. Developer dump was also real. Team 05 flagged the abandoned prior token. The book sized as if that stain was cosmetic. It was not." },
    { tokenId: id.shadowmint, kind: "skip", title: "SHDW skip was a profitable non-trade", insight: "Not losing 100% is a result. The security layer must be allowed to veto a high opportunity score. Gate held." },
    { tokenId: id["nexus-ai"], kind: "skip", title: "Synthetic social is not demand", insight: "Mention velocity without unique aged accounts is inventory, not community. Team 07 was right; Team 02 almost got captured by the tape." },
  ]);

  await db.insert(githubItems).values([
    { kind: "doc", title: "AHOS Master Vision 1.0", body: "Foundational specification. Evidence before decision. Risk gate. Council. Paper loop. $0 budget. Single user.", status: "published" },
    { kind: "issue", title: "Provider abstraction for market data", body: "MarketDataProvider with DEX Screener primary, GeckoTerminal + CoinGecko fallback. No provider owns the architecture.", status: "open" },
    { kind: "issue", title: "Honeypot sell simulator for EVM + Solana", body: "Local simulation path. Must fail closed if RPC is degraded.", status: "open" },
    { kind: "pr", title: "Cinematic command surface + 3D chamber", body: "Web dashboard as the intelligence interface. Beauty must not sacrifice auditability.", status: "merged" },
    { kind: "commit", title: "seed: ten-token board with council votes", body: "Goldenfruit through Aurora Seed. Includes rejects and skips so the board is honest.", status: "main" },
    { kind: "doc", title: "No change without a record", body: "What / Why / How / Files / Tests / Risks / Dependencies / Future work.", status: "published" },
    { kind: "issue", title: "Telegram alert templates", body: "Discovery, high opportunity, security, exit, whale, news, daily, paper result.", status: "in_progress" },
  ]);

  await db.insert(dailyReports).values([
    {
      reportDate: new Date().toISOString().slice(0, 10),
      headline: "One golden fruit, two traps, a useful loss",
      body: "Discovery found Aurora Seed (pre-launch crumb) and kept Nexus AI / Shadowmint off the book. Goldenfruit remains the only exceptional name. Driftleaf paper stopped −12.5% — developer history was underweighted. Echo Vault win was taken at T1. Social provider degraded; Telegram fallback is live. Learning engine recorded one win, one loss, two skips.",
      metrics: { newOpportunities: 2, rejects: 2, openPaper: 2, closedPaper: 2, winRate: 50, pnlUsd: 72.75 },
    },
  ]);

  await db.insert(auditLog).values([
    { action: "BOOTSTRAP", detail: "AHOS local intelligence seeded. Phase 1 Token Discovery Intelligence." },
    { action: "RISK_GATE", detail: "NXAI and SHDW rejected despite high optics." },
    { action: "PAPER_OPEN", detail: "GLDN 250 USDT virtual. DCORE 150 USDT virtual." },
    { action: "LEARN", detail: "Post-mortem LEAF: developer stain is not cosmetic." },
  ]);
}

export async function resetAndSeed() {
  await db.delete(auditLog);
  await db.delete(dailyReports);
  await db.delete(githubItems);
  await db.delete(learningRecords);
  await db.delete(telegramMessages);
  await db.delete(chatMessages);
  await db.delete(settings);
  await db.delete(systemComponents);
  await db.delete(alerts);
  await db.delete(newsItems);
  await db.delete(socialSignals);
  await db.delete(onchainEvents);
  await db.delete(whaleMoves);
  await db.delete(securityFindings);
  await db.delete(paperTrades);
  await db.delete(councilVotes);
  await db.delete(evidence);
  await db.delete(tokenScores);
  await db.delete(tokens);
  await seedAhos();
}
