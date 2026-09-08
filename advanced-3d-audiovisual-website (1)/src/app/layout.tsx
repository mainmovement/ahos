import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Space_Grotesk, Manrope, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AudioProvider } from "@/components/system/AudioProvider";
import { CustomCursor } from "@/components/system/CustomCursor";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AHOS — Artificial Hybrid Opportunity Scoring System",
  description:
    "AHOS is a crypto opportunity intelligence system — an AI council that discovers, verifies, scores and monitors emerging token opportunities before the crowd does.",
  keywords: ["AHOS", "crypto intelligence", "AI council", "opportunity scoring", "token discovery"],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${manrope.variable} ${jetbrains.variable}`}>
      <body className="bg-void text-slate-100 antialiased selection:bg-cyan-300">
        <AudioProvider>
          <div className="grain" aria-hidden="true" />
          <CustomCursor />
          {children}
        </AudioProvider>
      </body>
    </html>
  );
}
