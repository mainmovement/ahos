/** MOCK — governance, memory, reports, workshop, digital world, earth. */
import type {
  DigitalWorldOverview,
  EarthOverview,
  GovernanceOverview,
  MemoryOverview,
  ReportItem,
  WorkshopOverview,
} from "@/lib/api/types";
import { DAY, HOUR, L, minutesAgo, series } from "./_seed";

export function mockGovernance(now = Date.now()): GovernanceOverview {
  return {
    policyVersion: "policy-2b.3",
    constitution: [
      { id: "C1", title: L("UNKNOWN بر جعل مقدم است", "UNKNOWN over fabricated"), summary: L("هیچ قیمت، خبر یا اطمینانی ساخته نمی‌شود؛ نبود داده صریحاً نمایش داده می‌شود.", "No price, news or confidence is invented; missing data is shown explicitly.") },
      { id: "C2", title: L("فقط کاغذی", "Paper only"), summary: L("معامله واقعی، کیف پول و وجوه واقعی غیرفعال است.", "Real trading, wallets and real funds are disabled.") },
      { id: "C3", title: L("مرجع واحد تصمیم", "Single decision authority"), summary: L("فقط مرجع کانونی پایتون تصمیم می‌گیرد؛ هوش مصنوعی فقط می‌تواند کاهش دهد یا امتناع کند.", "Only the Python canonical authority decides; AI may downgrade or abstain, never upgrade.") },
      { id: "C4", title: L("حفظ اختلاف‌نظر", "Preserve disagreement"), summary: L("نظر اقلیت شورا میانگین‌گیری کور نمی‌شود.", "Council minority views are not blindly averaged.") },
      { id: "C5", title: L("Lane A منجمد", "Lane A frozen"), summary: L("کد کشف و معامله کاغذی بدون درخواست حاکمیتی بازبینی‌شده تغییر نمی‌کند.", "Discovery and paper code never change without a reviewed governance request.") },
    ],
    approvals: [
      { id: "AP-22", title: L("افزودن منبع خبری فارسی جدید", "Add new Persian news source"), requestedBy: "agent.news-pipeline", state: "PENDING", at: minutesAgo(70, now), scope: "providers" },
      { id: "AP-21", title: L("افزایش سقف موقعیت هم‌زمان به ۸", "Raise concurrent positions to 8"), requestedBy: "agent.paper-trader", state: "REJECTED", at: minutesAgo(60 * 20, now), scope: "risk" },
      { id: "AP-20", title: L("ارتقای آستانه ضدهیاهو", "Tighten anti-hype threshold"), requestedBy: "agent.discovery-scout", state: "ACCEPTED", at: minutesAgo(60 * 30, now), scope: "scoring" },
      { id: "AP-19", title: L("اتصال n8n به هشدارها", "Wire n8n to alerts"), requestedBy: "human", state: "DEFERRED", at: minutesAgo(60 * 54, now), scope: "automation" },
    ],
    audit: [
      { id: "au1", at: minutesAgo(3, now), actor: "python.canonical", action: L("ثبت تصمیم REJECT برای PEPE2", "Recorded REJECT for PEPE2"), target: "ethereum:0x6f3a…9f01", hash: "9f3c1a…e21b" },
      { id: "au2", at: minutesAgo(42, now), actor: "agent.paper-trader", action: L("بستن موقعیت کاغذی SOL", "Closed paper SOL position"), target: "paper:pp-sol-40", hash: "41be09…77ac" },
      { id: "au3", at: minutesAgo(70, now), actor: "agent.news-pipeline", action: L("ثبت درخواست تأیید AP-22", "Filed approval request AP-22"), target: "governance:AP-22", hash: "c08d4e…1f90" },
      { id: "au4", at: minutesAgo(60 * 20, now), actor: "human.operator", action: L("رد درخواست AP-21", "Rejected AP-21"), target: "governance:AP-21", hash: "77a2f1…b3c4" },
      { id: "au5", at: minutesAgo(60 * 30, now), actor: "human.operator", action: L("پذیرش درخواست AP-20", "Accepted AP-20"), target: "governance:AP-20", hash: "e5d1aa…0c2e" },
    ],
    boundaries: [
      { surface: L("رابط TypeScript", "TypeScript UI"), may: L("نمایش و رتبه‌بندی؛ REJECT/ABSTAIN ایمن", "Present & rank; fail-closed REJECT/ABSTAIN"), mustNot: L("صدور WATCH/PAPER_CANDIDATE بدون مرجع پایتون", "Emit WATCH/PAPER_CANDIDATE without Python") },
      { surface: L("هوش مصنوعی", "AI"), may: L("کاهش سطح یا امتناع", "Downgrade or abstain"), mustNot: L("ارتقای تصمیم", "Upgrade a decision") },
      { surface: L("تلگرام", "Telegram"), may: L("ارسال هشدار مجاز", "Send permitted alerts"), mustNot: L("هشدار بدون PASS و alerts_allowed", "Alert without PASS and alerts_allowed") },
      { surface: L("معامله کاغذی", "Paper trading"), may: L("باز کردن با paper_allowed و PASS", "Open with paper_allowed and PASS"), mustNot: L("هرگونه معامله واقعی", "Any real trade") },
    ],
  };
}

export function mockMemory(now = Date.now()): MemoryOverview {
  return {
    items: [
      { id: "mm1", title: L("تبلیغ پولی + نقدینگی کم ⇒ احتمال بالای ریزش", "Paid promo + thin liquidity ⇒ high dump likelihood"), kind: "pattern", state: "PROMOTED", confidence: "HIGH", source: "M-041 / H-09", at: minutesAgo(60 * 12, now) },
      { id: "mm2", title: L("Reddit بدون تأیید زنجیره‌ای قابل اتکا نیست", "Reddit without on-chain confirmation is unreliable"), kind: "source-trust", state: "PROMOTED", confidence: "MED", source: "M-037 / H-07", at: minutesAgo(60 * 30, now) },
      { id: "mm3", title: L("اطمینان ۰٫۸+ بیش‌برآورد شده است", "Confidence ≥ 0.8 is over-estimated"), kind: "calibration", state: "CANDIDATE", confidence: "MED", source: "University / e1", at: minutesAgo(35, now) },
      { id: "mm4", title: L("اختلاف پل‌ها در ۹۰ ثانیه بسته می‌شود", "Bridge gaps close within 90s"), kind: "pattern", state: "CANDIDATE", confidence: "LOW", source: "M-042 / H-14", at: minutesAgo(48, now) },
      { id: "mm5", title: L("حباب سکه پیش‌بینی‌کننده تقاضاست", "Coin premium predicts demand"), kind: "lesson", state: "REVOKED", confidence: "LOW", source: "M-035", at: minutesAgo(60 * 50, now) },
      { id: "mm6", title: L("GoPlus در ساعات اوج محدودیت نرخ دارد", "GoPlus rate-limits at peak hours"), kind: "source-trust", state: "EXPIRED", confidence: "MED", source: "System / providers", at: minutesAgo(60 * 24 * 9, now) },
    ],
    learning: [
      { id: "precision", label: L("دقت فیلتر", "Filter precision"), points: series("mem:prec", 30, 0.84, DAY, 0.012, 0.002, now, 3) },
      { id: "calibration", label: L("خطای کالیبراسیون", "Calibration error"), points: series("mem:cal", 30, 0.071, DAY, 0.03, -0.004, now, 3) },
    ],
    counts: { candidates: 14, promoted: 37, revoked: 6, expired: 11 },
  };
}

export function mockReports(now = Date.now()): ReportItem[] {
  return [
    { id: "r1", title: L("گزارش روزانه بازار — صبح", "Daily market brief — morning"), kind: "daily", state: "READY", generatedAt: minutesAgo(180, now), pages: 6, author: "agent.research-analyst", summary: L("انرژی و طلا مثبت، رمزارز با حجم بالا؛ ۳ هشدار امنیتی.", "Energy and gold up, crypto on heavy volume; 3 security alerts.") },
    { id: "r2", title: L("گزارش هفتگی شواهد", "Weekly evidence report"), kind: "weekly", state: "GENERATING", generatedAt: null, pages: null, author: "agent.research-analyst", summary: L("در حال تولید…", "Generating…") },
    { id: "r3", title: L("ممیزی مرز اختیارات", "Authority-boundary audit"), kind: "audit", state: "READY", generatedAt: minutesAgo(60 * 26, now), pages: 11, author: "human.operator", summary: L("هیچ صدور WATCH بدون مرجع پایتون ثبت نشد.", "No WATCH emitted without Python authority.") },
    { id: "r4", title: L("گزارش حادثه — تلگرام", "Incident report — Telegram"), kind: "incident", state: "FAILED", generatedAt: null, pages: null, author: "agent.org.14-agent-runtime-engineering", summary: L("داده ورودی ناقص است.", "Input data incomplete.") },
    { id: "r5", title: L("پژوهش: الگوی میم‌کوین‌ها", "Research: memecoin patterns"), kind: "research", state: "SCHEDULED", generatedAt: null, pages: null, author: "agent.research-analyst", summary: L("زمان‌بندی‌شده برای پایان مأموریت M-041.", "Scheduled for end of mission M-041.") },
  ];
}

export function mockWorkshop(now = Date.now()): WorkshopOverview {
  return {
    builds: [
      { id: "b1", target: "ahos-dashboard", state: "PASS", durationSec: 74, at: minutesAgo(25, now), commit: "ee325ea" },
      { id: "b2", target: "web (root Next.js)", state: "PASS", durationSec: 61, at: minutesAgo(60 * 3, now), commit: "ee325ea" },
      { id: "b3", target: "python lane-b", state: "RUNNING", durationSec: null, at: minutesAgo(1, now), commit: "ee325ea" },
      { id: "b4", target: "windows gate G1–G10", state: "QUEUED", durationSec: null, at: minutesAgo(0.5, now), commit: "ee325ea" },
    ],
    tests: [
      { suite: "tests/ (slice 1)", passed: 214, failed: 0, skipped: 3, durationSec: 41 },
      { suite: "tests2b/ (epistemic core)", passed: 168, failed: 0, skipped: 0, durationSec: 33 },
      { suite: "web-api-auth selftest", passed: 18, failed: 0, skipped: 0, durationSec: 2 },
      { suite: "canonical-read-model selftest", passed: 26, failed: 1, skipped: 0, durationSec: 3 },
      { suite: "lane A integrity", passed: 1, failed: 0, skipped: 0, durationSec: 1 },
    ],
    stack: [
      { name: "Next.js", version: "16.2.6", license: "MIT", role: L("چارچوب وب", "Web framework") },
      { name: "React", version: "19.2.6", license: "MIT", role: L("رابط کاربری", "UI library") },
      { name: "Tailwind CSS", version: "4.1.17", license: "MIT", role: L("سیستم طراحی", "Styling") },
      { name: "ECharts", version: "6.1.0", license: "Apache-2.0", role: L("نمودارها", "Charts") },
      { name: "three.js", version: "0.186.1", license: "MIT", role: L("گرافیک سه‌بعدی", "3D graphics") },
      { name: "three-globe", version: "2.45.6", license: "MIT", role: L("کره زمین", "Globe layers") },
      { name: "Python", version: "3.11", license: "PSF", role: L("مرجع کانونی", "Canonical authority") },
    ],
    issues: [
      { id: "G-12", title: L("گیت‌های ویندوز G1–G10 هنوز شواهد واقعی ندارند", "Windows gates G1–G10 lack real artifacts"), severity: "HIGH", state: "BLOCKED" },
      { id: "G-17", title: L("یکپارچه‌سازی داشبورد جدید با API موجود", "Wire new dashboard to existing API"), severity: "MEDIUM", state: "OPEN" },
      { id: "G-21", title: L("تست سرتاسری تلگرام", "Telegram end-to-end test"), severity: "MEDIUM", state: "BLOCKED" },
      { id: "G-08", title: L("پوشش تست کالیبراسیون", "Calibration test coverage"), severity: "LOW", state: "IN_PROGRESS" },
    ],
  };
}

export function mockDigitalWorld(now = Date.now()): DigitalWorldOverview {
  const nodes: DigitalWorldOverview["graph"]["nodes"] = [
    { id: "btc", name: "Bitcoin", category: "chain", value: 100 },
    { id: "eth", name: "Ethereum", category: "chain", value: 92 },
    { id: "sol", name: "Solana", category: "chain", value: 70 },
    { id: "bnb", name: "BNB Chain", category: "chain", value: 58 },
    { id: "base", name: "Base", category: "chain", value: 52 },
    { id: "arb", name: "Arbitrum", category: "chain", value: 46 },
    { id: "ton", name: "TON", category: "chain", value: 34 },
    { id: "tron", name: "Tron", category: "chain", value: 44 },
    { id: "usdt", name: "USDT", category: "stablecoin", value: 60 },
    { id: "usdc", name: "USDC", category: "stablecoin", value: 50 },
    { id: "uni", name: "Uniswap", category: "protocol", value: 38 },
    { id: "aave", name: "Aave", category: "protocol", value: 36 },
    { id: "jup", name: "Jupiter", category: "protocol", value: 30 },
    { id: "ray", name: "Raydium", category: "protocol", value: 24 },
    { id: "aero", name: "Aerodrome", category: "protocol", value: 22 },
    { id: "lido", name: "Lido", category: "protocol", value: 34 },
    { id: "link", name: "Chainlink", category: "oracle", value: 30 },
    { id: "pyth", name: "Pyth", category: "oracle", value: 20 },
    { id: "wormhole", name: "Wormhole", category: "bridge", value: 22 },
    { id: "lz", name: "LayerZero", category: "bridge", value: 24 },
  ];
  const links: DigitalWorldOverview["graph"]["links"] = [
    ["eth", "arb", 8], ["eth", "base", 8], ["eth", "uni", 6], ["eth", "aave", 6], ["eth", "lido", 7], ["eth", "usdc", 6], ["eth", "usdt", 6],
    ["sol", "jup", 7], ["sol", "ray", 5], ["sol", "usdc", 5], ["sol", "pyth", 4], ["base", "aero", 6], ["base", "usdc", 5],
    ["tron", "usdt", 9], ["bnb", "usdt", 5], ["link", "eth", 5], ["link", "arb", 3], ["link", "base", 3], ["pyth", "arb", 2],
    ["wormhole", "sol", 4], ["wormhole", "eth", 4], ["lz", "eth", 4], ["lz", "arb", 3], ["lz", "bnb", 3], ["btc", "wormhole", 2], ["ton", "usdt", 4], ["arb", "uni", 3], ["arb", "aave", 3],
  ].map(([source, target, value]) => ({ source: source as string, target: target as string, value: value as number }));
  return {
    graph: { nodes, links },
    chains: [
      { id: "eth", name: "Ethereum", tvl: 86.4e9, change7d: 3.1, tps: 18.2, fees24h: 2.9e6, status: "DEMO" },
      { id: "sol", name: "Solana", tvl: 13.8e9, change7d: 7.4, tps: 3_120, fees24h: 1.6e6, status: "DEMO" },
      { id: "bnb", name: "BNB Chain", tvl: 8.9e9, change7d: 1.2, tps: 142, fees24h: 0.9e6, status: "DEMO" },
      { id: "base", name: "Base", tvl: 5.2e9, change7d: 4.8, tps: 96, fees24h: 0.7e6, status: "DEMO" },
      { id: "arb", name: "Arbitrum", tvl: 3.4e9, change7d: -0.8, tps: 38, fees24h: 0.2e6, status: "DEMO" },
      { id: "tron", name: "Tron", tvl: 6.1e9, change7d: 0.4, tps: 64, fees24h: 1.1e6, status: "DEMO" },
      { id: "ton", name: "TON", tvl: null, change7d: null, tps: null, fees24h: null, status: "UNAVAILABLE" },
    ],
    totals: { tvl: 168.2e9, stablecoinSupply: 289.4e9, dexVolume24h: 18.6e9, activeAddresses: 14.2e6 },
    activity: [
      { id: "dex", label: L("حجم DEX (میلیارد $)", "DEX volume ($B)"), points: series("dw:dex", 60, 18.6, DAY, 0.06, 0.004, now, 2) },
      { id: "stable", label: L("عرضه استیبل‌کوین (میلیارد $)", "Stablecoin supply ($B)"), points: series("dw:stable", 60, 289.4, DAY, 0.004, 0.0012, now, 1) },
    ],
  };
}

export function mockEarth(now = Date.now()): EarthOverview {
  return {
    centers: [
      { id: "tehran", name: L("تهران", "Tehran"), lat: 35.6892, lng: 51.389, timeZone: "Asia/Tehran", exchangeId: "tse-ir", indexSymbol: "TEDPIX", indexChange: -0.64, tier: 1 },
      { id: "newyork", name: L("نیویورک", "New York"), lat: 40.7128, lng: -74.006, timeZone: "America/New_York", exchangeId: "nyse", indexSymbol: "SPX", indexChange: 0.42, tier: 1 },
      { id: "london", name: L("لندن", "London"), lat: 51.5074, lng: -0.1278, timeZone: "Europe/London", exchangeId: "lse", indexSymbol: "FTSE100", indexChange: 0.07, tier: 1 },
      { id: "frankfurt", name: L("فرانکفورت", "Frankfurt"), lat: 50.1109, lng: 8.6821, timeZone: "Europe/Berlin", exchangeId: "xetra", indexSymbol: "DAX", indexChange: 0.33, tier: 2 },
      { id: "tokyo", name: L("توکیو", "Tokyo"), lat: 35.6762, lng: 139.6503, timeZone: "Asia/Tokyo", exchangeId: "tse-jp", indexSymbol: "N225", indexChange: 1.18, tier: 1 },
      { id: "hongkong", name: L("هنگ‌کنگ", "Hong Kong"), lat: 22.3193, lng: 114.1694, timeZone: "Asia/Hong_Kong", exchangeId: "hkex", indexSymbol: "HSI", indexChange: -0.92, tier: 2 },
      { id: "shanghai", name: L("شانگهای", "Shanghai"), lat: 31.2304, lng: 121.4737, timeZone: "Asia/Shanghai", exchangeId: null, indexSymbol: "SSEC", indexChange: 0.21, tier: 2 },
      { id: "dubai", name: L("دبی", "Dubai"), lat: 25.2048, lng: 55.2708, timeZone: "Asia/Dubai", exchangeId: null, indexSymbol: "DFMGI", indexChange: null, tier: 2 },
      { id: "mumbai", name: L("بمبئی", "Mumbai"), lat: 19.076, lng: 72.8777, timeZone: "Asia/Kolkata", exchangeId: null, indexSymbol: "NIFTY50", indexChange: 0.28, tier: 2 },
      { id: "singapore", name: L("سنگاپور", "Singapore"), lat: 1.3521, lng: 103.8198, timeZone: "Asia/Singapore", exchangeId: null, indexSymbol: "STI", indexChange: null, tier: 3 },
      { id: "sydney", name: L("سیدنی", "Sydney"), lat: -33.8688, lng: 151.2093, timeZone: "Australia/Sydney", exchangeId: null, indexSymbol: "ASX200", indexChange: null, tier: 3 },
      { id: "saopaulo", name: L("سائوپائولو", "São Paulo"), lat: -23.5505, lng: -46.6333, timeZone: "America/Sao_Paulo", exchangeId: null, indexSymbol: "IBOV", indexChange: null, tier: 3 },
      { id: "zurich", name: L("زوریخ", "Zurich"), lat: 47.3769, lng: 8.5417, timeZone: "Europe/Zurich", exchangeId: null, indexSymbol: "SMI", indexChange: null, tier: 3 },
      { id: "istanbul", name: L("استانبول", "Istanbul"), lat: 41.0082, lng: 28.9784, timeZone: "Europe/Istanbul", exchangeId: null, indexSymbol: "XU100", indexChange: null, tier: 3 },
    ],
    links: [
      { from: "tehran", to: "dubai" },
      { from: "tehran", to: "istanbul" },
      { from: "tehran", to: "frankfurt" },
      { from: "tehran", to: "mumbai" },
      { from: "tehran", to: "shanghai" },
      { from: "london", to: "newyork" },
      { from: "frankfurt", to: "london" },
      { from: "tokyo", to: "hongkong" },
      { from: "hongkong", to: "singapore" },
      { from: "newyork", to: "saopaulo" },
      { from: "dubai", to: "london" },
      { from: "singapore", to: "sydney" },
    ],
    iran: {
      summary: L(
        "نمای ایران: شاخص‌های منتخب بازار داخلی و انرژی. همه مقادیر در این نسخه نمایشی‌اند.",
        "Iran view: selected domestic-market and energy indicators. All values in this build are demo.",
      ),
      indicators: [
        { id: "tedpix", label: L("شاخص کل بورس تهران", "TEDPIX"), value: 3_084_500, unit: L("واحد", "pts"), change: -0.64, decimals: 0, status: "STALE", retrievedAt: new Date(now - 2 * DAY).toISOString(), source: "mock/tse" },
        { id: "usd", label: L("دلار بازار آزاد", "USD (free market)"), value: 112_850, unit: L("تومان", "IRT"), change: 0.36, decimals: 0, status: "STALE", retrievedAt: new Date(now - 3 * HOUR).toISOString(), source: "mock/fx-ir" },
        { id: "emami", label: L("سکه امامی", "Emami coin"), value: 118_400_000, unit: L("تومان", "IRT"), change: 0.52, decimals: 0, status: "STALE", retrievedAt: new Date(now - 3 * HOUR).toISOString(), source: "mock/gold-ir" },
        { id: "brent", label: L("نفت برنت", "Brent"), value: 68.42, unit: L("دلار/بشکه", "USD/bbl"), change: 1.26, decimals: 2, status: "DEMO", retrievedAt: new Date(now - 40_000).toISOString(), source: "mock/markets" },
        { id: "heavy", label: L("نفت سنگین ایران", "Iran Heavy"), value: null, unit: L("دلار/بشکه", "USD/bbl"), change: null, decimals: 2, status: "UNKNOWN", retrievedAt: null, source: "mock/no-public-source" },
        { id: "exports", label: L("صادرات نفت (برآورد)", "Oil exports (est.)"), value: null, unit: L("هزار بشکه/روز", "kb/d"), change: null, decimals: 0, status: "UNAVAILABLE", retrievedAt: null, source: "mock/tanker-tracking" },
      ],
    },
  };
}
