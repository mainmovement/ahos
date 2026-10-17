import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Orbitron, Vazirmatn } from "next/font/google";
import { cookies } from "next/headers";
import Providers from "@/components/providers";
import "./globals.css";

const vazir = Vazirmatn({
  subsets: ["arabic", "latin"],
  variable: "--font-vazir",
  display: "swap",
});

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AHOS — مرکز فرماندهی هوشمند",
  description:
    "Artificial Hybrid Opportunity Scoring System — evidence-first crypto intelligence command center. Paper-only.",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const activeTheme = cookieStore.get("active_theme")?.value ?? "ahos";
  return (
    <html
      lang="fa"
      dir="rtl"
      data-theme="ahos"
      suppressHydrationWarning
      className={`${vazir.variable} ${orbitron.variable}`}
    >
      <body className="antialiased bg-ahos-bg text-ahos-text min-h-screen">
        <Providers activeThemeValue={activeTheme}>{children}</Providers>
      </body>
    </html>
  );
}
