import {
  Activity,
  LayoutGrid,
  Newspaper,
  Radar,
  Settings2,
  ShieldCheck,
  Table2,
} from "lucide-react";
import type { ComponentType } from "react";
import type { AppLocale } from "@/lib/i18n/config";

export type NavId =
  | "commandCenter"
  | "desks"
  | "positions"
  | "intelligence"
  | "readiness"
  | "health"
  | "settings";

export interface NavItem {
  id: NavId;
  path: string;
  icon: ComponentType<{ className?: string }>;
  group: "command" | "analysis" | "system";
}

export const NAV_ITEMS: NavItem[] = [
  { id: "commandCenter", path: "", icon: Radar, group: "command" },
  { id: "desks", path: "/desks", icon: LayoutGrid, group: "analysis" },
  { id: "positions", path: "/positions", icon: Table2, group: "analysis" },
  { id: "intelligence", path: "/intelligence", icon: Newspaper, group: "analysis" },
  { id: "readiness", path: "/readiness", icon: ShieldCheck, group: "system" },
  { id: "health", path: "/health", icon: Activity, group: "system" },
  { id: "settings", path: "/settings", icon: Settings2, group: "system" },
];

export const NAV_GROUPS: Array<NavItem["group"]> = ["command", "analysis", "system"];

export function navHref(locale: AppLocale, path: string): string {
  return `/${locale}${path}`;
}
