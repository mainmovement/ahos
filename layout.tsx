import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Orbitron, Vazirmatn } from "next/font/google";
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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl" className={`${vazir.variable} ${orbitron.variable}`}>
      <body className="bg-[#040714] text-cyan-50 antialiased" style={{ fontFamily: "var(--font-vazir), Tahoma, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
