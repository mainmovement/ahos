/**
 * Room text pack — bridges the i18n dictionary into the imperative 3D room
 * scene (canvas textures + floating role chips) without coupling the scene
 * to React. Persian dictionary is the source of truth.
 */
import type { Dictionary } from "@/lib/i18n";
import type { AssetId } from "./market-bus";
import type { WallClockId, WeatherKind } from "./derive";

export type RoleId =
  | "gold" | "crypto" | "memecoin" | "oil" | "eu" | "us" | "asia"
  | "news" | "whitehat" | "redteam" | "research" | "liaison";

export const ROLE_IDS: RoleId[] = [
  "gold", "crypto", "memecoin", "oil", "eu", "us", "asia",
  "news", "whitehat", "redteam", "research", "liaison",
];

/** Single source of truth: which live assets each role console tracks. */
export const ROLE_ASSETS: Record<RoleId, AssetId[]> = {
  gold: ["XAU", "PAXG"],
  crypto: ["BTC", "ETH", "SOL"],
  memecoin: ["DOGE", "SHIB", "PEPE"],
  oil: ["WTI", "BRENT"],
  eu: ["DAX", "FTSE"],
  us: ["IXIC", "GSPC"],
  asia: ["N225", "SSE"],
  news: [],
  whitehat: [],
  redteam: [],
  research: [],
  liaison: [],
};

export interface RoomTexts {
  locale: "fa" | "en";
  roles: Record<RoleId | "commander", string>;
  shortRoles: Record<RoleId, string>;
  weather: {
    title: string;
    live: string;
    offline: string;
    cond: Record<WeatherKind, string>;
  };
  market: {
    portfolioTitle: string;
    pnl: string;
    holdings: string;
    demoNote: string;
    clockTitle: string;
    clockNote: string;
    gridTitle: string;
    live: string;
    stale: string;
    offline: string;
    notConnected: string;
    sample: string;
    tape: string;
    buy: string;
    sell: string;
    updated: string;
    sources: string;
    newsTitle: string;
    offlineNews: string;
    assets: Record<AssetId, string>;
    clocks: Record<WallClockId, string>;
  };
  panel: {
    title: string;
    close: string;
    status: string;
    sampleNotice: string;
    noTape: string;
    holdingsRow: string;
  };
  hud: {
    fpvHint: string;
  };
}

export function buildRoomTexts(dict: Dictionary, locale: "fa" | "en"): RoomTexts {
  const room = dict.command.room;
  return {
    locale,
    roles: { ...room.roles },
    shortRoles: { ...room.shortRoles },
    weather: {
      title: room.weather.title,
      live: room.weather.live,
      offline: room.weather.offline,
      cond: { ...room.weather.cond },
    },
    market: {
      portfolioTitle: room.market.portfolioTitle,
      pnl: room.market.pnl,
      holdings: room.market.holdings,
      demoNote: room.market.demoNote,
      clockTitle: room.market.clockTitle,
      clockNote: room.market.clockNote,
      gridTitle: room.market.gridTitle,
      live: room.market.live,
      stale: room.market.stale,
      offline: room.market.offline,
      notConnected: room.market.notConnected,
      sample: room.market.sample,
      tape: room.market.tape,
      buy: room.market.buy,
      sell: room.market.sell,
      updated: room.market.updated,
      sources: room.market.sources,
      newsTitle: room.market.newsTitle,
      offlineNews: room.market.offlineNews,
      assets: { ...room.market.assets },
      clocks: { ...room.market.clocks },
    },
    panel: {
      title: room.panel.title,
      close: room.panel.close,
      status: room.panel.status,
      sampleNotice: room.panel.sampleNotice,
      noTape: room.panel.noTape,
      holdingsRow: room.panel.holdingsRow,
    },
    hud: {
      fpvHint: room.hud.fpvHint,
    },
  };
}
