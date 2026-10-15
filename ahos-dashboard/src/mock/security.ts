/** MOCK — security center. Domains below are fictional and use .example TLDs. */
import type { ProviderHealth, SecurityOverview } from "@/lib/api/types";
import { HOUR, L, floorTo, minutesAgo, rng } from "./_seed";

export function mockProviders(now = Date.now()): ProviderHealth[] {
  return [
    { name: "DexScreener", category: L("بازار", "Market"), status: "LIVE", latencyMs: 182, availability: 0.998, lastSuccess: minutesAgo(0.3, now), errorCount: 2 },
    { name: "GeckoTerminal", category: L("بازار", "Market"), status: "DEGRADED", latencyMs: 2240, availability: 0.94, lastSuccess: minutesAgo(1, now), errorCount: 31 },
    { name: "CoinGecko", category: L("بازار", "Market"), status: "LIVE", latencyMs: 410, availability: 0.991, lastSuccess: minutesAgo(0.8, now), errorCount: 6 },
    { name: "Binance public", category: L("بازار", "Market"), status: "LIVE", latencyMs: 96, availability: 0.999, lastSuccess: minutesAgo(0.2, now), errorCount: 0 },
    { name: "GoPlus", category: L("امنیت", "Security"), status: "RATE_LIMITED", latencyMs: null, availability: 0.82, lastSuccess: minutesAgo(6, now), errorCount: 58 },
    { name: "RugCheck", category: L("امنیت", "Security"), status: "LIVE", latencyMs: 640, availability: 0.97, lastSuccess: minutesAgo(1.5, now), errorCount: 9 },
    { name: "DefiLlama", category: L("درون‌زنجیره", "On-chain"), status: "LIVE", latencyMs: 330, availability: 0.995, lastSuccess: minutesAgo(2, now), errorCount: 1 },
    { name: "Pump.fun", category: L("بازار", "Market"), status: "LIVE", latencyMs: 410, availability: 0.96, lastSuccess: minutesAgo(0.6, now), errorCount: 14 },
    { name: "Jupiter", category: L("بازار", "Market"), status: "LIVE", latencyMs: 210, availability: 0.993, lastSuccess: minutesAgo(0.9, now), errorCount: 3 },
    { name: "mempool.space", category: L("درون‌زنجیره", "On-chain"), status: "LIVE", latencyMs: 280, availability: 0.998, lastSuccess: minutesAgo(1, now), errorCount: 0 },
    { name: "Alternative.me", category: L("احساسات", "Sentiment"), status: "LIVE", latencyMs: 350, availability: 0.99, lastSuccess: minutesAgo(30, now), errorCount: 0 },
    { name: "Helius", category: L("درون‌زنجیره", "On-chain"), status: "NO_KEY", latencyMs: null, availability: null, lastSuccess: null, errorCount: 0 },
    { name: "DEXTools", category: L("بازار", "Market"), status: "NO_KEY", latencyMs: null, availability: null, lastSuccess: null, errorCount: 0 },
    { name: "CoinMarketCap", category: L("بازار", "Market"), status: "NO_KEY", latencyMs: null, availability: null, lastSuccess: null, errorCount: 0 },
    { name: "X / Twitter", category: L("اجتماعی", "Social"), status: "SOURCE_UNAVAILABLE", latencyMs: null, availability: null, lastSuccess: null, errorCount: 0 },
    { name: "TON API", category: L("درون‌زنجیره", "On-chain"), status: "NETWORK_UNAVAILABLE", latencyMs: null, availability: 0.41, lastSuccess: minutesAgo(3 * 24 * 60, now), errorCount: 212 },
  ];
}

export function mockSecurity(now = Date.now()): SecurityOverview {
  const r = rng("sec");
  const base = floorTo(now, HOUR);
  return {
    gateCounts: { PASS: 68, REJECT: 136, INCOMPLETE: 39, STALE: 4 },
    scans: [
      { id: "s1", target: "PEPE2", chain: "ethereum", gate: "REJECT", flags: [L("هانی‌پات", "Honeypot"), L("مالیات فروش ۹۹٪", "99% sell tax")], at: minutesAgo(4, now), provider: "GoPlus" },
      { id: "s2", target: "NOVA", chain: "solana", gate: "INCOMPLETE", flags: [L("دارندگان نامعلوم", "Holders unknown")], at: minutesAgo(6, now), provider: "RugCheck" },
      { id: "s3", target: "AEROX", chain: "base", gate: "PASS", flags: [], at: minutesAgo(9, now), provider: "GoPlus" },
      { id: "s4", target: "POPX", chain: "solana", gate: "REJECT", flags: [L("معاملات شبه‌واش", "Wash-like trading"), L("تمرکز ۸۲٪ در ۱۰ کیف پول", "82% in top-10 wallets")], at: minutesAgo(12, now), provider: "RugCheck" },
      { id: "s5", target: "TONX", chain: "ton", gate: "STALE", flags: [L("بررسی منقضی", "Check expired")], at: minutesAgo(3 * 24 * 60, now), provider: "TON API" },
      { id: "s6", target: "JUPX", chain: "solana", gate: "PASS", flags: [], at: minutesAgo(15, now), provider: "RugCheck" },
    ],
    incidents: [
      { id: "i1", title: L("دامنه فیشینگ شبیه رابط Jupiter", "Phishing domain imitating Jupiter UI"), severity: "HIGH", at: minutesAgo(41, now), state: "MITIGATED" },
      { id: "i2", title: L("افزایش خطای GoPlus (محدودیت نرخ)", "GoPlus error spike (rate limit)"), severity: "MEDIUM", at: minutesAgo(64, now), state: "MONITORING" },
      { id: "i3", title: L("تلاش تزریق دستور در متن خبر", "Prompt-injection attempt in news text"), severity: "HIGH", at: minutesAgo(180, now), state: "CLOSED" },
      { id: "i4", title: L("منبع TON بیش از ۷۲ ساعت در دسترس نیست", "TON source unavailable > 72h"), severity: "LOW", at: minutesAgo(3 * 24 * 60, now), state: "OPEN" },
    ],
    phishing: [
      { domain: "jup-airdrop-claim.example", imitates: "jup.ag", detectedAt: minutesAgo(41, now), state: "BLOCKED" },
      { domain: "raydium-swap-v3.example", imitates: "raydium.io", detectedAt: minutesAgo(220, now), state: "BLOCKED" },
      { domain: "uniswap-rewards.example", imitates: "uniswap.org", detectedAt: minutesAgo(600, now), state: "MONITORING" },
    ],
    providers: mockProviders(now).filter((p) => p.category.en === "Security" || p.name === "TON API" || p.name === "DexScreener"),
    flagCounts: [
      { flag: L("هانی‌پات", "Honeypot"), count: 41 },
      { flag: L("مالیات بالا", "High tax"), count: 37 },
      { flag: L("ضرب نامحدود", "Unlimited mint"), count: 22 },
      { flag: L("تمرکز دارندگان", "Holder concentration"), count: 58 },
      { flag: L("نقدینگی قفل‌نشده", "Unlocked LP"), count: 33 },
      { flag: L("تعارض هویت", "Identity conflict"), count: 19 },
    ],
    trend: Array.from({ length: 24 }, (_, i) => ({
      t: base - (23 - i) * HOUR,
      pass: Math.round(2 + r() * 4),
      reject: Math.round(4 + r() * 6),
      incomplete: Math.round(1 + r() * 3),
    })),
  };
}
