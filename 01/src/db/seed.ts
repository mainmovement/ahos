import { sql } from "drizzle-orm";
import { db } from "./index";
import {
  alerts,
  councilOpinions,
  decisions,
  evidence,
  learningPatterns,
  paperTrades,
  providers,
  teamStats,
  tokenScores,
  tokens,
  treeEvents,
} from "./schema";

const H = 3600_000;
const D = 24 * H;
const ago = (ms: number) => new Date(Date.now() - ms);

/** Deterministic pseudo-organic sparkline, 24 points from `a` to `b`. */
function spark(a: number, b: number, vol = 0.04): number[] {
  return Array.from({ length: 24 }, (_, i) => {
    const t = i / 23;
    const base = a + (b - a) * t;
    return +(base * (1 + Math.sin(i * 2.7) * vol + Math.cos(i * 1.3) * vol * 0.6)).toFixed(6);
  });
}

let seeded = false;

/**
 * Idempotent development seeder. Every record carries explicit demo
 * provenance — AHOS never mistakes seeded narrative for live truth.
 */
export async function seedIfEmpty(): Promise<boolean> {
  if (seeded) return true;
  const [{ n }] = await db
    .select({ n: sql<number>`count(*)::int` })
    .from(tokens);
  if (n > 0) {
    seeded = true;
    return true;
  }

  await db.transaction(async (tx) => {
    /* ---------------- TOKENS ---------------- */
    const [nora, simorgh, kavir, mehr, atlas, darya, tiro, aura] = await tx
      .insert(tokens)
      .values([
        {
          slug: "nora",
          chain: "base",
          address: "0x5A96FeC3a97bC1B20d9aC846b4E94E3CbF2E17a1",
          name: "NORA Protocol",
          symbol: "NORA",
          nameFa: "پروتکل نورا",
          identityStatus: "VERIFIED",
          securityGate: "PASS",
          launchAt: ago(21 * D),
          priceUsd: 0.0421,
          change24h: 18.4,
          marketCap: 18_400_000,
          liquidityUsd: 1_900_000,
          volume24h: 4_200_000,
          sparkline: spark(0.021, 0.0421, 0.045),
          summaryFa:
            "پروتکل زیرساخت پرداخت لایه‌دوم روی Base؛ نقدینگی قفل‌شده، رشد ارگانیک حجم و انباشت تدریجی کیف‌پول‌های تازه.",
          summaryEn:
            "L2 payments infrastructure on Base; locked liquidity, organic volume growth and gradual accumulation by fresh wallets.",
          provenance: "DexScreener ↔ Base RPC cross-verified (demo)",
        },
        {
          slug: "simorgh",
          chain: "bsc",
          address: "0xB6d8F29a0C74Ee51A3bD94c8F1a7E20bD35cA0E9",
          name: "Simorgh Finance",
          symbol: "SIMORGH",
          nameFa: "سیمرغ فایننس",
          identityStatus: "VERIFIED",
          securityGate: "REJECT",
          launchAt: ago(3 * D),
          priceUsd: 0.00088,
          change24h: 214.7,
          marketCap: 2_600_000,
          liquidityUsd: 240_000,
          volume24h: 3_800_000,
          sparkline: spark(0.0001, 0.00088, 0.16),
          summaryFa:
            "پامپ ۲۱۴٪ در ۲۴ ساعت — اما شبیه‌سازی فروش شکست می‌خورد. فرصتِ بالا + ریسک امنیتی حدی = رد قطعی.",
          summaryEn:
            "214% pump in 24h — but sell simulation fails. High opportunity + critical security risk = hard reject.",
          provenance: "BscScan ↔ GoPlus simulation (demo)",
        },
        {
          slug: "kavir",
          chain: "solana",
          address: "KavRj9w2XfG3hQm4TzLpYuN5B6cD7eF8gH9iJkLmnoP",
          name: "Kavir",
          symbol: "KAVIR",
          nameFa: "کویر",
          identityStatus: "CONFLICT",
          securityGate: "INCOMPLETE",
          launchAt: ago(12 * D),
          priceUsd: 0.0132,
          change24h: -8.2,
          marketCap: 4_100_000,
          liquidityUsd: 310_000,
          volume24h: 480_000,
          sparkline: spark(0.016, 0.0132, 0.09),
          summaryFa:
            "دو قرارداد متفاوت با یک نماد — تا رفع تعارض هویت، هیچ توصیه، هشدار یا نامزد کاغذی مجاز نیست.",
          summaryEn:
            "Two different contracts share one symbol — until the conflict resolves, no recommendation, alert or paper candidate is allowed.",
          provenance: "Conflicting provider reports (demo)",
        },
        {
          slug: "mehr",
          chain: "ethereum",
          address: "0xE71bA37fC0d52A88b47f99C13eE62a35D0c84f02",
          name: "Mehr Finance",
          symbol: "MEHR",
          nameFa: "مهر فایننس",
          identityStatus: "VERIFIED",
          securityGate: "INCOMPLETE",
          launchAt: ago(40 * D),
          priceUsd: 0.351,
          change24h: 2.1,
          marketCap: 34_000_000,
          liquidityUsd: 4_800_000,
          volume24h: 1_900_000,
          sparkline: spark(0.34, 0.351, 0.03),
          summaryFa:
            "بنیاد قابل‌قبول، اما نتیجهٔ تست مالیات فروش از ارائه‌دهندگان متفاوت است؛ امنیت «ناکامل» است، نه «امن».",
          summaryEn:
            "Decent fundamentals, but sell-tax results differ across providers; security is INCOMPLETE, not safe.",
          provenance: "Multi-provider security screen (demo)",
        },
        {
          slug: "atlas",
          chain: "arbitrum",
          address: "0x2c1B95E5a6F4d8033B7Aa914f0E6C7D82bB53e10",
          name: "Atlas AI",
          symbol: "ATLAS",
          nameFa: "اطلس هوش",
          identityStatus: "VERIFIED",
          securityGate: "PASS",
          launchAt: ago(2 * D),
          priceUsd: 0.0917,
          change24h: 41.3,
          marketCap: 6_300_000,
          liquidityUsd: 520_000,
          volume24h: 2_100_000,
          sparkline: spark(0.052, 0.0917, 0.12),
          summaryFa:
            "دفتر شواهد برای هر نظریهٔ مثبت ناکافی است؛ اختلاف‌نظر شورا بالاست. عبور، خودِ یک تصمیم هوشمندانه است.",
          summaryEn:
            "The evidence ledger is too thin for any bullish thesis; council disagreement is high. SKIP is an intelligent decision.",
          provenance: "Early-stage discovery (demo)",
        },
        {
          slug: "darya",
          chain: "polygon",
          address: "0x4A62eB3f9D1c88A5f7E0c236B9d5F1a4C8b7D02E",
          name: "Darya Chain",
          symbol: "DARYA",
          nameFa: "دریا چین",
          identityStatus: "UNRESOLVED",
          securityGate: "STALE",
          monitoringOnly: true,
          launchAt: ago(6 * D),
          priceUsd: 0.0074,
          change24h: 0.6,
          marketCap: 1_800_000,
          liquidityUsd: 0,
          volume24h: 96_000,
          sparkline: spark(0.0072, 0.0074, 0.02),
          summaryFa:
            "استخر فعال هنوز نهایی نشده است — فقط پایش توکن. هیچ ادعایی دربارهٔ نقدینگیِ استخر مجاز نیست.",
          summaryEn:
            "Active pool unresolved — token monitoring only. No pool-level liquidity claims are permitted.",
          provenance: "Pool discovery pending (demo)",
        },
        {
          slug: "tiro",
          chain: "base",
          address: "0x9D40bE17Ce4aF001d28aC5Bb8E3dA6f2cC715b90",
          name: "Tiro Games",
          symbol: "TIRO",
          nameFa: "تیرو گیمز",
          identityStatus: "VERIFIED",
          securityGate: "PASS",
          launchAt: ago(55 * D),
          priceUsd: 0.0098,
          change24h: -11.6,
          marketCap: 5_500_000,
          liquidityUsd: 680_000,
          volume24h: 730_000,
          sparkline: spark(0.0125, 0.0098, 0.07),
          summaryFa:
            "سیگنال «انباشت نهنگی» فریب بود؛ آزمایش کاغذی با زیان بسته شد و الگوی شکست ثبت گردید.",
          summaryEn:
            "The \u201cwhale accumulation\u201d signal was a spoof; the paper trade closed at a loss and a failure pattern was recorded.",
          provenance: "On-chain flow analysis (demo)",
        },
        {
          slug: "aura",
          chain: "solana",
          address: "AurA7Kx2Pq4Rm9Ty3Wz5NvB8Cd6Ef1GhJkLsMnQwEr",
          name: "Aura Labs",
          symbol: "AURA",
          nameFa: "هاله لبز",
          identityStatus: "VERIFIED",
          securityGate: "PASS",
          launchAt: ago(30 * D),
          priceUsd: 4.47,
          change24h: -3.2,
          marketCap: 44_700_000,
          liquidityUsd: 7_600_000,
          volume24h: 3_100_000,
          sparkline: spark(4.9, 4.47, 0.035),
          summaryFa:
            "زیرساخت اوراکل Solana؛ نامزد با کیفیت اما نه استثنایی — موضع کاغذی باز زیر سطح ورود، بالای حد ضرر.",
          summaryEn:
            "Solana oracle infrastructure; a quality candidate, not exceptional — open paper position below entry, above stop.",
          provenance: "Solana RPC ↔ DexScreener (demo)",
        },
      ])
      .returning();

    const T = {
      nora: nora.id, simorgh: simorgh.id, kavir: kavir.id, mehr: mehr.id,
      atlas: atlas.id, darya: darya.id, tiro: tiro.id, aura: aura.id,
    };

    /* ---------------- SCORES ---------------- */
    await tx.insert(tokenScores).values([
      { tokenId: T.nora, opportunity: 88, security: 86, liquidity: 74, whale: 62, social: 79, narrative: 83, evidence: 81, confidence: 78, computedAt: ago(0.2 * H) },
      { tokenId: T.simorgh, opportunity: 71, security: 8, liquidity: 22, whale: 18, social: 91, narrative: 44, evidence: 76, confidence: 88, computedAt: ago(0.5 * H) },
      { tokenId: T.kavir, opportunity: 54, security: 30, liquidity: 41, whale: 25, social: 33, narrative: 29, evidence: 20, confidence: 12, computedAt: ago(1 * H) },
      { tokenId: T.mehr, opportunity: 58, security: 47, liquidity: 82, whale: 55, social: 31, narrative: 40, evidence: 62, confidence: 44, computedAt: ago(2 * H) },
      { tokenId: T.atlas, opportunity: 66, security: 61, liquidity: 38, whale: 30, social: 72, narrative: 68, evidence: 34, confidence: 29, computedAt: ago(1.4 * H) },
      { tokenId: T.darya, opportunity: 32, security: 24, liquidity: 0, whale: 12, social: 18, narrative: 22, evidence: 16, confidence: 10, computedAt: ago(7 * H) },
      { tokenId: T.tiro, opportunity: 41, security: 70, liquidity: 58, whale: 20, social: 44, narrative: 38, evidence: 66, confidence: 55, computedAt: ago(3 * H) },
      { tokenId: T.aura, opportunity: 72, security: 78, liquidity: 84, whale: 66, social: 52, narrative: 58, evidence: 74, confidence: 66, computedAt: ago(0.8 * H) },
    ]);

    /* ---------------- DECISIONS ---------------- */
    const [noraDecision, simorghDecision, atlasDecision] = await tx
      .insert(decisions)
      .values([
        {
          tokenId: T.nora,
          kind: "STRONG_CANDIDATE",
          confidence: 78,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "PASS", security: "PASS", liquidity: "PASS" },
          whyFa: [
            "هویت توکن و قرارداد با دو منبع مستقل تأیید شد؛ چک‌سام EVM معتبر است.",
            "۸۶٪ نقدینگی استخر اصلی سوزانده شده و شبیه‌سازی خرید/فروش موفق است.",
            "انباشت خالص ۴۱۰ هزار دلار توسط کیف‌پول‌های تازه با تاریخچهٔ تامین مالی متنوع.",
            "رشد حجم با ورودی ارگانیک کاربران همراه است؛ نسبت بات تخمینی زیر ۱۲٪.",
          ],
          whyEn: [
            "Token and contract identity verified via two independent sources; valid EVM checksum.",
            "86% of main-pool liquidity is burned and buy/sell simulation succeeds.",
            "Net accumulation of $410K by fresh wallets with diversified funding history.",
            "Volume growth tracks organic user inflow; estimated bot ratio below 12%.",
          ],
          risksFa: [
            "نقش ممتاز pause هنوز حذف نشده (کنترل ۲-از-۳).",
            "مارکت‌کپ پایین؛ نوسان بالا و عمق خروج محدود.",
            "روایت رسانه‌ای هنوز شکل نگرفته؛ بخشی از شتاب اجتماعی قابل‌تأیید نیست.",
            "بازار کلی در رژیم نوسان بالاست.",
          ],
          risksEn: [
            "Privileged pause role not yet removed (2-of-3 control).",
            "Low market cap; high volatility and limited exit depth.",
            "Media narrative not yet formed; part of social velocity is unverifiable.",
            "Broad market is in a high-volatility regime.",
          ],
          rejectFa: [
            "هر تغییر در مالکیت نقش‌های ممتاز یا فعال‌شدن pause.",
            "واریز بیش از ۵٪ عرضه به صرافی در ۲۴ ساعت آینده.",
            "شکست تازه در شبیه‌سازی فروش یا ظهور مالیات پنهان.",
          ],
          rejectEn: [
            "Any change in privileged roles or pause activation.",
            "More than 5% of supply moved to exchanges within 24h.",
            "Fresh sell-simulation failure or discovery of hidden tax.",
          ],
          scenarios: [
            { key: "bull", prob: 28, fa: "شکست مقاومت تاریخی با تایید حجم؛ رسیدن به محدودهٔ ۰٫۰۷۲ تا ۰٫۰۸۰ دلار.", en: "Break of the all-time resistance on volume; path toward $0.072–0.080." },
            { key: "base", prob: 41, fa: "تثبیت بالای ۰٫۰۳۸ و حرکت پلکانی هم‌راستا با رشد TVL.", en: "Consolidation above $0.038, stair-stepping with TVL growth." },
            { key: "bear", prob: 22, fa: "از دست رفتن ۰٫۰۳۱ و بازگشت به کف قبلی؛ خروج منضبط.", en: "Losing $0.031 and reverting to the prior floor; disciplined exit." },
            { key: "extreme", prob: 9, fa: "سناریوی حدی: سواستفاده از نقش pause یا خروج نقدینگی — خروج اضطراری.", en: "Tail case: privileged-role abuse or liquidity pull — emergency exit." },
          ],
          createdAt: ago(0.6 * H),
        },
        {
          tokenId: T.simorgh,
          kind: "REJECT",
          confidence: 88,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "PASS", security: "REJECT", liquidity: "FAIL" },
          whyFa: [
            "امتیاز فرصت ۷۱ — اما امنیت بالاتر از فرصت است.",
            "شبیه‌سازی فروش در ۷ مسیر DEX شکست خورد؛ احتمال هانی‌پات ۹۴٪.",
            "۹۱٪ عرضه در ۴ کیف‌پول متصل به دیپلویئر.",
            "تاریخچهٔ دیپلویئر شامل تأمین مالی دو توکن راگ‌شده است.",
          ],
          whyEn: [
            "Opportunity score 71 — but security sits above opportunity.",
            "Sell simulation failed on 7 DEX routes; honeypot probability 94%.",
            "91% of supply sits in 4 deployer-linked wallets.",
            "Deployer previously funded two rugged tokens.",
          ],
          risksFa: ["ریسک حدی: از دست رفتن کامل سرمایهٔ فرضی.", "نقدینگی قفل‌نشده و قابل‌برداشت.", "کمپین اجتماعی خریداری‌شده.", "کد بسته، بدون امکان بازبینی کامل."],
          risksEn: ["Tail risk: total loss of hypothetical capital.", "Unlocked, withdrawable liquidity.", "Paid social campaign.", "Closed source, incomplete review."],
          rejectFa: ["الگو از قبل رد شده است؛ هیچ شرط احیایی تعریف نشده."],
          rejectEn: ["Already rejected; no revival condition defined."],
          scenarios: [
            { key: "bull", prob: 4, fa: "حتی در سناریوی مثبت، خروج برای آدرس‌های عادی ناممکن است.", en: "Even the bullish path is unexitable for regular addresses." },
            { key: "base", prob: 18, fa: "پامپ ادامه‌دار برای شکار نقدینگی خروج تازه.", en: "Extended pump hunting fresh exit liquidity." },
            { key: "bear", prob: 40, fa: "تخلیهٔ تدریجی توسط کیف‌پول‌های متصل.", en: "Gradual distribution by linked wallets." },
            { key: "extreme", prob: 38, fa: "راگ‌پال کامل: برداشت LP و صفر شدن قیمت.", en: "Full rug pull: LP removal and price collapse." },
          ],
          createdAt: ago(1.2 * H),
        },
        {
          tokenId: T.atlas,
          kind: "SKIP",
          confidence: 71,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "FAIL", security: "PASS", liquidity: "WARN" },
          whyFa: [
            "هویت و امنیت سالم، اما دفتر شواهد (۳۴/۱۰۰) برای تصمیم مثبت ناکافی است.",
            "اختلاف‌نظر شورا بالاست؛ تیم ۱۰: «هر تصمیم مثبت با این شواهد، قمار است.»",
            "شتاب اجتماعی ناگهانی و بدون پیش‌زمینهٔ تاریخی — ضد فومو فعال شد.",
          ],
          whyEn: [
            "Identity and security are clean, but the evidence ledger (34/100) is too thin for a positive call.",
            "Council disagreement is high; Team 10: “any positive call on this ledger is gambling, not intelligence.”",
            "Sudden social velocity with no history — anti-FOMO engine engaged.",
          ],
          risksFa: ["دادهٔ ۴۸ ساعته برای آمارهٔ معنادار کافی نیست.", "اسپرد نوسانی و عمق نازک.", "تمرکز هولدر بالا."],
          risksEn: ["48h of data is not statistically meaningful.", "Unstable spread and thin depth.", "High holder concentration."],
          rejectFa: ["افشای نقش ممتاز پنهان.", "شکست تست فروش.", "ثبت الگوی تعامل مصنوعی."],
          rejectEn: ["Hidden privileged role disclosure.", "Sell-test failure.", "Detected artificial engagement."],
          scenarios: [
            { key: "bull", prob: 20, fa: "اگر دفتر شواهد کامل شود، می‌تواند نامزد شود؛ فعلاً فقط مشاهده.", en: "Could become a candidate once the ledger fills — observe only." },
            { key: "base", prob: 38, fa: "نوسان بی‌رونق تا شکل‌گیری دادهٔ کافی.", en: "Drifting sideways until meaningful data forms." },
            { key: "bear", prob: 27, fa: "فرسایش شتاب اولیه و بازگشت به کف.", en: "Early velocity fades back to the base." },
            { key: "extreme", prob: 15, fa: "ریسک حدی ناشی از تمرکز عرضه.", en: "Tail risk from supply concentration." },
          ],
          createdAt: ago(1.5 * H),
        },
        {
          tokenId: T.kavir,
          kind: "REJECT",
          confidence: 92,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "FAIL", evidence: "INCOMPLETE", security: "INCOMPLETE", liquidity: "FAIL" },
          whyFa: ["دروازهٔ هویت شکست خورد: دو قرارداد متفاوت با یک نماد.", "تا رفع تعارض: بدون توصیه، بدون هشدار، بدون نامزد کاغذی.", "نام و نماد، نام‌مستعار است نه هویت."],
          whyEn: ["Identity gate failed: two different contracts share one symbol.", "Until resolved: no recommendation, no alert, no paper candidate.", "Names and symbols are aliases, not identity."],
          risksFa: ["خطر انتخاب قرارداد اشتباه.", "احتمال کلاهبرداریِ سوارشده بر نماد."],
          risksEn: ["Wrong-contract selection risk.", "Symbol-squatting scam risk."],
          rejectFa: ["—"],
          rejectEn: ["—"],
          scenarios: [
            { key: "bull", prob: 0, fa: "تعریف‌نشده تا رفع تعارض هویت.", en: "Undefined until identity resolves." },
            { key: "base", prob: 0, fa: "تعریف‌نشده.", en: "Undefined." },
            { key: "bear", prob: 30, fa: "یکی از دو قرارداد به راگ متصل است.", en: "One of the two contracts links to a rug." },
            { key: "extreme", prob: 70, fa: "ریسک حدی: تعامل با قرارداد اشتباه.", en: "Tail risk: interacting with the wrong contract." },
          ],
          createdAt: ago(2.9 * H),
        },
        {
          tokenId: T.mehr,
          kind: "MONITOR",
          confidence: 46,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "PASS", security: "INCOMPLETE", liquidity: "PASS" },
          whyFa: ["نتیجهٔ تست مالیات فروش از دو ارائه‌دهنده متفاوت است.", "امنیت ناشناخته «ناکامل» است، نه «امن».", "بنیاد قابل‌قبول؛ منتظر سندی مستقل سوم."],
          whyEn: ["Sell-tax results differ across two providers.", "Unknown security is INCOMPLETE, not safe.", "Decent fundamentals; awaiting a third independent check."],
          risksFa: ["احتمال مالیات فروش نامشخص.", "دادهٔ ارائه‌دهندهٔ دوم کهنه است."],
          risksEn: ["Possible undisclosed sell tax.", "Second provider data is stale."],
          rejectFa: ["تأیید مالیات پنهان.", "خروج LP بالای ۲۰٪ در هفته."],
          rejectEn: ["Confirmed hidden tax.", "LP outflow above 20% weekly."],
          scenarios: [
            { key: "bull", prob: 24, fa: "با تأیید امنیت می‌تواند نامزد شود.", en: "Becomes a candidate once security verifies." },
            { key: "base", prob: 44, fa: "ادامهٔ پایش بدون موضع.", en: "Continued monitoring, no position." },
            { key: "bear", prob: 22, fa: "کاهش تدریجی در صورت پایداری ابهام.", en: "Gradual bleed while ambiguity persists." },
            { key: "extreme", prob: 10, fa: "ریسک حدی در صورت مالیات پنهان.", en: "Tail risk if hidden tax confirmed." },
          ],
          createdAt: ago(2.1 * H),
        },
        {
          tokenId: T.darya,
          kind: "MONITOR",
          confidence: 18,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "INCOMPLETE", evidence: "INCOMPLETE", security: "INCOMPLETE", liquidity: "FAIL" },
          whyFa: ["استخر فعال هنوز نهایی نشده؛ فقط پایش توکن.", "هیچ ادعای نقدینگیِ استخری مجاز نیست.", "دادهٔ امنیتی کهنه است."],
          whyEn: ["Active pool unresolved; token monitoring only.", "No pool-level liquidity claims permitted.", "Security data is stale."],
          risksFa: ["هویت استخر حل‌نشده.", "دادهٔ کهنه."],
          risksEn: ["Unresolved pool identity.", "Stale data."],
          rejectFa: ["تعارض در هویت استخر."],
          rejectEn: ["Conflicting pool identity."],
          scenarios: [
            { key: "bull", prob: 0, fa: "تعریف‌نشده.", en: "Undefined." },
            { key: "base", prob: 60, fa: "ادامهٔ پایش غیرفعال.", en: "Passive monitoring continues." },
            { key: "bear", prob: 25, fa: "—", en: "—" },
            { key: "extreme", prob: 15, fa: "—", en: "—" },
          ],
          createdAt: ago(6 * H),
        },
        {
          tokenId: T.tiro,
          kind: "SKIP",
          confidence: 64,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "PASS", security: "PASS", liquidity: "PASS" },
          whyFa: ["سیگنال نهنگی فریب شناسایی شد؛ اعتبار جریان هوشمند زیر سوال است.", "پس از کالبدشکافی، امتیاز نهنگی به ۲۰ افت کرد.", "عبور تا بازسازی اعتبار سیگنال‌ها."],
          whyEn: ["Whale signal proven spoofed; smart-flow credibility is impaired.", "Whale score downgraded to 20 after the post-mortem.", "Skipping until signals re-earn trust."],
          risksFa: ["توزیع مجدد عرضه در جریان.", "حجم رو به افول."],
          risksEn: ["Ongoing supply redistribution.", "Fading volume."],
          rejectFa: ["فروش دوبارهٔ کیف‌پول‌های متصل."],
          rejectEn: ["Renewed selling by linked wallets."],
          scenarios: [
            { key: "bull", prob: 14, fa: "نیازمند الگوی انباشت تأییدشدهٔ تازه.", en: "Requires a fresh verified accumulation pattern." },
            { key: "base", prob: 36, fa: "روند خنثی فرسایشی.", en: "Grinding sideways." },
            { key: "bear", prob: 34, fa: "ادامهٔ توزیع به قیمت‌های پایین‌تر.", en: "Further distribution lower." },
            { key: "extreme", prob: 16, fa: "خروج تند کیف‌پول‌های بزرگ.", en: "Accelerated large-holder exit." },
          ],
          createdAt: ago(5 * H),
        },
        {
          tokenId: T.aura,
          kind: "CANDIDATE",
          confidence: 66,
          policyVersion: "v1.4.2",
          gateSnapshot: { identity: "PASS", evidence: "PASS", security: "PASS", liquidity: "PASS" },
          whyFa: ["بنیاد قوی اوراکل Solana با درآمد کارمزد واقعی.", "نقدینگی عمیق و پایدار؛ خروج امن.", "اما شتاب روایی برای عنوان «استثنایی» کافی نیست."],
          whyEn: ["Strong Solana oracle fundamentals with real fee revenue.", "Deep, stable liquidity; safe exit depth.", "But narrative velocity is not enough for an “exceptional” grade."],
          risksFa: ["هم‌بستگی بالا با حرکت SOL.", "رقابت شدید در بخش اوراکل."],
          risksEn: ["High correlation with SOL.", "Intense oracle-sector competition."],
          rejectFa: ["از دست رفتن سهم بازار به‌نفع رقیب جدید.", "شکست حمایت ۴٫۱۰ دلار."],
          rejectEn: ["Market-share loss to a new rival.", "Losing the $4.10 support."],
          scenarios: [
            { key: "bull", prob: 26, fa: "بازگشت به کانال ۵٫۸ تا ۶٫۴ دلار.", en: "Return to the $5.8–6.4 channel." },
            { key: "base", prob: 40, fa: "تثبیت بالای ۴٫۳۰ دلار.", en: "Consolidation above $4.30." },
            { key: "bear", prob: 24, fa: "آزمودن دوبارهٔ ۴٫۱۰.", en: "Re-testing $4.10." },
            { key: "extreme", prob: 10, fa: "ریسک حدی سیستمیک Solana.", en: "Solana systemic tail risk." },
          ],
          createdAt: ago(3.5 * H),
        },
      ])
      .returning();

    /* ---------------- COUNCIL ---------------- */
    type Op = { teamId: string; stance: "BULLISH" | "BEARISH" | "NEUTRAL" | "ABSTAIN" | "ALARM"; confidence: number; fa: string; en: string };
    const noraOps: Op[] = [
      { teamId: "01", stance: "BULLISH", confidence: 81, fa: "توزیع بازده ۲۴ ساعته با امضای پامپ‌وسازش ناسازگار است؛ خودهم‌بستگی حجم، رفتار ارگانیک را تأیید می‌کند.", en: "24h return distribution is inconsistent with pump-and-dump signatures; volume autocorrelation confirms organic behavior." },
      { teamId: "02", stance: "BULLISH", confidence: 84, fa: "ساختار بازار سالم است: مارکت‌کپ پایین، عمق خرید افزایشی در DEX و LP سوزانده‌شده.", en: "Healthy market structure: low cap, rising DEX bid depth, burned LP." },
      { teamId: "03", stance: "BULLISH", confidence: 76, fa: "انباشت تدریجی در سه کیف‌پول نوساز با تأمین مالی متنوع؛ الگوی کلاسیک ورود پول هوشمند.", en: "Gradual accumulation across three fresh wallets with diversified funding — a classic smart-entry pattern." },
      { teamId: "04", stance: "NEUTRAL", confidence: 62, fa: "قرارداد تمیز است، اما نقش pause تحت کنترل ۲-از-۳ باقی است؛ حذف‌نشده بودنِ نقش ممتاز یعنی ریسک زنده.", en: "Contract is clean, but the pause role persists under 2-of-3 control; a live privileged role is live risk." },
      { teamId: "05", stance: "BULLISH", confidence: 70, fa: "تاریخچهٔ دیپلویئر تمیز است؛ هیچ مسیر گرافی به راگ‌های شناخته‌شدهٔ Base دیده نشد.", en: "Deployer history is clean; no graph path to known Base rugs." },
      { teamId: "06", stance: "NEUTRAL", confidence: 55, fa: "پوشش خبری معتبر هنوز شکل نگرفته؛ روایت رسانه‌ای در مرحلهٔ جنین است.", en: "No credible news coverage yet; the media narrative is embryonic." },
      { teamId: "07", stance: "BULLISH", confidence: 74, fa: "شتاب اجتماعی صعودی با ورود طبیعی اعضا؛ نسبت بات تخمینی زیر ۱۲٪.", en: "Rising social velocity with organic member intake; estimated bot ratio below 12%." },
      { teamId: "08", stance: "NEUTRAL", confidence: 60, fa: "زیرساخت پایدار است؛ مخزن عمومی فعال اما کوچک — برای قضاوت قطعی زود است.", en: "Stable infrastructure; public repo active but small — too early for a firm call." },
      { teamId: "09", stance: "ABSTAIN", confidence: 40, fa: "نمونه‌های تاریخی مشابه برای کالیبراسیون مدل کافی نیست؛ از رأی جهت‌دار امتناع می‌کنم.", en: "Too few historical analogues to calibrate; abstaining from any directional vote." },
      { teamId: "10", stance: "BEARISH", confidence: 58, fa: "فرضیهٔ مخالف: انباشت می‌تواند تبانی برای خروج در عمق تازه باشد. حد ضرر را جدی بگیرید.", en: "Counter-thesis: the accumulation could be staged exit into new depth. Respect the stop." },
    ];
    const simorghOps: Op[] = [
      { teamId: "01", stance: "BEARISH", confidence: 88, fa: "توزیع تراکنش‌ها با الگوی پامپ‌اندامپ کلاسیک انطباق ۰٫۹۱ دارد.", en: "Transaction distribution matches classic pump-and-dump at 0.91 correlation." },
      { teamId: "02", stance: "BEARISH", confidence: 82, fa: "نقدینگی قفل‌نشده و در هر لحظه قابل‌برداشت است؛ ریسک خروج مطلق.", en: "Liquidity unlocked and withdrawable at any moment; absolute exit risk." },
      { teamId: "03", stance: "ALARM", confidence: 90, fa: "۹۱٪ عرضه در چهار کیف‌پول متصل به دیپلویئر تمرکز دارد.", en: "91% of supply concentrated in four deployer-linked wallets." },
      { teamId: "04", stance: "ALARM", confidence: 96, fa: "شبیه‌سازی فروش در ۷ مسیر شکست خورد — احتمال هانی‌پات ۹۴٪. فروش برای آدرس عادی ناممکن است.", en: "Sell simulation failed on 7 routes — 94% honeypot probability. Regular addresses cannot sell." },
      { teamId: "05", stance: "ALARM", confidence: 87, fa: "دیپلویئر پیش‌تر دو توکن راگ‌شده را تأمین مالی کرده است؛ الگوی رفتاری تکراری.", en: "Deployer previously funded two rugged tokens; a repeating behavioral pattern." },
      { teamId: "06", stance: "BEARISH", confidence: 60, fa: "موج خبری یکدست و هماهنگ — امضای کمپین خریداری‌شده.", en: "Uniform, synchronized news wave — the signature of a paid campaign." },
      { teamId: "07", stance: "ALARM", confidence: 85, fa: "۷۴٪ تعاملات از حساب‌هایی است که در ۴۸ ساعت گذشته ساخته شده‌اند.", en: "74% of engagement comes from accounts created within the last 48 hours." },
      { teamId: "08", stance: "NEUTRAL", confidence: 50, fa: "کد بسته است؛ بازبینی کامل ممکن نیست اما خروجی بایت‌کد الگوهای مخرب را نشان می‌دهد.", en: "Closed source; full review impossible, but bytecode output shows malicious patterns." },
      { teamId: "09", stance: "ABSTAIN", confidence: 30, fa: "مدل برای این کلاس از الگو کالیبره نیست؛ امتناع.", en: "Model not calibrated for this pattern class; abstaining." },
      { teamId: "10", stance: "BEARISH", confidence: 92, fa: "حتی اگر سود کند، ریسک حدی غیرقابل‌قبول است. رد — بدون مذاکره.", en: "Even if it pays, the tail risk is unacceptable. Reject — non-negotiable." },
    ];
    const atlasOps: Op[] = [
      { teamId: "01", stance: "ABSTAIN", confidence: 45, fa: "۴۸ ساعت داده برای آمارهٔ معنادار کافی نیست.", en: "48 hours of data is statistically insufficient." },
      { teamId: "02", stance: "NEUTRAL", confidence: 58, fa: "حجم واقعی اما نازک؛ اسپرد ناپایدار و عمق متغیر.", en: "Real but thin volume; unstable spread and shifting depth." },
      { teamId: "03", stance: "NEUTRAL", confidence: 52, fa: "هولدرها رشد می‌کنند اما تمرکز بالا باقی است.", en: "Holders growing, but concentration stays high." },
      { teamId: "04", stance: "NEUTRAL", confidence: 55, fa: "نشانهٔ مخربی نیست؛ اما مالکیت renounce نشده — نه امن، نه خطرناکِ اثبات‌شده.", en: "No malicious indicators; ownership not renounced — neither safe nor proven-dangerous." },
      { teamId: "05", stance: "NEUTRAL", confidence: 50, fa: "تیم ناشناس؛ نه مثبتِ قابل‌استناد، نه منفیِ قطعی.", en: "Anonymous team; neither citable-positive nor definitive-negative." },
      { teamId: "06", stance: "BULLISH", confidence: 61, fa: "اشارهٔ رسانه‌ای معتبر به پروتکل مادر می‌تواند آغاز روایت باشد.", en: "A credible media nod to the parent protocol could seed the narrative." },
      { teamId: "07", stance: "BEARISH", confidence: 57, fa: "شتاب اجتماعی ناگهانی و بی‌پیشینه — امضای فومو، نه رشد.", en: "Sudden, ahistorical social velocity — a FOMO signature, not growth." },
      { teamId: "08", stance: "NEUTRAL", confidence: 53, fa: "کد مرتب اما پوشش تست ناکافی.", en: "Tidy code, insufficient test coverage." },
      { teamId: "09", stance: "ABSTAIN", confidence: 35, fa: "دادهٔ آموزشی مشابه بسیار کم؛ امتناع.", en: "Very few comparable training samples; abstaining." },
      { teamId: "10", stance: "BEARISH", confidence: 66, fa: "با این دفتر شواهد، هر رأی مثبت قمار است. عبور — و پرونده را باز نگه دارید.", en: "On this ledger, any bullish vote is gambling. SKIP — and keep the file open." },
    ];

    const opsOf = (ops: Op[], decisionId: string) =>
      ops.map((o) => ({
        decisionId,
        teamId: o.teamId,
        stance: o.stance,
        confidence: o.confidence,
        summaryFa: o.fa,
        summaryEn: o.en,
      }));

    await tx.insert(councilOpinions).values([
      ...opsOf(noraOps, noraDecision.id),
      ...opsOf(simorghOps, simorghDecision.id),
      ...opsOf(atlasOps, atlasDecision.id),
    ]);

    /* ---------------- EVIDENCE ---------------- */
    await tx.insert(evidence).values([
      { tokenId: T.nora, kind: "IDENTITY", source: "DexScreener × Base RPC", sourceUrl: "https://dexscreener.com", status: "VERIFIED", confidence: 97, contentFa: "آدرس قرارداد از دو منبع مستقل یکسان گزارش شد؛ فرمت و چک‌سام EVM معتبر.", contentEn: "Contract address identical across two independent sources; valid EVM format and checksum.", observedAt: ago(0.8 * H) },
      { tokenId: T.nora, kind: "SECURITY", source: "GoPlus Security (demo)", sourceUrl: "https://gopluslabs.io", status: "VERIFIED", confidence: 92, contentFa: "شبیه‌سازی خرید/فروش موفق؛ کارمزد ۱٪/۱٪؛ بدون بلک‌لیست، بدون مینت، بدون مالیات پنهان.", contentEn: "Buy/sell simulation passes; 1%/1% tax; no blacklist, no mint, no hidden tax.", observedAt: ago(0.7 * H) },
      { tokenId: T.nora, kind: "MARKET", source: "GeckoTerminal (demo)", sourceUrl: "https://www.geckoterminal.com", status: "VERIFIED", confidence: 84, contentFa: "نقدینگی استخر اصلی ۱٫۹ میلیون دلار؛ ۸۶٪ LP سوزانده‌شده.", contentEn: "Main pool liquidity $1.9M; 86% of LP burned.", observedAt: ago(1.1 * H) },
      { tokenId: T.nora, kind: "ONCHAIN", source: "تحلیل گراف درون‌زنجیره‌ای (demo)", sourceUrl: null, status: "VERIFIED", confidence: 78, contentFa: "انباشت خالص ۴۱۰ هزار دلار توسط سه کیف‌پول در ۷۲ ساعت گذشته؛ منشأ تأمین مالی متنوع.", contentEn: "Net accumulation of $410K by three wallets over 72h; diversified funding origins.", observedAt: ago(2 * H) },
      { tokenId: T.nora, kind: "SOCIAL", source: "منبع اجتماعی X (نامشخص)", sourceUrl: null, status: "UNVERIFIED", confidence: 46, contentFa: "موج اشارهٔ اینفلوئنسری در X — منبع اولیه در دسترس نیست؛ به‌عنوان شواهد نهایی پذیرفته نشد.", contentEn: "Wave of influencer mentions on X — primary source unavailable; not accepted as final evidence.", observedAt: ago(3 * H) },
      { tokenId: T.simorgh, kind: "SECURITY", source: "شبیه‌ساز فروش GoPlus (demo)", sourceUrl: "https://gopluslabs.io", status: "VERIFIED", confidence: 96, contentFa: "فروش آزمایشی برای آدرس غیرممتاز در هر ۷ مسیر ناموفق؛ پرچم هانی‌پات سطح بحرانی.", contentEn: "Simulated sell for a non-privileged address fails across all 7 routes; critical honeypot flag.", observedAt: ago(1 * H) },
      { tokenId: T.simorgh, kind: "ONCHAIN", source: "تحلیل هولدر (demo)", sourceUrl: null, status: "VERIFIED", confidence: 90, contentFa: "۹۱٪ عرضه در ۴ کیف‌پول متصل به دیپلویئر؛ بدون قفل LP.", contentEn: "91% of supply in 4 deployer-linked wallets; no LP lock.", observedAt: ago(1.3 * H) },
      { tokenId: T.simorgh, kind: "SOCIAL", source: "تحلیل تعامل اجتماعی (demo)", sourceUrl: null, status: "VERIFIED", confidence: 85, contentFa: "۷۴٪ تعاملات از حساب‌های تازه‌ساخته‌شده — تعامل مصنوعی تأیید شد.", contentEn: "74% of engagement from freshly created accounts — artificial engagement confirmed.", observedAt: ago(2.2 * H) },
      { tokenId: T.simorgh, kind: "IDENTITY", source: "BscScan (demo)", sourceUrl: "https://bscscan.com", status: "VERIFIED", confidence: 60, contentFa: "هویت قرارداد معتبر است؛ مشکل، هویت نیست — رفتار قرارداد است.", contentEn: "Contract identity is valid; the issue is not identity — it is contract behavior.", observedAt: ago(2.5 * H) },
      { tokenId: T.kavir, kind: "IDENTITY", source: "گزارش چندمنبعی (demo)", sourceUrl: null, status: "CONFLICTED", confidence: 88, contentFa: "دو قرارداد متفاوت (یکی روی Solana، یک ادعای Base) با نماد KAVIR گزارش شده‌اند؛ تعارض حل‌نشده.", contentEn: "Two different contracts (one Solana, one claimed Base) reported under symbol KAVIR; conflict unresolved.", observedAt: ago(2.8 * H) },
      { tokenId: T.kavir, kind: "IDENTITY", source: "کشف اولیه (demo)", sourceUrl: null, status: "STALE", confidence: 40, contentFa: "دادهٔ اولیهٔ کشف کهنه است؛ بررسی مجدد در صف.", contentEn: "Initial discovery data is stale; re-check queued.", observedAt: ago(9 * H) },
      { tokenId: T.mehr, kind: "SECURITY", source: "اسکنر امنیتی دوم (demo)", sourceUrl: null, status: "UNVERIFIED", confidence: 52, contentFa: "نتیجهٔ تست مالیات فروش با اسکنر اول ناسازگار است؛ نیازمند منبع مستقل سوم.", contentEn: "Sell-tax result conflicts with the first scanner; a third independent source is required.", observedAt: ago(2 * H) },
      { tokenId: T.mehr, kind: "MARKET", source: "CoinGecko (demo)", sourceUrl: "https://www.coingecko.com", status: "STALE", confidence: 50, contentFa: "خوراک قیمت ارائه‌دهندهٔ دوم ۵ ساعت تازگی ندارد.", contentEn: "Second provider price feed is 5h stale.", observedAt: ago(5 * H) },
      { tokenId: T.atlas, kind: "MARKET", source: "DexScreener (demo)", sourceUrl: "https://dexscreener.com", status: "VERIFIED", confidence: 66, contentFa: "حجم ۲۴ ساعتهٔ واقعی اما با عمق خرید نازک و اسپرد نوسانی.", contentEn: "Genuine 24h volume, but thin bid depth and unstable spread.", observedAt: ago(1.2 * H) },
      { tokenId: T.atlas, kind: "SOCIAL", source: "تحلیل اجتماعی (demo)", sourceUrl: null, status: "UNVERIFIED", confidence: 38, contentFa: "شتاب اجتماعی ناگهانی و بدون پیش‌زمینه؛ احتمال هیپ خریداری‌شده بررسی نشده.", contentEn: "Sudden social velocity without history; possible paid hype — unverified.", observedAt: ago(1.6 * H) },
      { tokenId: T.darya, kind: "IDENTITY", source: "کشف استخر (demo)", sourceUrl: null, status: "UNVERIFIED", confidence: 44, contentFa: "استخر فعال هنوز نهایی نشده است؛ صرفاً پایش توکن مجاز است.", contentEn: "Active pool not finalized; token-only monitoring permitted.", observedAt: ago(6 * H) },
      { tokenId: T.tiro, kind: "ONCHAIN", source: "ردیاب جریان وجوه (demo)", sourceUrl: null, status: "VERIFIED", confidence: 80, contentFa: "انتقال ۱۸٪ عرضه به کیف‌پول تازه دو ساعت پیش از ریزش — انباشت نبود، توزیع مجدد بود.", contentEn: "18% of supply moved to a fresh wallet two hours before the drop — redistribution, not accumulation.", observedAt: ago(2 * D) },
      { tokenId: T.tiro, kind: "MARKET", source: "GeckoTerminal (demo)", sourceUrl: "https://www.geckoterminal.com", status: "VERIFIED", confidence: 62, contentFa: "حجم پس از رویداد در روند نزولی پایدار.", contentEn: "Post-event volume in a persistent downtrend.", observedAt: ago(3 * H) },
      { tokenId: T.aura, kind: "MARKET", source: "DexScreener (demo)", sourceUrl: "https://dexscreener.com", status: "VERIFIED", confidence: 78, contentFa: "درآمد کارمزد پروتکل در ۹۰ روز گذشته روند صعودی پایدار دارد.", contentEn: "Protocol fee revenue on a steady 90-day uptrend.", observedAt: ago(0.9 * H) },
      { tokenId: T.aura, kind: "SECURITY", source: "اسکنر امنیتی (demo)", sourceUrl: null, status: "VERIFIED", confidence: 82, contentFa: "بدون نقش ممتاز فعال؛ مالکیت renounce شده.", contentEn: "No active privileged roles; ownership renounced.", observedAt: ago(1.4 * H) },
    ]);

    /* ---------------- PAPER TRADES ---------------- */
    await tx.insert(paperTrades).values([
      { tokenId: T.nora, status: "OPEN", result: null, entry: 0.0331, sizeUsd: 500, stop: 0.028, target1: 0.045, target2: 0.058, target3: 0.072, currentPrice: 0.0421, feesUsd: 1.5, maxHoldHours: 96, openedAt: ago(30 * H) },
      { tokenId: T.aura, status: "OPEN", result: null, entry: 4.62, sizeUsd: 400, stop: 4.1, target1: 5.1, target2: 5.8, target3: 6.4, currentPrice: 4.47, feesUsd: 1.2, maxHoldHours: 120, openedAt: ago(52 * H) },
      { tokenId: T.tiro, status: "CLOSED", result: "LOSS", entry: 0.0118, exitPrice: 0.0098, sizeUsd: 400, stop: 0.0099, target1: 0.0145, target2: 0.017, pnlPct: -16.9, pnlUsd: -67.6, feesUsd: 1.2, maxHoldHours: 72, openedAt: ago(3.2 * D), closedAt: ago(2 * D), postmortemFa: "فرضیهٔ اشتباه: انتقال ۱۸٪ عرضه به کیف‌پول تازه «انباشت» تفسیر شد، حال آنکه مسیر بعدی وجوه به سمت صرافی بود. تأییدیهٔ مسیریابی وجوه درخواست نشده بود. دادهٔ ارائه‌دهنده تازه بود اما تفسیر گروهی هم‌سو (confirmation bias) شد؛ تیم ۱۰ مخالف بود و نادیده گرفته شد.", postmortemEn: "Wrong assumption: an 18% transfer to a fresh wallet was read as accumulation, while funds later flowed to an exchange. No fund-path confirmation was requested. Groupthink (confirmation bias) overrode Team 10's dissent.", lessonFa: "سیگنال نهنگی بدون تحلیل «مسیر وجوه» معتبر نیست؛ امتیاز نهنگی فقط با تأیید مقصد نهایی وجوه اعتبار دارد.", lessonEn: "A whale signal without fund-path analysis is invalid; the whale score only counts after destination flow is verified." },
      { tokenId: T.nora, status: "CLOSED", result: "WIN", entry: 0.0262, exitPrice: 0.0327, sizeUsd: 450, stop: 0.0235, target1: 0.0315, target2: 0.0368, pnlPct: 24.6, pnlUsd: 110.7, feesUsd: 1.4, maxHoldHours: 96, openedAt: ago(9 * D), closedAt: ago(6 * D), postmortemFa: "سیگنال برنده: انباشت آرام ۴۸ ساعت پیش از شتاب حجم. تیم‌های ۰۲ و ۰۳ مسیر درست را دیدند؛ تیم ۰۴ دربارهٔ نقش pause معتبر هشدار داد و در حد ضرر لحاظ شد.", postmortemEn: "Winning signal: quiet accumulation 48h before volume acceleration. Teams 02 and 03 read it right; Team 04's pause-role warning was valid and factored into the stop.", lessonFa: "الگوی «سکوت پیش از موج» در سه نمونهٔ اخیر موفق بوده — به عنوان الگوی مثبت ثبت شد.", lessonEn: "“Silence before the wave” has hit three recent times — recorded as a positive pattern." },
      { tokenId: T.aura, status: "CLOSED", result: "WIN", entry: 4.08, exitPrice: 4.58, sizeUsd: 380, stop: 3.82, target1: 4.5, target2: 4.9, pnlPct: 12.1, pnlUsd: 46.0, feesUsd: 1.1, maxHoldHours: 120, openedAt: ago(8 * D), closedAt: ago(4 * D), postmortemFa: "هم‌گرایی روایت و نقدینگی پایدار، ورود را توجیه کرد؛ خروج پلکانی در هدف اول و دوم انجام شد.", postmortemEn: "Narrative–liquidity alignment justified the entry; laddered exits hit targets one and two." },
      { tokenId: T.mehr, status: "CLOSED", result: "TIMEOUT", entry: 0.359, exitPrice: 0.3504, sizeUsd: 300, stop: 0.331, target1: 0.395, pnlPct: -2.4, pnlUsd: -7.2, feesUsd: 0.9, maxHoldHours: 72, openedAt: ago(12 * D), closedAt: ago(9 * D), postmortemFa: "ابهام مالیات فروش مانع حرکت شد؛ بازار به ابهام رأی داد. پایان‌زمان درست بود — سرمایهٔ فرضی برای فرصت بهتر آزاد شد.", postmortemEn: "Sell-tax ambiguity froze the move; the market voted on the ambiguity. Timing out was correct — virtual capital freed for better setups.", lessonFa: "وقتی شواهد امنیتی ناکامل است، «عدم ورود زودهنگام» به خودی خود نتیجهٔ بهتری از میانگین بازار می‌سازد.", lessonEn: "When security evidence is incomplete, “not entering early” itself outperforms the market average." },
    ]);

    /* ---------------- ALERTS ---------------- */
    await tx.insert(alerts).values([
      { type: "OPPORTUNITY", severity: "HIGH", tokenSlug: "nora", titleFa: "میوهٔ طلایی: NORA با اطمینان ۷۸", titleEn: "Golden fruit: NORA at confidence 78", bodyFa: "هر چهار دروازهٔ کانونیکال گذرانده شد؛ اما ریسک‌های نقش pause در پرونده ثبت است.", bodyEn: "All four canonical gates passed; pause-role risk recorded in the dossier.", createdAt: ago(38 * 60000) },
      { type: "SECURITY", severity: "CRITICAL", tokenSlug: "simorgh", titleFa: "رد امنیتی: SIMORGH — احتمال هانی‌پات ۹۴٪", titleEn: "Security reject: SIMORGH — 94% honeypot probability", bodyFa: "شبیه‌سازی فروش در ۷ مسیر شکست خورد. امتیاز فرصت بالا هیچ‌وقت بالاتر از امنیت نیست.", bodyEn: "Sell simulation failed on 7 routes. A high opportunity score never outranks security.", createdAt: ago(1.2 * H) },
      { type: "WHALE", severity: "MEDIUM", tokenSlug: "nora", titleFa: "انباشت ۴۱۰ هزار دلاری در NORA", titleEn: "$410K accumulation in NORA", bodyFa: "سه کیف‌پول تازه با تأمین مالی متنوع؛ مسیر وجوه پایش می‌شود.", bodyEn: "Three fresh wallets, diversified funding; flow path under watch.", createdAt: ago(2 * H) },
      { type: "IDENTITY", severity: "HIGH", tokenSlug: "kavir", titleFa: "سرکوب خروجی: تعارض هویت KAVIR", titleEn: "Output suppressed: KAVIR identity conflict", bodyFa: "دو قرارداد با یک نماد — هیچ توصیه، هشدار یا نامزد کاغذی صادر نشد.", bodyEn: "Two contracts, one symbol — no recommendation, alert or paper candidate issued.", createdAt: ago(3 * H) },
      { type: "DAILY", severity: "INFO", tokenSlug: null, titleFa: "گزارش روزانهٔ هوش منتشر شد", titleEn: "Daily intelligence report published", bodyFa: "۸ توکن تحت پایش، ۲ موضع کاغذی باز، ۱ الگوی شکست تازه.", bodyEn: "8 tokens monitored, 2 open paper positions, 1 new failure pattern.", createdAt: ago(5 * H) },
      { type: "PAPER", severity: "MEDIUM", tokenSlug: "tiro", titleFa: "پایان آزمایش TIRO (−۱۶٫۹٪) — کالبدشکافی آماده است", titleEn: "TIRO experiment closed (−16.9%) — post-mortem ready", bodyFa: "الگوی شکست «فریب انباشت نهنگی» ثبت شد؛ امتیاز نهنگی بازتنظیم گردید.", bodyEn: "Failure pattern “whale-accumulation spoof” recorded; whale scoring recalibrated.", createdAt: ago(2 * D) },
    ]);

    /* ---------------- PROVIDERS ---------------- */
    await tx.insert(providers).values([
      { name: "DexScreener", kind: "MarketData", status: "OK", latencyMs: 182, reliability: 0.984, lastSuccessAt: ago(45 * 1000) },
      { name: "GeckoTerminal", kind: "MarketData", status: "OK", latencyMs: 240, reliability: 0.972, lastSuccessAt: ago(2 * 60000) },
      { name: "GoPlus Security", kind: "Security", status: "OK", latencyMs: 310, reliability: 0.991, lastSuccessAt: ago(4 * 60000) },
      { name: "CoinGecko", kind: "MarketData", status: "STALE", latencyMs: 0, reliability: 0.861, lastSuccessAt: ago(5 * H), failureFa: "سهمیهٔ رایگان اشباع شده؛ آخرین پاسخ موفق ۵ ساعت پیش.", failureEn: "Free quota saturated; last success 5 hours ago." },
      { name: "Base RPC", kind: "Blockchain", status: "OK", latencyMs: 96, reliability: 0.995, lastSuccessAt: ago(20 * 1000) },
      { name: "Solana RPC", kind: "Blockchain", status: "OK", latencyMs: 141, reliability: 0.989, lastSuccessAt: ago(35 * 1000) },
      { name: "X Social Source", kind: "Social", status: "BLOCKED", latencyMs: 0, reliability: 0.42, lastSuccessAt: ago(26 * H), failureFa: "دسترسی از موقعیت جاری مسدود است؛ مسیر جایگزین در حال ارزیابی.", failureEn: "Access blocked from the current location; fallback path under evaluation." },
      { name: "Telegram Gateway", kind: "Delivery", status: "OK", latencyMs: 210, reliability: 0.981, lastSuccessAt: ago(12 * 60000) },
      { name: "Open-Meteo", kind: "Environment", status: "OK", latencyMs: 260, reliability: 0.993, lastSuccessAt: ago(9 * 60000) },
    ]);

    /* ---------------- LEARNING PATTERNS ---------------- */
    await tx.insert(learningPatterns).values([
      { kind: "POSITIVE", titleFa: "سکوت پیش از موج", titleEn: "Silence before the wave", descFa: "انباشت آرام در استخرهای کم‌عمق، ۴۸ تا ۷۲ ساعت پیش از شتاب حجم، در نمونه‌های اخیر مقدمهٔ افزایش پایدار بوده است.", descEn: "Quiet accumulation in shallow pools, 48–72h before volume acceleration, has preceded sustained upside in recent samples.", metricFa: "۳ مورد موفق از ۴ مشاهده", metricEn: "3 of 4 observations hit", createdAt: ago(6 * D) },
      { kind: "POSITIVE", titleFa: "هم‌گرایی روایت و نقدینگی", titleEn: "Narrative–liquidity alignment", descFa: "وقتی رشد روایت با رشد واقعی TVL همراستا است، دقت رتبه‌بندی به‌طور معناداری بالاتر می‌رود.", descEn: "When narrative growth aligns with real TVL growth, ranking accuracy improves materially.", metricFa: "۲ مورد موفق از ۲ مشاهده", metricEn: "2 of 2 observations hit", createdAt: ago(4 * D) },
      { kind: "FAILURE", titleFa: "فریب انباشت نهنگی", titleEn: "Whale-accumulation spoof", descFa: "انتقال بزرگ به کیف‌پول تازه «انباشت» نبود؛ توزیع مجدد به‌سمت صرافی بود. سیگنال نهنگی بدون ردیابی مسیر وجوه فریب می‌خورد.", descEn: "A large transfer to a fresh wallet was not accumulation — it was redistribution toward an exchange. Whale signals without fund-path tracking get spoofed.", metricFa: "ناشی از شکست TIRO", metricEn: "Derived from the TIRO loss", createdAt: ago(2 * D) },
      { kind: "FAILURE", titleFa: "شتاب اجتماعی خریداری‌شده", titleEn: "Purchased social velocity", descFa: "رشد انفجاری تعامل از حساب‌های تازه‌ساخته‌شده همیشه با فروپاشی قیمت همراه بوده است؛ فیلتر نسبت‌بات اجباری شد.", descEn: "Explosive engagement from freshly created accounts has always preceded price collapse; the bot-ratio filter is now mandatory.", metricFa: "ناشی از رد SIMORGH", metricEn: "Derived from the SIMORGH reject", createdAt: ago(1.2 * H) },
    ]);

    /* ---------------- WISE TREE EVENTS ---------------- */
    await tx.insert(treeEvents).values([
      { kind: "GOLDEN_FRUIT", titleFa: "یک میوهٔ طلایی رسید", titleEn: "A golden fruit has ripened", detailFa: "NORA با اطمینان کانونیکال ۷۸ و عبور از هر چهار دروازه، به میوهٔ طلایی بدل شد.", detailEn: "NORA became a golden fruit at canonical confidence 78 with all four gates passed.", weight: 5, createdAt: ago(38 * 60000) },
      { kind: "WATER", titleFa: "آب تازه به ریشه رسید", titleEn: "Fresh water reached the roots", detailFa: "۱۴ سند شواهد در چرخهٔ اخیر تأیید و به دانش تبدیل شد.", detailEn: "14 evidence records verified and converted into knowledge in the latest cycle.", weight: 3, createdAt: ago(2 * H) },
      { kind: "FRUIT", titleFa: "میوه‌ای تازه در پایش", titleEn: "A new fruit under watch", detailFa: "AURA به‌عنوان نامزد با کیفیت وارد شاخهٔ فرصت‌ها شد.", detailEn: "AURA entered the opportunity branch as a quality candidate.", weight: 2, createdAt: ago(6 * H) },
      { kind: "ROCK", titleFa: "سنگی در مسیر ریشهٔ اجتماعی", titleEn: "A rock blocks the social root", detailFa: "دسترسی به منبع X مسدود شد؛ ریشهٔ اجتماعی تحت‌فشار اما جایگزین در راه است.", detailEn: "Access to the X source is blocked; the social root is stressed but a fallback is coming.", weight: 4, createdAt: ago(26 * H) },
      { kind: "LESSON", titleFa: "برگی پوسید و خاک سمومتر شد", titleEn: "A leaf composted into richer soil", detailFa: "شکست TIRO به الگوی «فریب انباشت نهنگی» تبدیل شد؛ درخت از خطا تغذیه می‌کند.", detailEn: "The TIRO loss became the “whale-spoof” failure pattern; the tree feeds on mistakes.", weight: 3, createdAt: ago(2 * D) },
      { kind: "ROOT", titleFa: "ریشهٔ GeckoTerminal عمیق‌تر شد", titleEn: "The GeckoTerminal root grew deeper", detailFa: "سه روز پایداری پیوسته؛ اطمینان منبع چهار درصد افزایش یافت.", detailEn: "Three days of continuous stability; source confidence up four percent.", weight: 2, createdAt: ago(1 * D) },
      { kind: "BRANCH", titleFa: "شاخهٔ تیم قرمز تقویت شد", titleEn: "The red-team branch strengthened", detailFa: "دقت تشخیص امنیتی پس از SIMORGH به ۸۳٪ رسید.", detailEn: "Security detection accuracy reached 83% after SIMORGH.", weight: 2, createdAt: ago(3 * D) },
      { kind: "NEW_SOURCE", titleFa: "منشأ تازه‌ای کوچید", titleEn: "A new spring joined", detailFa: "RPC مستقیم Solana به شبکهٔ ریشه‌ها افزوده شد؛ استقلال از واسطه‌ها بیشتر شد.", detailEn: "Direct Solana RPC joined the root network; fewer intermediaries now.", weight: 3, createdAt: ago(4 * D) },
    ]);

    /* ---------------- COUNCIL TEAMS ---------------- */
    await tx.insert(teamStats).values([
      { teamId: "01", nameFa: "ریاضی‌گو", nameEn: "MathMind", personaFa: "استاد احتمال", personaEn: "Master of probability", specialtyFa: "ریاضیات، آمار، بیزی، سری‌های زمانی، تشخیص ناهنجاری", specialtyEn: "Mathematics, statistics, Bayesian reasoning, time series, anomaly detection", icon: "Sigma", color: "#7dd3fc", calls: 214, correct: 149, abstains: 41, calibration: 0.78 },
      { teamId: "02", nameFa: "نگهبان بازار", nameEn: "MarketPulse", personaFa: "خوانندهٔ ساختار", personaEn: "Structure reader", specialtyFa: "بازار، توکنومیکس، نقدینگی، اکشن قیمت و رژیم بازار", specialtyEn: "Markets, tokenomics, liquidity, price action, market regime", icon: "ChartCandlestick", color: "#34d399", calls: 326, correct: 201, abstains: 37, calibration: 0.72 },
      { teamId: "03", nameFa: "دیده‌بان زنجیره", nameEn: "ChainEye", personaFa: "کاوشگر گراف", personaEn: "Graph explorer", specialtyFa: "کیف‌پول‌ها، نهنگ‌ها، پول هوشمند و گراف تراکنش‌ها", specialtyEn: "Wallets, whales, smart money and transaction graphs", icon: "Blocks", color: "#a78bfa", calls: 288, correct: 176, abstains: 44, calibration: 0.7 },
      { teamId: "04", nameFa: "تیم قرمز", nameEn: "RedFlag", personaFa: "خصم ذاتی", personaEn: "The adversary", specialtyFa: "امنیت، هانی‌پات، قراردادهای مخرب و سطح حمله", specialtyEn: "Security, honeypots, malicious contracts, attack surface", icon: "ShieldAlert", color: "#fb7185", calls: 197, correct: 163, abstains: 12, calibration: 0.83 },
      { teamId: "05", nameFa: "کارآگاه", nameEn: "Sleuth", personaFa: "ردیاب هویت", personaEn: "Identity tracer", specialtyFa: "OSINT، روابط موجودیت‌ها و راستی‌آزمایی متقابل", specialtyEn: "OSINT, entity relationships and cross-verification", icon: "Fingerprint", color: "#f59e0b", calls: 154, correct: 98, abstains: 30, calibration: 0.68 },
      { teamId: "06", nameFa: "روزنامه‌نگار", nameEn: "PressCheck", personaFa: "سردبیر شکاک", personaEn: "Skeptical editor", specialtyFa: "خبر، راستی‌آزمایی و کیفیت منابع رسانه‌ای", specialtyEn: "News, verification and media source quality", icon: "Newspaper", color: "#60a5fa", calls: 176, correct: 104, abstains: 52, calibration: 0.64 },
      { teamId: "07", nameFa: "نبض اجتماعی", nameEn: "CrowdSense", personaFa: "شنوندهٔ جمعیت", personaEn: "Crowd listener", specialtyFa: "شبکه‌های اجتماعی، شتاب روایت و تشخیص تعامل مصنوعی", specialtyEn: "Social networks, narrative velocity, artificial engagement", icon: "Radio", color: "#f472b6", calls: 243, correct: 131, abstains: 47, calibration: 0.61 },
      { teamId: "08", nameFa: "مهندس", nameEn: "ForgeMind", personaFa: "معمار خاموش", personaEn: "Silent architect", specialtyFa: "زیرساخت، API، پایگاه‌داده و قابلیت اطمینان", specialtyEn: "Infrastructure, APIs, databases, reliability", icon: "Cpu", color: "#22d3ee", calls: 98, correct: 74, abstains: 15, calibration: 0.76 },
      { teamId: "09", nameFa: "پژوهشگر مدل", nameEn: "ModelScout", personaFa: "شکارچی مدل", personaEn: "Model hunter", specialtyFa: "مدل‌های هوشی، استدلال، عامل‌ها و خودتکاملی", specialtyEn: "AI models, reasoning, agents, self-evolution", icon: "Brain", color: "#c084fc", calls: 87, correct: 61, abstains: 18, calibration: 0.71 },
      { teamId: "10", nameFa: "رقیب‌خوار", nameEn: "DevilAdvocate", personaFa: "صدا علیه همه", personaEn: "The voice against all", specialtyFa: "رد تیم — چالش فرضیه‌ها، سوگیری تأیید و بدترین حالت", specialtyEn: "Red teaming — challenging theses, confirmation bias, worst cases", icon: "Swords", color: "#f97316", calls: 205, correct: 118, abstains: 26, calibration: 0.66 },
    ]);
  });

  seeded = true;
  return true;
}
