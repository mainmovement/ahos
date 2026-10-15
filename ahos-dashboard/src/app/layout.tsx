import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import { inter, vazirmatn } from "./fonts";
import { AppProviders } from "@/components/layout/providers";
import { AppShell, type ShellData } from "@/components/layout/app-shell";
import { COOKIE_KEY, DEFAULT_SETTINGS, parseCookieSettings } from "@/lib/settings/types";
import { getAgentActivity, getAgents } from "@/lib/api/agents";
import { getAlerts, getNotifications } from "@/lib/api/system";
import { getChatSeed } from "@/lib/api/chat";
import { getNavBadges } from "@/lib/api/dashboard";

export const metadata: Metadata = {
  title: { default: "AHOS · مرکز فرماندهی", template: "%s · AHOS" },
  description: "AHOS — Persian-first AI market-intelligence command center. Paper-only. Demo data.",
  applicationName: "AHOS",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#03060e",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const initial = parseCookieSettings(cookieStore.get(COOKIE_KEY)?.value);
  const s = { ...DEFAULT_SETTINGS, ...initial };

  const [notifications, agents, activity, alerts, seedFa, seedEn, badges] = await Promise.all([
    getNotifications(),
    getAgents(),
    getAgentActivity(),
    getAlerts(),
    getChatSeed("fa"),
    getChatSeed("en"),
    getNavBadges(),
  ]);

  const shell: ShellData = {
    badges: badges.data,
    notifications: notifications.data,
    assistant: {
      chatSeed: { fa: seedFa.data, en: seedEn.data },
      activity: activity.data,
      activityMeta: activity.meta,
      agentIndex: Object.fromEntries(agents.data.agents.map((a) => [a.id, { name: a.name, runtime: a.runtime, code: a.code }])),
      alerts: alerts.data,
      alertsMeta: alerts.meta,
    },
  };

  return (
    <html
      lang={s.locale}
      dir={s.locale === "fa" ? "rtl" : "ltr"}
      data-quality={s.quality}
      data-theme={s.theme}
      data-motion={s.motion}
      className={`${inter.variable} ${vazirmatn.variable}`}
      suppressHydrationWarning
    >
      <body>
        <AppProviders initialSettings={initial}>
          <AppShell data={shell}>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}
