import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Cormorant_Garamond, IBM_Plex_Mono, Outfit } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const display = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-cormorant",
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
});

const sans = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-ibm",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "AHOS — Artificial Hybrid Opportunity Scoring",
  description:
    "Evidence-first crypto token discovery. Council scoring, risk gates, paper trading, and a self-improving intelligence tree.",
  icons: { icon: "/images/mark.png" },
  openGraph: {
    title: "AHOS — Find the fruit. Refuse the trap.",
    description: "Artificial Hybrid Opportunity Scoring System.",
    images: ["/images/og.jpg"],
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable} ${mono.variable} bg-[#05070b] text-[#efe6d6] antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
