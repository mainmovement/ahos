"use client";

import type { ReactNode } from "react";
import { ThemeProvider } from "next-themes";
import { SettingsProvider } from "./settings-provider";
import { LocaleProvider } from "./locale-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { Dictionary } from "@/lib/i18n";
import type { AppLocale } from "@/lib/i18n/config";

export function Providers({
  locale,
  dict,
  children,
}: {
  locale: AppLocale;
  dict: Dictionary;
  children: ReactNode;
}) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
      <SettingsProvider>
        <LocaleProvider value={{ locale, dict }}>
          <TooltipProvider delayDuration={250}>{children}</TooltipProvider>
        </LocaleProvider>
      </SettingsProvider>
    </ThemeProvider>
  );
}
