const GLOSSARY: Array<[RegExp, string]> = [
  [/\bbitcoin\b/gi, "بیت‌کوین"],
  [/\bbtc\b/gi, "بیت‌کوین"],
  [/\bethereum\b/gi, "اتریوم"],
  [/\beth\b/gi, "اتریوم"],
  [/\bsolana\b/gi, "سولانا"],
  [/\bsol\b/gi, "سولانا"],
  [/\bhack(?:ed|ing)?\b/gi, "هک"],
  [/\bexploit(?:ed|s)?\b/gi, "سوءاستفاده امنیتی"],
  [/\breach(?:ed)?\b/gi, "رخنه"],
  [/\blisting\b/gi, "لیست شدن"],
  [/\blisted\b/gi, "لیست شد"],
  [/\betf\b/gi, "صندوق ETF"],
  [/\bsec\b/gi, "کمیسیون بورس آمریکا"],
  [/\bregulat(?:ion|ory|es|ed)\b/gi, "قانون‌گذاری"],
  [/\bwhale[s]?\b/gi, "نهنگ"],
  [/\bpump(?:ing)?\b/gi, "پامپ"],
  [/\bdump(?:ing)?\b/gi, "دامپ"],
  [/\bliquidity\b/gi, "نقدینگی"],
  [/\bvolume\b/gi, "حجم معاملات"],
  [/\bmarket cap(?:italization)?\b/gi, "ارزش بازار"],
  [/\bairdrop\b/gi, "ایردراپ"],
  [/\bdefi\b/gi, "دیفای"],
  [/\bnft\b/gi, "NFT"],
  [/\bstablecoin\b/gi, "استیبل‌کوین"],
  [/\btether\b/gi, "تتر"],
  [/\busdt\b/gi, "تتر"],
  [/\busdc\b/gi, "یو‌اس‌دی‌سی"],
  [/\bbinance\b/gi, "بایننس"],
  [/\bcoinbase\b/gi, "کوین‌بیس"],
  [/\bfederal reserve\b/gi, "فدرال رزرو"],
  [/\binterest rate\b/gi, "نرخ بهره"],
  [/\binflation\b/gi, "تورم"],
  [/\brally\b/gi, "رالی صعودی"],
  [/\bcrash\b/gi, "سقوط"],
  [/\bsurge\b/gi, "جهش"],
  [/\bplunge\b/gi, "ریزش"],
  [/\boutage\b/gi, "اختلال"],
  [/\bmainnet\b/gi, "مین‌نت"],
  [/\btestnet\b/gi, "تست‌نت"],
  [/\btoken\b/gi, "توکن"],
  [/\bcrypto(?:currency)?\b/gi, "رمزارز"],
  [/\bblockchain\b/gi, "بلاکچین"],
  [/\bwallet\b/gi, "کیف پول"],
  [/\bexchange\b/gi, "صرافی"],
  [/\bsecu(?:rity|re)\b/gi, "امنیت"],
  [/\bhoneypot\b/gi, "هانی‌پات"],
  [/\brug\s*pull\b/gi, "راگ‌پول"],
  [/\bscam\b/gi, "کلاهبرداری"],
  [/\bapproval\b/gi, "تأیید"],
  [/\breject(?:ed|ion)?\b/gi, "رد"],
  [/\blaunch(?:ed|es)?\b/gi, "راه‌اندازی"],
  [/\bupgrade\b/gi, "ارتقاء"],
  [/\bfork\b/gi, "فورک"],
  [/\bstaking\b/gi, "استیکینگ"],
  [/\byield\b/gi, "بازده"],
  [/\bprice\b/gi, "قیمت"],
  [/\brises?\b/gi, "افزایش"],
  [/\bfalls?\b/gi, "کاهش"],
  [/\bgains?\b/gi, "سود"],
  [/\bloss(?:es)?\b/gi, "زیان"],
  [/\binvestors?\b/gi, "سرمایه‌گذاران"],
  [/\btraders?\b/gi, "معامله‌گران"],
  [/\bmarket\b/gi, "بازار"],
  [/\bbullish\b/gi, "صعودی"],
  [/\bbearish\b/gi, "نزولی"],
  [/\ball-time high\b/gi, "اوج تاریخی"],
  [/\bath\b/gi, "اوج تاریخی"],
  [/\bsec chair\b/gi, "رئیس کمیسیون بورس"],
  [/\bspot etf\b/gi, "ETF اسپات"],
];

const CATEGORY_RULES: Array<{ re: RegExp; cat: string; importance: "HIGH" | "MED" | "LOW" }> = [
  { re: /\b(hack|exploit|breach|rug.?pull|honeypot|exploit(ed)?|drained)\b/i, cat: "امنیت/هک", importance: "HIGH" },
  { re: /\b(etf|sec|regulat|lawsuit|ban|sanction|ofac)\b/i, cat: "قانون‌گذاری", importance: "HIGH" },
  { re: /\b(listing|lists|listed on)\b/i, cat: "لیست شدن", importance: "MED" },
  { re: /\b(whale|large transfer|outflow|inflow)\b/i, cat: "نهنگ", importance: "MED" },
  { re: /\b(solana|sol\b)\b/i, cat: "سولانا", importance: "MED" },
  { re: /\b(ethereum|eth\b)\b/i, cat: "اتریوم", importance: "MED" },
  { re: /\b(bitcoin|btc\b)\b/i, cat: "بیت‌کوین", importance: "MED" },
  { re: /\b(fed|inflation|interest rate|cpi|jobs)\b/i, cat: "کلان‌اقتصاد", importance: "HIGH" },
  { re: /\b(ai|agent|gpt|model)\b/i, cat: "هوش مصنوعی × رمزارز", importance: "MED" },
  { re: /\b(defi|tvl|uniswap|aave|lido)\b/i, cat: "دیفای", importance: "MED" },
  { re: /\b(launch|airdrop|meme|pump)\b/i, cat: "راه‌اندازی توکن", importance: "LOW" },
];

export function classifyNews(title: string, body: string): {
  category: string;
  importance: "HIGH" | "MED" | "LOW" | "UNKNOWN";
  sentiment: "POS" | "NEG" | "NEU" | "UNKNOWN";
  relatedTokens: string[];
  relatedChains: string[];
  impact: "HIGH" | "MED" | "LOW" | "UNKNOWN";
} {
  const text = `${title} ${body}`;
  let category = "عمومی رمزارز";
  let importance: "HIGH" | "MED" | "LOW" | "UNKNOWN" = "UNKNOWN";
  for (const rule of CATEGORY_RULES) {
    if (rule.re.test(text)) {
      category = rule.cat;
      importance = rule.importance;
      break;
    }
  }
  const neg = /\b(hack|exploit|crash|ban|lawsuit|loss|plunge|scam|rug|outage|sell-off)\b/i.test(text);
  const pos = /\b(rally|surge|ath|approval|etf inflows|partnership|upgrade|record)\b/i.test(text);
  let sentiment: "POS" | "NEG" | "NEU" | "UNKNOWN" = "UNKNOWN";
  if (neg && !pos) sentiment = "NEG";
  else if (pos && !neg) sentiment = "POS";
  else if (pos && neg) sentiment = "NEU";

  const relatedTokens: string[] = [];
  const relatedChains: string[] = [];
  if (/\b(bitcoin|btc)\b/i.test(text)) relatedTokens.push("BTC");
  if (/\b(ethereum|eth)\b/i.test(text)) relatedTokens.push("ETH");
  if (/\b(solana|sol)\b/i.test(text)) relatedTokens.push("SOL");
  if (/\bxrp\b/i.test(text)) relatedTokens.push("XRP");
  if (/\bdoge/i.test(text)) relatedTokens.push("DOGE");
  if (relatedTokens.includes("BTC")) relatedChains.push("bitcoin");
  if (relatedTokens.includes("ETH")) relatedChains.push("ethereum");
  if (relatedTokens.includes("SOL")) relatedChains.push("solana");

  const impact = importance;
  return { category, importance, sentiment, relatedTokens, relatedChains, impact };
}

export function glossaryTranslate(input: string): string {
  let out = input;
  for (const [re, fa] of GLOSSARY) out = out.replace(re, fa);
  return out;
}

export function persianNewsRewrite(title: string, summary: string, source: string): { titleFa: string; summaryFa: string } {
  const titleFa = polishFa(glossaryTranslate(title));
  const body = summary ? glossaryTranslate(summary) : "";
  const cls = classifyNews(title, summary);
  const summaryFa = [
    `منبع: ${source}.`,
    body ? clip(body, 280) : "خلاصه اصلی منبع خالی بود — INSUFFICIENT_EVIDENCE برای جزئیات بیشتر.",
    `طبقه‌بندی شواهدی: ${cls.category}. اهمیت: ${cls.importance}. حس خبر: ${cls.sentiment}.`,
  ].join(" ");
  return { titleFa, summaryFa };
}

function polishFa(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

function clip(s: string, n: number): string {
  const t = s.replace(/\s+/g, " ").trim();
  if (t.length <= n) return t;
  return `${t.slice(0, n)}…`;
}

export function faNumber(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "نامشخص";
  return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: digits }).format(n);
}

export function faUsd(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "نامشخص";
  const abs = Math.abs(n);
  if (abs >= 1e12) return `${faNumber(n / 1e12, 2)} تریلیون دلار`;
  if (abs >= 1e9) return `${faNumber(n / 1e9, 2)} میلیارد دلار`;
  if (abs >= 1e6) return `${faNumber(n / 1e6, 2)} میلیون دلار`;
  if (abs >= 1e3) return `${faNumber(n / 1e3, 2)} هزار دلار`;
  return `${faNumber(n, n < 1 ? 6 : 2)} دلار`;
}

export function faPct(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "نامشخص";
  const sign = n > 0 ? "+" : "";
  return `${sign}${faNumber(n, 2)}٪`;
}

export function faTime(iso: string | null | undefined): string {
  if (!iso) return "نامشخص";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "نامشخص";
  return new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(d);
}
