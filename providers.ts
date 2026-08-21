import { envKey, fetchJson } from "./http";
import {
  asNumber,
  asString,
  tokenKey,
  type Envelope,
  type MarketAsset,
  type PairObservation,
  type ProviderStatus,
  type SecurityAssessment,
} from "./types";

type AnyRec = Record<string, unknown>;

export type MarketBundle = {
  envelopes: Envelope<unknown>[];
  assets: MarketAsset[];
  pairs: PairObservation[];
  global: {
    totalMcap: number | null;
    mcapChange24h: number | null;
    btcDominance: number | null;
    defiTvl: number | null;
    fearGreed: number | null;
    fearGreedLabel: string | null;
    btcHash: number | null;
    mempoolFee: number | null;
  };
  blocked: Array<{ provider: string; status: ProviderStatus; reasonFa: string }>;
};

function rec(v: unknown): AnyRec {
  return v && typeof v === "object" ? (v as AnyRec) : {};
}

function arr(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function pairFromDex(p: AnyRec, source: string): PairObservation | null {
  const base = rec(p.baseToken);
  const quote = rec(p.quoteToken);
  const symbol = asString(base.symbol) || asString(p.symbol);
  if (!symbol) return null;
  const chain = asString(p.chainId) || asString(p.chain) || "unknown";
  const address = asString(base.address) || asString(p.tokenAddress);
  const liq = rec(p.liquidity);
  const vol = rec(p.volume);
  const ch = rec(p.priceChange);
  const tx = rec(p.txns);
  const tx24 = rec(tx.h24);
  const boosts = rec(p.boosts);
  const info = rec(p.info);
  const created = asNumber(p.pairCreatedAt);
  return {
    tokenKey: tokenKey(chain, address, symbol),
    symbol: symbol.toUpperCase(),
    name: asString(base.name) || symbol.toUpperCase(),
    chain,
    address,
    pairAddress: asString(p.pairAddress),
    dexId: asString(p.dexId),
    url: asString(p.url),
    imageUrl: asString(info.imageUrl) || asString(p.icon),
    priceUsd: asNumber(p.priceUsd),
    liquidityUsd: asNumber(liq.usd) ?? asNumber(p.liquidity),
    volume24h: asNumber(vol.h24) ?? asNumber(p.volume),
    fdv: asNumber(p.fdv),
    marketCap: asNumber(p.marketCap),
    priceChange5m: asNumber(ch.m5),
    priceChange1h: asNumber(ch.h1),
    priceChange6h: asNumber(ch.h6),
    priceChange24h: asNumber(ch.h24),
    buys24h: asNumber(tx24.buys) !== null ? Math.round(asNumber(tx24.buys) as number) : null,
    sells24h: asNumber(tx24.sells) !== null ? Math.round(asNumber(tx24.sells) as number) : null,
    pairCreatedAt: created ? new Date(created).toISOString() : null,
    boostActive: asNumber(boosts.active),
    paidPromotion: (asNumber(boosts.active) ?? 0) > 0,
    source,
    labels: [asString(quote.symbol), ...arr(p.labels).map((x) => String(x))].filter(Boolean) as string[],
  };
}

function pairFromGecko(item: AnyRec, source: string): PairObservation | null {
  const attrs = rec(item.attributes);
  const name = asString(attrs.name) || "";
  const symbol = name.split(" / ")[0] || asString(attrs.base_token_symbol) || asString(attrs.name);
  if (!symbol) return null;
  const rel = rec(item.relationships);
  const baseRel = rec(rec(rel.base_token).data);
  const netRel = rec(rec(rel.network).data);
  const chain = asString(netRel.id) || asString(attrs.network) || "unknown";
  const address = asString(baseRel.id) || asString(attrs.address);
  const vol = rec(attrs.volume_usd);
  const ch = rec(attrs.price_change_percentage);
  const tx = rec(attrs.transactions);
  const h24 = rec(tx.h24);
  return {
    tokenKey: tokenKey(chain, address, symbol),
    symbol: symbol.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 16) || symbol.toUpperCase(),
    name,
    chain,
    address,
    pairAddress: asString(attrs.address) || asString(item.id),
    dexId: asString(rec(rec(rel.dex).data).id),
    url: asString(attrs.pool_url) || null,
    imageUrl: null,
    priceUsd: asNumber(attrs.base_token_price_usd),
    liquidityUsd: asNumber(attrs.reserve_in_usd),
    volume24h: asNumber(vol.h24),
    fdv: asNumber(attrs.fdv_usd),
    marketCap: asNumber(attrs.market_cap_usd),
    priceChange5m: asNumber(ch.m5),
    priceChange1h: asNumber(ch.h1),
    priceChange6h: asNumber(ch.h6),
    priceChange24h: asNumber(ch.h24),
    buys24h: asNumber(h24.buys) !== null ? Math.round(asNumber(h24.buys) as number) : null,
    sells24h: asNumber(h24.sells) !== null ? Math.round(asNumber(h24.sells) as number) : null,
    pairCreatedAt: asString(attrs.pool_created_at),
    boostActive: null,
    paidPromotion: false,
    source,
    labels: [],
  };
}

export async function collectMarket(): Promise<MarketBundle> {
  const blocked: MarketBundle["blocked"] = [
    {
      provider: "DEXTools",
      status: envKey("DEXTOOLS_API_KEY") ? "UNKNOWN" : "NO_KEY",
      reasonFa: envKey("DEXTOOLS_API_KEY")
        ? "کلید هست اما آداپتر پولی هنوز به مسیر رایگان وصل نشده — COST_BLOCKED تا تأیید لایسنس."
        : "DEXTools لایه رایگان عمومی ندارد — NO_KEY / COST_BLOCKED.",
    },
    {
      provider: "CoinMarketCap",
      status: envKey("COINMARKETCAP_API_KEY") ? "UNKNOWN" : "NO_KEY",
      reasonFa: envKey("COINMARKETCAP_API_KEY")
        ? "کلید موجود است اما در این موج از مسیر رایگان CoinGecko استفاده می‌شود."
        : "بدون کلید CMC — NO_KEY. از CoinGecko و DexScreener استفاده شد.",
    },
    { provider: "X/Twitter", status: "COST_BLOCKED", reasonFa: "API رسمی X پولی است — COST_BLOCKED." },
    { provider: "Instagram", status: "OUT_OF_POLICY", reasonFa: "اسکرپینگ اینستاگرام خارج از سیاست است." },
    { provider: "TikTok", status: "OUT_OF_POLICY", reasonFa: "اسکرپینگ تیک‌تاک خارج از سیاست است." },
    { provider: "Telegram-scrape", status: "OUT_OF_POLICY", reasonFa: "اسکرپینگ تلگرام خارج از سیاست است. Bot API فقط با توکن کاربر." },
  ];

  const jobs = [
    fetchJson<AnyRec>("CoinGecko", "market", "https://api.coingecko.com/api/v3/global"),
    fetchJson<AnyRec>(
      "CoinGecko",
      "market",
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple,dogecoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true",
    ),
    fetchJson<unknown>(
      "CoinGecko",
      "market",
      "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=30&page=1&sparkline=false&price_change_percentage=24h",
    ),
    fetchJson<AnyRec>("CoinGecko", "discovery", "https://api.coingecko.com/api/v3/search/trending"),
    fetchJson<AnyRec>("Alternative.me", "market", "https://api.alternative.me/fng/?limit=1"),
    fetchJson<unknown>(
      "Binance",
      "market",
      "https://api.binance.com/api/v3/ticker/24hr?symbols=%5B%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22%5D",
    ),
    fetchJson<AnyRec>("CoinCap", "market", "https://api.coincap.io/v2/assets?limit=20"),
    fetchJson<AnyRec>(
      "CryptoCompare",
      "market",
      "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,SOL&tsyms=USD",
    ),
    fetchJson<unknown>("DefiLlama", "market", "https://api.llama.fi/v2/historicalChainTvl/Solana"),
    fetchJson<unknown>("DefiLlama", "market", "https://api.llama.fi/tvl"),
    fetchJson<AnyRec>("mempool.space", "market", "https://mempool.space/api/v1/fees/recommended"),
    fetchJson<AnyRec>("Blockchain.com", "market", "https://api.blockchain.info/stats"),
    fetchJson<unknown>("DexScreener", "discovery", "https://api.dexscreener.com/token-boosts/top/v1"),
    fetchJson<unknown>("DexScreener", "discovery", "https://api.dexscreener.com/token-boosts/latest/v1"),
    fetchJson<unknown>("DexScreener", "discovery", "https://api.dexscreener.com/token-profiles/latest/v1"),
    fetchJson<unknown>("DexScreener", "discovery", "https://api.dexscreener.com/metas/trending/v1"),
    fetchJson<AnyRec>("DexScreener", "discovery", "https://api.dexscreener.com/latest/dex/search?q=SOL"),
    fetchJson<AnyRec>("DexScreener", "discovery", "https://api.dexscreener.com/latest/dex/search?q=pump"),
    fetchJson<AnyRec>("DexScreener", "discovery", "https://api.dexscreener.com/latest/dex/search?q=ETH"),
    fetchJson<AnyRec>("GeckoTerminal", "discovery", "https://api.geckoterminal.com/api/v2/networks/trending_pools?page=1"),
    fetchJson<AnyRec>("GeckoTerminal", "discovery", "https://api.geckoterminal.com/api/v2/networks/solana/trending_pools"),
    fetchJson<AnyRec>("GeckoTerminal", "discovery", "https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page=1"),
    fetchJson<AnyRec>("GeckoTerminal", "discovery", "https://api.geckoterminal.com/api/v2/networks/eth/trending_pools"),
    fetchJson<AnyRec>("GeckoTerminal", "discovery", "https://api.geckoterminal.com/api/v2/networks/base/trending_pools"),
    fetchJson<unknown>(
      "Pump.fun",
      "discovery",
      "https://frontend-api-v3.pump.fun/coins?offset=0&limit=30&sort=currently_live&order=DESC&includeNsfw=false",
    ),
    fetchJson<AnyRec>(
      "Jupiter",
      "market",
      "https://lite-api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112",
    ),
    fetchJson<AnyRec>("CoinPaprika", "market", "https://api.coinpaprika.com/v1/global"),
    fetchJson<unknown>("CoinPaprika", "market", "https://api.coinpaprika.com/v1/tickers?limit=15"),
  ];

  const envelopes = await Promise.all(jobs);
  const assets: MarketAsset[] = [];
  const pairs: PairObservation[] = [];
  const global: MarketBundle["global"] = {
    totalMcap: null,
    mcapChange24h: null,
    btcDominance: null,
    defiTvl: null,
    fearGreed: null,
    fearGreedLabel: null,
    btcHash: null,
    mempoolFee: null,
  };

  for (const env of envelopes) {
    if (env.status !== "SUCCESS" || env.data == null) continue;
    const data = env.data as unknown;

    if (env.provider === "CoinGecko" && env.url?.includes("/global")) {
      const d = rec(rec(data).data);
      global.totalMcap = asNumber(d.total_market_cap) ?? asNumber(rec(d.total_market_cap).usd);
      const tmc = rec(d.total_market_cap);
      if (global.totalMcap == null) global.totalMcap = asNumber(tmc.usd);
      global.mcapChange24h = asNumber(d.market_cap_change_percentage_24h_usd);
      global.btcDominance = asNumber(rec(d.market_cap_percentage).btc);
    }

    if (env.provider === "CoinGecko" && env.url?.includes("simple/price")) {
      const d = rec(data);
      for (const [id, raw] of Object.entries(d)) {
        const row = rec(raw);
        assets.push({
          id,
          symbol: id === "bitcoin" ? "BTC" : id === "ethereum" ? "ETH" : id === "solana" ? "SOL" : id.toUpperCase(),
          name: id,
          priceUsd: asNumber(row.usd),
          change24h: asNumber(row.usd_24h_change),
          marketCap: asNumber(row.usd_market_cap),
          volume24h: asNumber(row.usd_24h_vol),
          source: "CoinGecko",
        });
      }
    }

    if (env.provider === "CoinGecko" && env.url?.includes("coins/markets") && Array.isArray(data)) {
      for (const row of data) {
        const r = rec(row);
        assets.push({
          id: asString(r.id) || "",
          symbol: (asString(r.symbol) || "").toUpperCase(),
          name: asString(r.name) || "",
          priceUsd: asNumber(r.current_price),
          change24h: asNumber(r.price_change_percentage_24h),
          marketCap: asNumber(r.market_cap),
          volume24h: asNumber(r.total_volume),
          source: "CoinGecko",
        });
      }
    }

    if (env.provider === "CoinGecko" && env.url?.includes("trending")) {
      const coins = arr(rec(data).coins);
      for (const c of coins) {
        const item = rec(rec(c).item);
        assets.push({
          id: asString(item.id) || "",
          symbol: (asString(item.symbol) || "").toUpperCase(),
          name: asString(item.name) || "",
          priceUsd: asNumber(rec(item.data).price) ?? asNumber(item.price_btc),
          change24h: asNumber(rec(item.data).price_change_percentage_24h) ?? asNumber(rec(rec(item.data).price_change_percentage_24h).usd),
          marketCap: asNumber(String(item.market_cap || "").replace(/[^0-9.]/g, "")) ?? null,
          volume24h: null,
          source: "CoinGecko-trending",
        });
      }
    }

    if (env.provider === "Alternative.me") {
      const row = rec(arr(rec(data).data)[0]);
      global.fearGreed = asNumber(row.value);
      global.fearGreedLabel = asString(row.value_classification);
    }

    if (env.provider === "Binance" && Array.isArray(data)) {
      for (const row of data) {
        const r = rec(row);
        const sym = asString(r.symbol) || "";
        assets.push({
          id: sym,
          symbol: sym.replace("USDT", ""),
          name: sym,
          priceUsd: asNumber(r.lastPrice),
          change24h: asNumber(r.priceChangePercent),
          marketCap: null,
          volume24h: asNumber(r.quoteVolume),
          source: "Binance",
        });
      }
    }

    if (env.provider === "CoinCap") {
      for (const row of arr(rec(data).data)) {
        const r = rec(row);
        assets.push({
          id: asString(r.id) || "",
          symbol: (asString(r.symbol) || "").toUpperCase(),
          name: asString(r.name) || "",
          priceUsd: asNumber(r.priceUsd),
          change24h: asNumber(r.changePercent24Hr),
          marketCap: asNumber(r.marketCapUsd),
          volume24h: asNumber(r.volumeUsd24Hr),
          source: "CoinCap",
        });
      }
    }

    if (env.provider === "CryptoCompare") {
      const raw = rec(rec(data).RAW);
      for (const sym of ["BTC", "ETH", "SOL"]) {
        const usd = rec(rec(raw[sym]).USD);
        if (!Object.keys(usd).length) continue;
        assets.push({
          id: sym.toLowerCase(),
          symbol: sym,
          name: sym,
          priceUsd: asNumber(usd.PRICE),
          change24h: asNumber(usd.CHANGEPCT24HOUR),
          marketCap: asNumber(usd.MKTCAP),
          volume24h: asNumber(usd.TOTALVOLUME24HTO),
          source: "CryptoCompare",
        });
      }
    }

    if (env.provider === "DefiLlama" && env.url?.endsWith("/tvl")) {
      global.defiTvl = asNumber(data);
    }

    if (env.provider === "mempool.space") {
      global.mempoolFee = asNumber(rec(data).fastestFee);
    }

    if (env.provider === "Blockchain.com") {
      global.btcHash = asNumber(rec(data).hash_rate);
    }

    if (env.provider === "DexScreener" && env.url?.includes("latest/dex/search")) {
      for (const p of arr(rec(data).pairs)) {
        const mapped = pairFromDex(rec(p), "DexScreener");
        if (mapped) pairs.push(mapped);
      }
    }

    if (env.provider === "DexScreener" && (env.url?.includes("token-boosts") || env.url?.includes("token-profiles"))) {
      const list = Array.isArray(data) ? data : [data];
      for (const row of list) {
        const r = rec(row);
        const symbol = asString(r.symbol) || asString(r.description) || "BOOST";
        const chain = asString(r.chainId) || "unknown";
        const address = asString(r.tokenAddress);
        pairs.push({
          tokenKey: tokenKey(chain, address, symbol),
          symbol: symbol.slice(0, 16).toUpperCase(),
          name: asString(r.description) || symbol,
          chain,
          address,
          pairAddress: null,
          dexId: "dexscreener-boost",
          url: asString(r.url),
          imageUrl: asString(r.icon),
          priceUsd: null,
          liquidityUsd: null,
          volume24h: null,
          fdv: null,
          marketCap: null,
          priceChange5m: null,
          priceChange1h: null,
          priceChange6h: null,
          priceChange24h: null,
          buys24h: null,
          sells24h: null,
          pairCreatedAt: null,
          boostActive: asNumber(r.amount) ?? asNumber(r.totalAmount) ?? 1,
          paidPromotion: true,
          source: "DexScreener-boost",
          labels: ["PAID_PROMOTION"],
        });
      }
    }

    if (env.provider === "GeckoTerminal") {
      for (const row of arr(rec(data).data)) {
        const mapped = pairFromGecko(rec(row), "GeckoTerminal");
        if (mapped) pairs.push(mapped);
      }
    }

    if (env.provider === "Pump.fun" && Array.isArray(data)) {
      for (const row of data) {
        const r = rec(row);
        const symbol = asString(r.symbol);
        if (!symbol) continue;
        const address = asString(r.mint) || asString(r.address);
        pairs.push({
          tokenKey: tokenKey("solana", address, symbol),
          symbol: symbol.toUpperCase(),
          name: asString(r.name) || symbol,
          chain: "solana",
          address,
          pairAddress: asString(r.bonding_curve),
          dexId: "pumpfun",
          url: address ? `https://pump.fun/${address}` : "https://pump.fun",
          imageUrl: asString(r.image_uri),
          priceUsd: asNumber(r.usd_market_cap) && asNumber(r.total_supply)
            ? (asNumber(r.usd_market_cap) as number) / Math.max(asNumber(r.total_supply) as number, 1)
            : asNumber(r.price_usd),
          liquidityUsd: asNumber(r.virtual_sol_reserves),
          volume24h: asNumber(r.volume_24h),
          fdv: asNumber(r.usd_market_cap),
          marketCap: asNumber(r.usd_market_cap) ?? asNumber(r.market_cap),
          priceChange5m: null,
          priceChange1h: null,
          priceChange6h: null,
          priceChange24h: null,
          buys24h: null,
          sells24h: null,
          pairCreatedAt: asNumber(r.created_timestamp) ? new Date(asNumber(r.created_timestamp) as number).toISOString() : null,
          boostActive: null,
          paidPromotion: false,
          source: "Pump.fun",
          labels: ["launchpad"],
        });
      }
    }

    if (env.provider === "CoinPaprika" && env.url?.includes("/global")) {
      const r = rec(data);
      if (global.totalMcap == null) global.totalMcap = asNumber(r.market_cap_usd);
      if (global.btcDominance == null) global.btcDominance = asNumber(r.bitcoin_dominance_percentage);
    }
  }

  return { envelopes, assets, pairs, global, blocked };
}

export async function enrichPairs(pairs: PairObservation[]): Promise<PairObservation[]> {
  const need = pairs
    .filter((p) => p.address && (p.priceUsd == null || p.liquidityUsd == null))
    .slice(0, 12);
  if (!need.length) return pairs;
  const byChain = new Map<string, string[]>();
  for (const p of need) {
    if (!p.address) continue;
    const list = byChain.get(p.chain) || [];
    if (!list.includes(p.address)) list.push(p.address);
    byChain.set(p.chain, list);
  }
  const extra: PairObservation[] = [];
  await Promise.all(
    [...byChain.entries()].slice(0, 4).map(async ([chain, addrs]) => {
      const chunk = addrs.slice(0, 8).join(",");
      const env = await fetchJson<unknown>(
        "DexScreener",
        "discovery",
        `https://api.dexscreener.com/tokens/v1/${encodeURIComponent(chain)}/${chunk}`,
      );
      if (env.status !== "SUCCESS" || !env.data) return;
      const list = Array.isArray(env.data) ? env.data : arr(rec(env.data).pairs);
      for (const row of list) {
        const mapped = pairFromDex(rec(row), "DexScreener-tokens");
        if (mapped) extra.push(mapped);
      }
    }),
  );
  if (!extra.length) return pairs;
  const map = new Map<string, PairObservation>();
  for (const p of [...pairs, ...extra]) {
    const prev = map.get(p.tokenKey);
    if (!prev) {
      map.set(p.tokenKey, p);
      continue;
    }
    map.set(p.tokenKey, {
      ...prev,
      ...Object.fromEntries(
        Object.entries(p).filter(([, v]) => v !== null && v !== undefined && v !== false),
      ),
      paidPromotion: prev.paidPromotion || p.paidPromotion,
      boostActive: prev.boostActive ?? p.boostActive,
      source: `${prev.source}+${p.source}`,
    } as PairObservation);
  }
  return [...map.values()];
}

export async function fetchSecurity(token: PairObservation): Promise<SecurityAssessment> {
  if (!token.address) {
    return {
      provider: "none",
      status: "NO_DATA",
      honeypot: "UNKNOWN",
      sellable: "UNKNOWN",
      mintable: "UNKNOWN",
      freezeable: "UNKNOWN",
      ownership: "UNKNOWN",
      flags: ["NO_CONTRACT"],
      summaryFa: "آدرس قرارداد UNKNOWN است — امنیت را SAFE فرض نکن.",
      raw: null,
    };
  }
  const chain = token.chain.toLowerCase();
  if (chain.includes("sol")) {
    const env = await fetchJson<AnyRec>(
      "GoPlus",
      "security",
      `https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses=${encodeURIComponent(token.address)}`,
    );
    if (env.status === "SUCCESS" && env.data) {
      const result = rec(rec(env.data).result);
      const row = rec(result[token.address] || result[Object.keys(result)[0] || ""]);
      return mapGoplusSol(row, env.data);
    }
    const rug = await fetchJson<AnyRec>(
      "RugCheck",
      "security",
      `https://api.rugcheck.xyz/v1/tokens/${encodeURIComponent(token.address)}/report`,
    );
    if (rug.status === "SUCCESS" && rug.data) {
      return mapRugcheck(rec(rug.data));
    }
    return emptySec(env.status === "SUCCESS" ? rug.status : env.status, env.provider);
  }

  const chainId = evmId(chain);
  if (!chainId) {
    return emptySec("UNSUPPORTED", "GoPlus");
  }
  const env = await fetchJson<AnyRec>(
    "GoPlus",
    "security",
    `https://api.gopluslabs.io/api/v1/token_security/${chainId}?contract_addresses=${encodeURIComponent(token.address)}`,
  );
  if (env.status === "SUCCESS" && env.data) {
    const result = rec(rec(env.data).result);
    const row = rec(result[token.address.toLowerCase()] || result[Object.keys(result)[0] || ""]);
    return mapGoplusEvm(row);
  }
  return emptySec(env.status, "GoPlus");
}

function emptySec(status: ProviderStatus, provider: string): SecurityAssessment {
  return {
    provider,
    status,
    honeypot: "UNKNOWN",
    sellable: "UNKNOWN",
    mintable: "UNKNOWN",
    freezeable: "UNKNOWN",
    ownership: "UNKNOWN",
    flags: ["UNKNOWN_SECURITY"],
    summaryFa: "امنیت UNKNOWN است و هرگز معادل SAFE نیست.",
    raw: null,
  };
}

function yn(v: unknown, yes = "1"): "YES" | "NO" | "UNKNOWN" {
  if (v === undefined || v === null || v === "") return "UNKNOWN";
  const s = String(v).toLowerCase();
  if (s === yes || s === "true" || s === "yes") return "YES";
  if (s === "0" || s === "false" || s === "no") return "NO";
  return "UNKNOWN";
}

function mapGoplusEvm(row: AnyRec): SecurityAssessment {
  const honeypot = yn(row.is_honeypot);
  const buyTax = asNumber(row.buy_tax);
  const sellTax = asNumber(row.sell_tax);
  const flags: string[] = [];
  if (honeypot === "YES") flags.push("HONEYPOT");
  if (yn(row.is_blacklisted) === "YES") flags.push("BLACKLIST");
  if (yn(row.is_whitelisted) === "YES") flags.push("WHITELIST");
  if (yn(row.hidden_owner) === "YES") flags.push("HIDDEN_OWNER");
  if (yn(row.can_take_back_ownership) === "YES") flags.push("OWNERSHIP_RECLAIM");
  if (yn(row.is_proxy) === "YES") flags.push("PROXY");
  if (yn(row.is_mintable) === "YES") flags.push("MINTABLE");
  if (yn(row.transfer_pausable) === "YES") flags.push("TRANSFER_PAUSE");
  if (yn(row.trading_cooldown) === "YES") flags.push("COOLDOWN");
  if ((sellTax ?? 0) > 10) flags.push("HIGH_SELL_TAX");
  return {
    provider: "GoPlus",
    status: "SUCCESS",
    honeypot,
    sellable: honeypot === "YES" ? "NO" : honeypot === "NO" ? "YES" : "UNKNOWN",
    mintable: yn(row.is_mintable),
    freezeable: yn(row.transfer_pausable),
    ownership: yn(row.can_take_back_ownership) === "NO" && yn(row.hidden_owner) === "NO" ? "RENOUNCED" : yn(row.hidden_owner) === "YES" ? "OPEN" : "UNKNOWN",
    flags,
    summaryFa:
      flags.length > 0
        ? `پرچم‌های امنیتی واقعی GoPlus: ${flags.join("، ")}. مالیات خرید/فروش: ${buyTax ?? "UNKNOWN"} / ${sellTax ?? "UNKNOWN"}.`
        : "GoPlus پرچم بحرانی گزارش نکرد؛ این به معنی SAFE بودن کامل نیست.",
    raw: row,
  };
}

function mapGoplusSol(row: AnyRec, raw: unknown): SecurityAssessment {
  const flags: string[] = [];
  const mintableRaw = rec(row.mintable);
  const mintable =
    yn(mintableRaw.status || row.mintable, "true") === "YES" || String(row.mintAuthority) === "true"
      ? "YES"
      : yn(row.mintable);
  if (String(row.honeypot) === "true" || String(row.is_honeypot) === "1") flags.push("HONEYPOT");
  if (String(row.freezable) === "true" || String(row.freezeAuthority)) flags.push("FREEZE");
  const metadata = rec(row.metadata);
  return {
    provider: "GoPlus-Solana",
    status: "SUCCESS",
    honeypot: flags.includes("HONEYPOT") ? "YES" : "UNKNOWN",
    sellable: flags.includes("HONEYPOT") ? "NO" : "UNKNOWN",
    mintable: mintable === "YES" ? "YES" : mintable,
    freezeable: flags.includes("FREEZE") ? "YES" : "UNKNOWN",
    ownership: "UNKNOWN",
    flags,
    summaryFa: flags.length
      ? `GoPlus سولانا: ${flags.join("، ")}. متادیتا: ${asString(metadata.symbol) || "UNKNOWN"}.`
      : "GoPlus سولانا داده داد اما پرچم قطعی هانی‌پات نداشت — UNKNOWN ≠ SAFE.",
    raw: rec(raw),
  };
}

function mapRugcheck(row: AnyRec): SecurityAssessment {
  const score = asNumber(row.score);
  const risks = arr(row.risks).map((r) => asString(rec(r).name) || asString(rec(r).level) || "risk");
  const flags = risks.filter(Boolean) as string[];
  const token = rec(row.token);
  const mint = rec(token.mintAuthority || row.mintAuthority);
  return {
    provider: "RugCheck",
    status: "SUCCESS",
    honeypot: flags.some((f) => /honey/i.test(f)) ? "YES" : "UNKNOWN",
    sellable: "UNKNOWN",
    mintable: Object.keys(mint).length ? "YES" : "UNKNOWN",
    freezeable: "UNKNOWN",
    ownership: "UNKNOWN",
    flags,
    summaryFa: `RugCheck امتیاز خام ${score ?? "UNKNOWN"} و ریسک‌ها: ${flags.join("، ") || "نامشخص"}. امتیاز به‌تنهایی SAFE نیست.`,
    raw: row,
  };
}

function evmId(chain: string): string | null {
  if (chain === "ethereum" || chain === "eth") return "1";
  if (chain === "bsc" || chain === "bnb") return "56";
  if (chain === "polygon" || chain === "matic") return "137";
  if (chain === "arbitrum") return "42161";
  if (chain === "optimism") return "10";
  if (chain === "avalanche" || chain === "avax") return "43114";
  if (chain === "base") return "8453";
  if (chain === "fantom") return "250";
  if (chain === "cronos") return "25";
  return null;
}

export function mergePairs(list: PairObservation[]): PairObservation[] {
  const map = new Map<string, PairObservation>();
  for (const p of list) {
    const prev = map.get(p.tokenKey);
    if (!prev) {
      map.set(p.tokenKey, p);
      continue;
    }
    map.set(p.tokenKey, {
      ...prev,
      name: prev.name || p.name,
      address: prev.address || p.address,
      pairAddress: prev.pairAddress || p.pairAddress,
      dexId: prev.dexId || p.dexId,
      url: prev.url || p.url,
      imageUrl: prev.imageUrl || p.imageUrl,
      priceUsd: prev.priceUsd ?? p.priceUsd,
      liquidityUsd: prev.liquidityUsd ?? p.liquidityUsd,
      volume24h: prev.volume24h ?? p.volume24h,
      fdv: prev.fdv ?? p.fdv,
      marketCap: prev.marketCap ?? p.marketCap,
      priceChange5m: prev.priceChange5m ?? p.priceChange5m,
      priceChange1h: prev.priceChange1h ?? p.priceChange1h,
      priceChange6h: prev.priceChange6h ?? p.priceChange6h,
      priceChange24h: prev.priceChange24h ?? p.priceChange24h,
      buys24h: prev.buys24h ?? p.buys24h,
      sells24h: prev.sells24h ?? p.sells24h,
      pairCreatedAt: prev.pairCreatedAt || p.pairCreatedAt,
      boostActive: prev.boostActive ?? p.boostActive,
      paidPromotion: prev.paidPromotion || p.paidPromotion,
      source: prev.source.includes(p.source) ? prev.source : `${prev.source},${p.source}`,
      labels: [...new Set([...prev.labels, ...p.labels])],
    });
  }
  return [...map.values()];
}
