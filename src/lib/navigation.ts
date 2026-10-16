import type { AhosIconName } from "../components/icons";
import { tr } from "./i18n";

export type Language = "fa" | "en";
export type Quality = "high" | "balanced" | "low";
export type NavItem = { id: string; fa: string; en: string; icon: AhosIconName; /** Real route; items without it are in-shell placeholders. */ href?: string };
export type NavGroup = { id: string; fa: string; en: string; items: NavItem[] };
export const navigation: NavGroup[] = [
  {
    id: "overview",
    fa: "فضای فرماندهی",
    en: "COMMAND",
    items: [
      {
        id: "command",
        fa: tr("fa", "brand.commandCenter"),
        en: "Command Center",
        icon: "nav/command-center",
      },
      { id: "digital", fa: "جهان دیجیتال", en: "Digital World", icon: "nav/digital-world" },
      { id: "earth", fa: "زمین و جهان", en: "Earth & Global", icon: "nav/earth" },
    ],
  },
  {
    id: "markets",
    fa: "هوشمندی بازار",
    en: "MARKET INTELLIGENCE",
    items: [
      {
        id: "prices",
        fa: tr("fa", "nav.markets"),
        en: "Market Prices",
        icon: "nav/market-prices",
      },
      {
        id: "trade-venue",
        fa: tr("fa", "tradeVenue.nav"),
        en: "Trade Venue",
        icon: "nav/paper-trading",
        href: "/arena/trade-venue",
      },
      {
        id: "opportunities",
        fa: tr("fa", "nav.signals"),
        en: "Opportunities",
        icon: "nav/opportunities",
      },
      { id: "oil", fa: "بازار نفت", en: "Oil", icon: "nav/oil" },
      { id: "gold", fa: "بازار طلا", en: "Gold", icon: "nav/gold" },
      { id: "us", fa: "سهام آمریکا", en: "US Equities", icon: "nav/us-equities" },
      { id: "eu", fa: "سهام اروپا", en: "EU Equities", icon: "nav/eu-equities" },
      { id: "asia", fa: "سهام آسیا", en: "Asia Equities", icon: "nav/asia-equities" },
      { id: "crypto", fa: "بازار رمزارز", en: "Crypto Market", icon: "nav/crypto-market" },
      {
        id: "tokens",
        fa: "هوشمندی توکن",
        en: "Token Intelligence",
        icon: "nav/token-intelligence",
      },
      { id: "news", fa: "اتاق خبر", en: "Newsroom", icon: "nav/newsroom" },
    ],
  },
  {
    id: "intelligence",
    fa: "پژوهش و هوش مصنوعی",
    en: "RESEARCH & INTELLIGENCE",
    items: [
      { id: "security", fa: "مرکز امنیت", en: "Security", icon: "nav/security" },
      { id: "workshop", fa: "کارگاه فناوری", en: "Tech Workshop", icon: "nav/tech-workshop" },
      {
        id: "university",
        fa: "دانشگاه AHOS",
        en: "University",
        icon: "nav/university",
      },
      { id: "research", fa: "مؤسسه پژوهش", en: "Research", icon: "nav/research" },
      {
        id: "kian",
        fa: "گفت‌وگو با کیان",
        en: "Kian Chat",
        icon: "nav/kian-chat",
      },
      { id: "agents", fa: tr("fa", "nav.agents"), en: "Agents", icon: "nav/agents" },
    ],
  },
  {
    id: "operations",
    fa: "عملیات و زیرساخت",
    en: "OPERATIONS",
    items: [
      {
        id: "paper",
        fa: tr("fa", "nav.positions"),
        en: "Paper Trading",
        icon: "nav/paper-trading",
      },
      {
        id: "portfolio",
        fa: "سبد دارایی",
        en: "Portfolio",
        icon: "nav/portfolio",
      },
      {
        id: "memory",
        fa: "حافظه و یادگیری",
        en: "Memory & Learning",
        icon: "nav/memory-learning",
      },
      {
        id: "errors",
        fa: "خطاها و بازیابی",
        en: "Errors",
        icon: "nav/errors-recovery",
      },
      { id: "reports", fa: "گزارش‌ها", en: "Reports", icon: "nav/reports-evidence" },
      { id: "system", fa: "سیستم و اجرا", en: "System", icon: "nav/system-runtime" },
      {
        id: "white-hats",
        fa: tr("fa", "whiteHats.nav"),
        en: "White Hats & Judge",
        icon: "nav/governance-audit",
        href: "/arena/white-hats",
      },
      { id: "governance", fa: "حاکمیت", en: "Governance", icon: "nav/governance-audit" },
      { id: "settings", fa: tr("fa", "nav.settings"), en: "Settings", icon: "nav/settings" },
    ],
  },
];
export const allItems = navigation.flatMap((group) => group.items);
export const stageModules: { icon: AhosIconName; fa: string; en: string; sub: string }[] = [
  {
    icon: "nav/earth",
    fa: "زمین تعاملی",
    en: "Interactive Earth",
    sub: "GLOBAL INTELLIGENCE",
  },
  {
    icon: "nav/market-prices",
    fa: "داده‌ها و بازارها",
    en: "Market intelligence",
    sub: "EVIDENCE FIRST",
  },
  {
    icon: "nav/agents",
    fa: "عامل‌های هوشمند",
    en: "Agent workspace",
    sub: "EXPLICIT STATE",
  },
  {
    icon: "nav/university",
    fa: "پژوهش و یادگیری",
    en: "Research & learning",
    sub: "KNOWLEDGE SYSTEM",
  },
];
export const workspaceIcon: AhosIconName = "nav/system-runtime";
