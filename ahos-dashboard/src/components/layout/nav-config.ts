import {
  Bitcoin,
  Bot,
  Brain,
  Building2,
  ChartCandlestick,
  Coins,
  Earth,
  FileText,
  Fingerprint,
  Flame,
  FlaskConical,
  Gem,
  GraduationCap,
  Landmark,
  LayoutDashboard,
  LifeBuoy,
  MessagesSquare,
  Network,
  Newspaper,
  ChartPie,
  Radar,
  ScrollText,
  Settings,
  ShieldCheck,
  Wallet,
  Wrench,
  Server,
  type LucideIcon,
} from "lucide-react";
import type { Dict } from "@/lib/i18n/fa";

export type NavItemKey = keyof Dict["nav"]["items"];
export type NavGroupKey = keyof Dict["nav"]["groups"];

export interface NavItem {
  key: NavItemKey;
  href: string;
  icon: LucideIcon;
}

export interface NavGroup {
  key: NavGroupKey;
  items: NavItem[];
}

/** Sidebar + command-palette navigation (single source). */
export const NAV: NavGroup[] = [
  {
    key: "command",
    items: [
      { key: "commandCenter", href: "/", icon: LayoutDashboard },
      { key: "digitalWorld", href: "/digital-world", icon: Network },
      { key: "earth", href: "/earth", icon: Earth },
    ],
  },
  {
    key: "markets",
    items: [
      { key: "markets", href: "/markets", icon: ChartCandlestick },
      { key: "opportunities", href: "/opportunities", icon: Radar },
      { key: "oil", href: "/oil", icon: Flame },
      { key: "gold", href: "/gold", icon: Gem },
      { key: "equitiesUs", href: "/equities/us", icon: Landmark },
      { key: "equitiesEu", href: "/equities/eu", icon: Building2 },
      { key: "equitiesAsia", href: "/equities/asia", icon: Coins },
      { key: "crypto", href: "/crypto", icon: Bitcoin },
      { key: "tokens", href: "/tokens", icon: Fingerprint },
    ],
  },
  {
    key: "intelligence",
    items: [
      { key: "news", href: "/news", icon: Newspaper },
      { key: "security", href: "/security", icon: ShieldCheck },
      { key: "workshop", href: "/workshop", icon: Wrench },
      { key: "university", href: "/university", icon: GraduationCap },
      { key: "research", href: "/research", icon: FlaskConical },
      { key: "chat", href: "/chat", icon: MessagesSquare },
      { key: "agents", href: "/agents", icon: Bot },
    ],
  },
  {
    key: "operations",
    items: [
      { key: "paperTrading", href: "/paper-trading", icon: Wallet },
      { key: "portfolio", href: "/portfolio", icon: ChartPie },
      { key: "memory", href: "/memory", icon: Brain },
      { key: "errors", href: "/errors", icon: LifeBuoy },
      { key: "reports", href: "/reports", icon: FileText },
    ],
  },
  {
    key: "system",
    items: [
      { key: "system", href: "/system", icon: Server },
      { key: "governance", href: "/governance", icon: ScrollText },
      { key: "settings", href: "/settings", icon: Settings },
    ],
  },
];

export const ALL_NAV_ITEMS: NavItem[] = NAV.flatMap((g) => g.items);

export function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

