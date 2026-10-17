// FILE: 13_missions_batch3/src/app/layout.tsx
import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "AHOS — مأموریت‌های دسته ۳",
  description: "صفحات کاغذی/نمایشی AHOS: رادار علم، خطایابی، آزمون هفتگی، بازار مهارت، مرکز اخبار",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body className="ah-body">{children}</body>
    </html>
  );
}
