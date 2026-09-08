import { db } from "./index";
import { tokens, councilOpinions, paperTrades, learningLogs, githubWorkflows, systemLogs } from "./schema";
import { eq } from "drizzle-orm";

export async function seedDatabaseIfEmpty() {
  try {
    const existing = await db.select().from(tokens).limit(1);
    if (existing.length > 0) {
      return;
    }

    console.log("Seeding AHOS database...");

    // Insert Tokens
    const insertedTokens = await db.insert(tokens).values([
      {
        symbol: "AHOS-AI",
        name: "Synthetic Neural Network Agent",
        chain: "Solana",
        contractAddress: "7xKX3N8sP1zQ9mR4vL2wY8uT6jH1bF3aN5mP",
        category: "newly-launched",
        opportunityScore: 94,
        securityScore: 88,
        confidenceScore: 91,
        liquidityScore: 85,
        whaleScore: 92,
        socialScore: 90,
        narrativeScore: 98,
        evidenceScore: 89,
        price: "0.0425",
        priceChange24h: "142.8",
        liquidityUsd: "1850000",
        marketCapUsd: "8500000",
        volume24h: "4200000",
        holdersCount: 4120,
        status: "approved",
        narrative: "AI + Autonomous Agent Infrastructure",
        evidenceSummary: "Multi-source confirmation: On-chain liquidity locked for 24 months, 14 Smart Money wallets accumulated $420k, GitHub repo has active commits from top Rust dev, social velocity increased 340% organically.",
        risksSummary: "Moderate concentration in Top 5 non-deployer wallets (18.4%). Deployer ownership renounced.",
        bullScenario: "Reaches $0.25 on tier-1 CEX listing and mainnet agent orchestrator release.",
        baseScenario: "Consolidates around $0.06 - $0.09 with steady liquidity expansion.",
        bearScenario: "Pullback to $0.018 if overall Solana AI narrative cools down.",
      },
      {
        symbol: "NEURAL-DEP",
        name: "Neural DePIN Sensor Grid",
        chain: "Base",
        contractAddress: "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7",
        category: "hidden-opportunity",
        opportunityScore: 89,
        securityScore: 95,
        confidenceScore: 86,
        liquidityScore: 80,
        whaleScore: 87,
        socialScore: 78,
        narrativeScore: 92,
        evidenceScore: 85,
        price: "1.2800",
        priceChange24h: "34.2",
        liquidityUsd: "3400000",
        marketCapUsd: "18200000",
        volume24h: "2100000",
        holdersCount: 8920,
        status: "approved",
        narrative: "DePIN + Physical AI Hardware",
        evidenceSummary: "1200 active physical sensor nodes confirmed via cryptographic proof-of-physical-work. Liquidity in Uniswap V3 locked via Uncx. Zero mint authority.",
        risksSummary: "Hardware supply chain bottlenecks could delay Q3 network expansion.",
        bullScenario: "Mass adoption by autonomous vehicle networks driving token burns to $4.50.",
        baseScenario: "Gradual growth toward $2.10 as node count scales to 5000.",
        bearScenario: "Ranging between $0.85 and $1.10 during consolidation.",
      },
      {
        symbol: "QUANTUM-RWA",
        name: "Quantum Real World Compute",
        chain: "Ethereum",
        contractAddress: "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        category: "pre-launch",
        opportunityScore: 92,
        securityScore: 90,
        confidenceScore: 82,
        liquidityScore: 0,
        whaleScore: 88,
        socialScore: 84,
        narrativeScore: 96,
        evidenceScore: 80,
        price: "0.0000",
        priceChange24h: "0.0",
        liquidityUsd: "0",
        marketCapUsd: "0",
        volume24h: "0",
        holdersCount: 0,
        status: "investigating",
        narrative: "RWA + Quantum Compute Credit",
        evidenceSummary: "Testnet contract bytecode audited by CertiK. Deployer address linked to Stanford Distributed Systems Lab alumni. 45,000 Telegram community members awaiting launch date announcement.",
        risksSummary: "Pre-launch status means liquidity risk is unverified until TGE pool deployment.",
        bullScenario: "Successful TGE at $50M FDV following strategic investment round.",
        baseScenario: "Fair launch with $10M initial market cap.",
        bearScenario: "Launch delay due to regulatory compliance check on tokenized compute.",
      },
      {
        symbol: "HYPER-MEME",
        name: "Hyperion Autonomous Cat",
        chain: "Solana",
        contractAddress: "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        category: "newly-launched",
        opportunityScore: 42,
        securityScore: 22,
        confidenceScore: 88,
        liquidityScore: 30,
        whaleScore: 40,
        socialScore: 95,
        narrativeScore: 60,
        evidenceScore: 90,
        price: "0.00012",
        priceChange24h: "-68.5",
        liquidityUsd: "24000",
        marketCapUsd: "120000",
        volume24h: "850000",
        holdersCount: 1200,
        status: "rejected",
        narrative: "Meme",
        evidenceSummary: "Security Red Team trigger: Mint authority present in un-renounced proxy contract, 72% LP held by deployer-linked wallet cluster, trading fee can be dynamically updated to 99%.",
        risksSummary: "CRITICAL SECURITY RISK: High probability of Honeypot / LP rug pull.",
        bullScenario: "None. Reject condition met.",
        baseScenario: "Slow bleed to zero.",
        bearScenario: "Total liquidity drain by deployer within 24h.",
      },
    ]).returning();

    const mainToken = insertedTokens[0];
    const depinToken = insertedTokens[1];
    const rwaToken = insertedTokens[2];
    const scamToken = insertedTokens[3];

    // Insert 10-Team AI Council Opinions for AHOS-AI
    await db.insert(councilOpinions).values([
      {
        tokenId: mainToken.id,
        teamCode: "team_01",
        teamName: "Team 01 - Mathematical Intelligence",
        verdict: "bullish",
        confidence: 92,
        argument: "Bayesian probability of sustained momentum is 87.4%. Volumetric dispersion conforms to institutional accumulation curves.",
        keyEvidence: "Log-normal distribution of transfer sizes, Hurst exponent = 0.74 indicating strong trend persistence.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_02",
        teamName: "Team 02 - Crypto Market Intelligence",
        verdict: "bullish",
        confidence: 89,
        argument: "Liquidity depth to market cap ratio is extremely healthy (21.7%). DEX slippage is below 0.8% for $10k orders.",
        keyEvidence: "Raydium CPMM pool depth $1.85M, 24h volume/MC ratio = 0.49.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_03",
        teamName: "Team 03 - Blockchain & On-Chain Intelligence",
        verdict: "bullish",
        confidence: 94,
        argument: "14 Smart Money wallets previously profitable on $GRASS & $RENDER accumulated $420k without selling a single token.",
        keyEvidence: "Solana RPC wallet cluster graph shows zero outflow to CEX deposit addresses.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_04",
        teamName: "Team 04 - Cybersecurity & Hacker Intelligence",
        verdict: "bullish",
        confidence: 96,
        argument: "Contract bytecode completely verified. Mint Authority: NULL. Freeze Authority: NULL. Liquidity locked 730 days via Streamflow.",
        keyEvidence: "Static analysis score: 98/100. No proxy pattern, no blacklists, buy/sell tax 0/0.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_05",
        teamName: "Team 05 - Investigative Intelligence",
        verdict: "bullish",
        confidence: 88,
        argument: "OSINT confirms deployer key is associated with verified GitHub identity with 8-year commit history in Rust & WebAssembly.",
        keyEvidence: "Twitter dev account created 2018, keypair signed message matching official project domain.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_06",
        teamName: "Team 06 - News & Journalism Intelligence",
        verdict: "bullish",
        confidence: 85,
        argument: "Featured in Cointelegraph & Blockworks organic coverage without paid press release indicators.",
        keyEvidence: "Metadata header analysis confirms editorial submission path.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_07",
        teamName: "Team 07 - Social & Narrative Intelligence",
        verdict: "bullish",
        confidence: 91,
        argument: "AI Agent narrative velocity is at 90th percentile across Twitter X and Telegram channels.",
        keyEvidence: "Bot ratio is under 4.2% (very low bot inflation). Organic engagement multiplier = 3.8x.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_08",
        teamName: "Team 08 - Technology & Software Engineering",
        verdict: "bullish",
        confidence: 93,
        argument: "GitHub repository demonstrates high development velocity: 48 commits in last 7 days, 12 active contributors.",
        keyEvidence: "Automated Rust unit tests passing rate 100%, zero open critical CVE dependencies.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_09",
        teamName: "Team 09 - AI Research & Self-Evolution",
        verdict: "bullish",
        confidence: 90,
        argument: "RAG knowledge base matches high-conviction historical pattern #204 (Early Solana AI Autonomous Core).",
        keyEvidence: "Model consensus score across Claude, GPT-4, and Gemini = 92.4/100.",
      },
      {
        tokenId: mainToken.id,
        teamCode: "team_10",
        teamName: "Team 10 - Strategic Decision & Red-Team Council",
        verdict: "bullish",
        confidence: 87,
        argument: "Contrarian analysis evaluated worst-case scenario: Sol market -20% drop would draw drawdown to $0.028 max. Risk-reward ratio 1:5.2.",
        keyEvidence: "Cross-examination of Teams 1-9 validated no confirmation bias found.",
      },
    ]);

    // Insert Council Opinions for Scam Token (Showing Red Team Rejection)
    await db.insert(councilOpinions).values([
      {
        tokenId: scamToken.id,
        teamCode: "team_04",
        teamName: "Team 04 - Cybersecurity & Hacker Intelligence",
        verdict: "reject",
        confidence: 99,
        argument: "CRITICAL RISK REJECT: Unrenounced proxy bytecode allows instant fee inflation to 99% and freeze authority active.",
        keyEvidence: "Bytecode signature matches Honeypot Exploit Template #412.",
      },
      {
        tokenId: scamToken.id,
        teamCode: "team_10",
        teamName: "Team 10 - Strategic Decision & Red-Team Council",
        verdict: "reject",
        confidence: 100,
        argument: "REJECTED BY RISK GATE. High opportunity score in social team overriden by critical security flaw.",
        keyEvidence: "Rule: High Opportunity + Critical Security Risk = MANDATORY REJECT.",
      },
    ]);

    // Insert Paper Trades
    await db.insert(paperTrades).values([
      {
        tokenId: mainToken.id,
        symbol: "AHOS-AI",
        type: "BUY",
        entryPrice: "0.0180",
        currentPrice: "0.0425",
        stopLoss: "0.0140",
        targetPrice: "0.0900",
        virtualCapital: "500",
        positionSize: "27777",
        pnlUsd: "680.53",
        pnlPercent: "136.1",
        status: "OPEN",
        postMortem: "Paper Trade running +136.1%. Initial entry triggered on Smart Money wallet cluster detection + contract security pass.",
      },
      {
        tokenId: depinToken.id,
        symbol: "NEURAL-DEP",
        type: "BUY",
        entryPrice: "0.8500",
        currentPrice: "1.2800",
        exitPrice: "1.2800",
        stopLoss: "0.7200",
        targetPrice: "1.2500",
        virtualCapital: "300",
        positionSize: "352.9",
        pnlUsd: "151.76",
        pnlPercent: "50.58",
        status: "CLOSED_WIN",
        postMortem: "Target 1 hit at $1.25 (+50.5%). Winning pattern confirmed: Physical proof-of-work on-chain verification yields low false positive rate.",
      },
    ]);

    // Insert Learning Logs (Tree of Wisdom roots & groundwater)
    await db.insert(learningLogs).values([
      {
        eventType: "WIN_PATTERN",
        title: "Smart Money + LP Lock > 365 Days Synergy",
        description: "Tokens where Smart Money accumulation happens within 6 hours of TGE with LP locked > 365 days have an 88.2% win rate over 7-day holding periods.",
        impact: "Weight increased in Team 03 & Team 04 scoring matrix.",
        treeLayer: "ROOTS",
      },
      {
        eventType: "FAILURE_PATTERN",
        title: "High Twitter Engagement Bot Trap Neutralized",
        description: "Detected false positive on $HYPER-MEME where 92% of X mentions originated from coordinated retweeting farms.",
        impact: "Team 07 Social Intelligence added Bot Multiplier Penalty algorithm.",
        treeLayer: "BRANCHES",
      },
      {
        eventType: "SECURITY_EXPLOIT",
        title: "Dynamic Proxy Bytecode Pattern Saved Capital",
        description: "Red-Team Security Gate successfully rejected contract 0x4k3D... before paper trading allocation.",
        impact: "Zero loss on simulated honeypot.",
        treeLayer: "OCEAN",
      },
    ]);

    // Insert Workflows
    await db.insert(githubWorkflows).values([
      {
        name: "AHOS Token Scanner & On-Chain Scraper (Python)",
        type: "python_scanner",
        status: "active",
        executionCount: 1420,
        logSummary: "Scanned 14,280 Solana & Base contracts. 34 flagged for Council evaluation.",
      },
      {
        name: "n8n AI Council Multi-Agent Orchestrator Pipeline",
        type: "n8n_agent",
        status: "active",
        executionCount: 890,
        logSummary: "10-Agent Council debate triggered on 12 tokens. 2 approved, 10 rejected/pending.",
      },
      {
        name: "GitHub OpenSource Knowledge Ingestion Bot",
        type: "github_action",
        status: "active",
        executionCount: 310,
        logSummary: "Parsed 45 crypto research repositories for new smart contract exploit vectors.",
      },
    ]);

    // Insert System Logs
    await db.insert(systemLogs).values([
      {
        level: "OPPORTUNITY_ALERT",
        source: "CouncilEngine",
        message: "High-Conviction Opportunity Discovered: $AHOS-AI Score: 94/100, Security: 88/100, Confidence: 91%.",
        details: "Solana RPC Liquidity depth verified.",
      },
      {
        level: "SECURITY_ALERT",
        source: "SecurityGate",
        message: "REJECTED $HYPER-MEME: Honeypot risk detected in bytecode.",
        details: "Mint authority un-renounced.",
      },
      {
        level: "INFO",
        source: "TelegramBot",
        message: "Daily Intelligence Report dispatched to Master User via Telegram API.",
        details: "2 Paper Trades active, PnL +$832.29 total.",
      },
    ]);

    console.log("AHOS Database successfully seeded!");
  } catch (err) {
    console.error("Error seeding database:", err);
  }
}
