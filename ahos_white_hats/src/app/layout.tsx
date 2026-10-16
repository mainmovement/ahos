import type { Metadata, Viewport } from "next";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/vazirmatn/400.css";
import "@fontsource/vazirmatn/500.css";
import "@fontsource/vazirmatn/600.css";
import "@fontsource/vazirmatn/700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "کلاه‌سفیدها و ناظر · AHOS",
  description:
    "صفحه‌ی بازبینی مستقل تصمیم‌ها — فقط کاغذی، فقط خواندنی. AHOS White Hats & Judge — read-only, PAPER_ONLY.",
};

export const viewport: Viewport = {
  themeColor: "#080b10",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body className="min-h-dvh">{children}</body>
    </html>
  );
}
