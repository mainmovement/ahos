import {
  Activity,
  Atom,
  BarChart3,
  BookOpen,
  Bot,
  BrainCircuit,
  BriefcaseBusiness,
  ChartCandlestick,
  CircleDollarSign,
  Coins,
  Compass,
  Cpu,
  Database,
  Earth,
  FileChartColumn,
  FlaskConical,
  Fuel,
  Gem,
  Globe2,
  GraduationCap,
  Landmark,
  Layers3,
  LayoutDashboard,
  MessageCircle,
  Newspaper,
  Scale,
  ScanLine,
  Settings2,
  ShieldCheck,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";

export type Language = "fa" | "en";
export type Quality = "high" | "balanced" | "low";
export type NavItem = { id: string; fa: string; en: string; icon: LucideIcon };
export type NavGroup = { id: string; fa: string; en: string; items: NavItem[] };
export const navigation: NavGroup[] = [
  {
    id: "overview",
    fa: "فضای فرماندهی",
    en: "COMMAND",
    items: [
      {
        id: "command",
        fa: "مرکز فرماندهی",
        en: "Command Center",
        icon: LayoutDashboard,
      },
      { id: "digital", fa: "جهان دیجیتال", en: "Digital World", icon: Globe2 },
      { id: "earth", fa: "زمین و جهان", en: "Earth & Global", icon: Earth },
    ],
  },
  {
    id: "markets",
    fa: "هوشمندی بازار",
    en: "MARKET INTELLIGENCE",
    items: [
      {
        id: "prices",
        fa: "قیمت‌های بازار",
        en: "Market Prices",
        icon: ChartCandlestick,
      },
      {
        id: "opportunities",
        fa: "فرصت‌ها",
        en: "Opportunities",
        icon: Compass,
      },
      { id: "oil", fa: "بازار نفت", en: "Oil", icon: Fuel },
      { id: "gold", fa: "بازار طلا", en: "Gold", icon: Gem },
      { id: "us", fa: "سهام آمریکا", en: "US Equities", icon: Landmark },
      { id: "eu", fa: "سهام اروپا", en: "EU Equities", icon: BarChart3 },
      { id: "asia", fa: "سهام آسیا", en: "Asia Equities", icon: Globe2 },
      { id: "crypto", fa: "بازار رمزارز", en: "Crypto Market", icon: Coins },
      {
        id: "tokens",
        fa: "هوشمندی توکن",
        en: "Token Intelligence",
        icon: ScanLine,
      },
      { id: "news", fa: "اتاق خبر", en: "Newsroom", icon: Newspaper },
    ],
  },
  {
    id: "intelligence",
    fa: "پژوهش و هوش مصنوعی",
    en: "RESEARCH & INTELLIGENCE",
    items: [
      { id: "security", fa: "مرکز امنیت", en: "Security", icon: ShieldCheck },
      { id: "workshop", fa: "کارگاه فناوری", en: "Tech Workshop", icon: Atom },
      {
        id: "university",
        fa: "دانشگاه AHOS",
        en: "University",
        icon: GraduationCap,
      },
      { id: "research", fa: "مؤسسه پژوهش", en: "Research", icon: FlaskConical },
      {
        id: "kian",
        fa: "گفت‌وگو با کیان",
        en: "Kian Chat",
        icon: MessageCircle,
      },
      { id: "agents", fa: "مرکز عامل‌ها", en: "Agents", icon: Bot },
    ],
  },
  {
    id: "operations",
    fa: "عملیات و زیرساخت",
    en: "OPERATIONS",
    items: [
      {
        id: "paper",
        fa: "معاملات آزمایشی",
        en: "Paper Trading",
        icon: CircleDollarSign,
      },
      {
        id: "portfolio",
        fa: "سبد دارایی",
        en: "Portfolio",
        icon: BriefcaseBusiness,
      },
      {
        id: "memory",
        fa: "حافظه و یادگیری",
        en: "Memory & Learning",
        icon: BrainCircuit,
      },
      {
        id: "errors",
        fa: "خطاها و بازیابی",
        en: "Errors",
        icon: TriangleAlert,
      },
      { id: "reports", fa: "گزارش‌ها", en: "Reports", icon: FileChartColumn },
      { id: "system", fa: "سیستم و اجرا", en: "System", icon: Cpu },
      { id: "governance", fa: "حاکمیت", en: "Governance", icon: Scale },
      { id: "settings", fa: "تنظیمات", en: "Settings", icon: Settings2 },
    ],
  },
];
export const allItems = navigation.flatMap((group) => group.items);
export const stageModules = [
  {
    icon: Earth,
    fa: "زمین تعاملی",
    en: "Interactive Earth",
    sub: "GLOBAL INTELLIGENCE",
  },
  {
    icon: Activity,
    fa: "داده‌ها و بازارها",
    en: "Market intelligence",
    sub: "EVIDENCE FIRST",
  },
  {
    icon: Layers3,
    fa: "عامل‌های هوشمند",
    en: "Agent workspace",
    sub: "EXPLICIT STATE",
  },
  {
    icon: BookOpen,
    fa: "پژوهش و یادگیری",
    en: "Research & learning",
    sub: "KNOWLEDGE SYSTEM",
  },
];
export const workspaceIcon = Database;
