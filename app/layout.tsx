import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Orbitron, Vazirmatn } from "next/font/google";
import { cookies } from "next/headers";
import Providers from "@/components/providers";

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
      style={{
        /* AHOS Theme Tokens */
        '--ahos-bg': '#0B0709',
        '--ahos-panel': '#160E12',
        '--ahos-border': '#3A2A1C',
        '--ahos-text': '#EFE4CC',
        '--ahos-text-muted': '#A99A80',
        '--ahos-gold': '#D4AF37',
        '--ahos-gold-hi': '#F1D58E',
        '--ahos-crimson': '#9E1C26',
        '--ahos-crimson-hi': '#D2343E',
        '--ahos-ember': '#E8834A',

        /* Tailwind CSS v4 Base Styles */
        '--tw-bg-opacity': 1,
        '--tw-text-opacity': 1,
        '--tw-shadow-color': 'rgba(0, 0, 0, 0.1)',
        '--tw-shadow': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        '--tw-shadow-colored': '0 1px 3px 0 var(--tw-shadow-color), 0 1px 2px -1px var(--tw-shadow-color)',
        '--tw-ring-offset-shadow': '0 0 #0000',
        '--tw-ring-shadow': '0 0 #0000',
        '--tw-ring-offset-color': '#fff',
        '--tw-ring-color': 'rgba(59, 130, 246, 0.5)',
        '--tw-ring-offset-width': '0px',
        '--tw-ring-inset': '',
        '--tw-blur': '',
        '--tw-drop-shadow': '',
        '--tw-filter': '',
        '--tw-backdrop-blur': '',
        '--tw-backdrop-filter': '',
        '--tw-grayscale': '',
        '--tw-hue-rotate': '',
        '--tw-invert': '',
        '--tw-saturate': '',
        '--tw-sepia': '',
        '--tw-contain': '',

        /* CSS Reset */
        'margin': 0,
        'padding': 0,
        'box-sizing': 'border-box',

        /* Base Styles */
        'min-height': '100vh',
        'scroll-behavior': 'smooth'
      } as React.HTMLAttributes<HTMLHtmlElement>['style']}
    >
      <body
        className="antialiased"
        style={{
          fontFamily: "var(--font-vazir), Tahoma, sans-serif",
          background: "var(--ahos-bg)",
          color: "var(--ahos-text)",
          margin: 0,
          padding: 0,
          boxSizing: 'border-box',
          minHeight: '100vh',
          position: 'relative'
        }}
      >
        <Providers activeThemeValue={activeTheme}>{children}</Providers>
      </body>
    </html>
  );
}
