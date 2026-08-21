import { db } from "@/db";
import { translationCache } from "@/db/schema";
import { eq } from "drizzle-orm";
import { fetchText, sha1 } from "./http";
import { classifyNews, persianNewsRewrite } from "./persian";
import type { Envelope, NewsStory } from "./types";

/**
 * Free / public RSS and API sources only.
 * No scraping of X, Instagram, TikTok, Telegram channels (OUT_OF_POLICY).
 * If a source is DOWN → SOURCE_UNAVAILABLE. Never fabricate stories.
 */
export const NEWS_SOURCES: Array<{ id: string; fa: string; url: string }> = [
  { id: "CoinTelegraph", fa: "کوین‌تلگراف", url: "https://cointelegraph.com/rss" },
  { id: "CoinDesk", fa: "کوین‌دسک", url: "https://www.coindesk.com/arc/outboundfeeds/rss/" },
  { id: "Decrypt", fa: "دیکریپت", url: "https://decrypt.co/feed" },
  { id: "BitcoinMagazine", fa: "بیت‌کوین مگزین", url: "https://bitcoinmagazine.com/.rss/full/" },
  { id: "TheBlock", fa: "د بلاک", url: "https://www.theblock.co/rss.xml" },
  { id: "CryptoSlate", fa: "کریپتواسلیت", url: "https://cryptoslate.com/feed/" },
  { id: "BitcoinCom", fa: "بیت‌کوین دات‌کام", url: "https://news.bitcoin.com/feed/" },
  { id: "NewsBTC", fa: "نیوزبی‌تی‌سی", url: "https://www.newsbtc.com/feed/" },
  { id: "UToday", fa: "یو‌تودی", url: "https://u.today/rss" },
  { id: "AMBCrypto", fa: "ای‌ام‌بی کریپتو", url: "https://ambcrypto.com/feed/" },
  { id: "Blockworks", fa: "بلاک‌ورکس", url: "https://blockworks.co/feed" },
  { id: "CryptoNews", fa: "کریپتو نیوز", url: "https://crypto.news/feed/" },
  { id: "BeInCrypto", fa: "بی‌این‌کریپتو", url: "https://beincrypto.com/feed/" },
  { id: "CoinGape", fa: "کوین‌گِیپ", url: "https://coingape.com/feed/" },
  { id: "DailyHodl", fa: "دیلی‌هادل", url: "https://dailyhodl.com/feed/" },
  { id: "Bitcoinist", fa: "بیت‌کوینیست", url: "https://bitcoinist.com/feed/" },
  { id: "CryptoPotato", fa: "کریپتوپوتیتو", url: "https://cryptopotato.com/feed/" },
  { id: "CoinJournal", fa: "کوین‌ژورنال", url: "https://coinjournal.net/feed/" },
  { id: "CCN", fa: "سی‌سی‌ان", url: "https://www.ccn.com/feed/" },
  { id: "CoinSpeaker", fa: "کوین‌اسپیکر", url: "https://www.coinspeaker.com/feed/" },
  { id: "Cryptopolitan", fa: "کریپتوپولیتن", url: "https://www.cryptopolitan.com/feed/" },
  { id: "Coinpedia", fa: "کوین‌پدیا", url: "https://coinpedia.org/feed/" },
  { id: "CryptoBriefing", fa: "کریپتو بریفینگ", url: "https://cryptobriefing.com/feed/" },
  { id: "NullTX", fa: "نال‌تی‌ایکس", url: "https://nulltx.com/feed/" },
  { id: "CoinIdol", fa: "کوین‌آیدل", url: "https://coinidol.com/rss/" },
  { id: "CryptoDaily", fa: "کریپتو دیلی", url: "https://cryptodaily.co.uk/feed" },
  { id: "RedditCrypto", fa: "ردیت CryptoCurrency", url: "https://www.reddit.com/r/CryptoCurrency/new/.rss" },
  { id: "RedditSolana", fa: "ردیت Solana", url: "https://www.reddit.com/r/solana/new/.rss" },
  { id: "RedditDefi", fa: "ردیت DeFi", url: "https://www.reddit.com/r/defi/new/.rss" },
  { id: "RedditBitcoin", fa: "ردیت Bitcoin", url: "https://www.reddit.com/r/Bitcoin/new/.rss" },
  { id: "RedditEthTrader", fa: "ردیت ethtrader", url: "https://www.reddit.com/r/ethtrader/new/.rss" },
  { id: "HNAlgolia", fa: "هکرنیوز", url: "https://hn.algolia.com/api/v1/search?query=crypto%20OR%20bitcoin%20OR%20ethereum%20OR%20solana&tags=story" },
];

type RssItem = { title: string; link: string; date: string | null; summary: string };

function decode(s: string): string {
  return s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function parseRss(xml: string): RssItem[] {
  const items: RssItem[] = [];
  const chunks = xml.split(/<item[\s>]/i).slice(1);
  const entries = chunks.length ? chunks : xml.split(/<entry[\s>]/i).slice(1);
  for (const chunk of entries.slice(0, 12)) {
    const title = decode((chunk.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || "");
    const link =
      decode((chunk.match(/<link[^>]*href="([^"]+)"/i) || [])[1] || "") ||
      decode((chunk.match(/<link[^>]*>([\s\S]*?)<\/link>/i) || [])[1] || "");
    const date =
      decode((chunk.match(/<pubDate[^>]*>([\s\S]*?)<\/pubDate>/i) || [])[1] || "") ||
      decode((chunk.match(/<updated[^>]*>([\s\S]*?)<\/updated>/i) || [])[1] || "") ||
      decode((chunk.match(/<published[^>]*>([\s\S]*?)<\/published>/i) || [])[1] || "") ||
      null;
    const summary = decode(
      (chunk.match(/<description[^>]*>([\s\S]*?)<\/description>/i) || [])[1] ||
        (chunk.match(/<summary[^>]*>([\s\S]*?)<\/summary>/i) || [])[1] ||
        (chunk.match(/<content[^>]*>([\s\S]*?)<\/content>/i) || [])[1] ||
        "",
    );
    if (title) items.push({ title, link, date, summary });
  }
  return items;
}

async function translateFa(text: string): Promise<{ fa: string; engine: string }> {
  const sourceHash = sha1(text.slice(0, 800));
  try {
    const cached = await db.select().from(translationCache).where(eq(translationCache.sourceHash, sourceHash)).limit(1);
    if (cached[0]) return { fa: cached[0].translatedFa, engine: cached[0].engine };
  } catch {
    /* table may not exist yet during first boot */
  }
  const local = persianNewsRewrite(text, "", "local");
  let fa = local.titleFa;
  let engine = "glossary";
  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text.slice(0, 400))}&langpair=en|fa`;
    const res = await fetch(url, { cache: "no-store", headers: { "User-Agent": "AHOS-CommandCenter/1.0" } });
    if (res.ok) {
      const json = (await res.json()) as { responseData?: { translatedText?: string }; responseStatus?: number };
      const t = json.responseData?.translatedText;
      if (t && json.responseStatus === 200 && !/MYMEMORY WARNING/i.test(t)) {
        fa = t;
        engine = "MyMemory";
      }
    }
  } catch {
    /* keep glossary */
  }
  try {
    await db
      .insert(translationCache)
      .values({ sourceHash, sourceText: text.slice(0, 800), translatedFa: fa, engine })
      .onConflictDoNothing();
  } catch {
    /* ignore */
  }
  return { fa, engine };
}

export async function collectNews(): Promise<{ stories: NewsStory[]; envelopes: Envelope<unknown>[] }> {
  const envelopes: Envelope<unknown>[] = [];
  const stories: NewsStory[] = [];

  const results = await Promise.all(
    NEWS_SOURCES.map(async (src) => {
      if (src.id === "HNAlgolia") {
        const env = await fetchText(src.id, "news", src.url, 8000);
        envelopes.push(env);
        return { src, env };
      }
      const env = await fetchText(src.id, "news", src.url, 8000);
      envelopes.push(env);
      return { src, env };
    }),
  );

  const pending: Array<{ src: (typeof NEWS_SOURCES)[number]; item: RssItem }> = [];

  for (const { src, env } of results) {
    if (env.status !== "SUCCESS" || !env.data) continue;
    if (src.id === "HNAlgolia") {
      try {
        const json = JSON.parse(String(env.data)) as { hits?: Array<Record<string, unknown>> };
        for (const hit of json.hits || []) {
          const title = String(hit.title || "");
          if (!title) continue;
          pending.push({
            src,
            item: {
              title,
              link: String(hit.url || hit.story_url || ""),
              date: hit.created_at ? String(hit.created_at) : null,
              summary: String(hit.title || ""),
            },
          });
        }
      } catch {
        /* ignore */
      }
      continue;
    }
    for (const item of parseRss(String(env.data))) pending.push({ src, item });
  }

  const unique = new Map<string, { src: (typeof NEWS_SOURCES)[number]; item: RssItem }>();
  for (const row of pending) {
    const fp = sha1(`${row.src.id}|${row.item.title}`.toLowerCase());
    if (!unique.has(fp)) unique.set(fp, row);
  }

  const picked = [...unique.entries()].slice(0, 56);
  for (const [fp, row] of picked) {
    const cls = classifyNews(row.item.title, row.item.summary);
    const translated = await translateFa(row.item.title);
    const rewrite = persianNewsRewrite(row.item.title, row.item.summary, row.src.fa);
    const publishedAt = row.item.date ? new Date(row.item.date) : null;
    stories.push({
      fingerprint: fp,
      source: row.src.fa,
      sourceUrl: row.item.link || null,
      titleOriginal: row.item.title,
      titleFa: translated.fa || rewrite.titleFa,
      summaryFa: rewrite.summaryFa,
      publishedAt: publishedAt && !Number.isNaN(publishedAt.getTime()) ? publishedAt.toISOString() : null,
      importance: cls.importance,
      category: cls.category,
      sentiment: cls.sentiment,
      relatedTokens: cls.relatedTokens,
      relatedChains: cls.relatedChains,
      impact: cls.impact,
    });
  }

  stories.sort((a, b) => {
    const rank = { HIGH: 0, MED: 1, LOW: 2, UNKNOWN: 3 };
    const d = rank[a.importance] - rank[b.importance];
    if (d !== 0) return d;
    return (b.publishedAt || "").localeCompare(a.publishedAt || "");
  });

  return { stories, envelopes };
}
