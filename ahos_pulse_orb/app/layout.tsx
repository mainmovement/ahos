import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AHOS Pulse Orb",
  description: "Calm technology orb",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body className="min-h-screen bg-black text-stone-100 antialiased">{children}</body>
    </html>
  );
}