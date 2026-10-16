import type { Metadata, Viewport } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'دیده‌بان · خبرنگاران — AHOS Newsroom',
  description:
    'میزِ اطلاعاتِ فقط‌خواندنیِ AHOS برای خبرهای نفت و طلا. فقط کاغذی؛ بدون هیچ کنترل معاملاتی.',
};

export const viewport: Viewport = {
  themeColor: '#080b10',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body className="m-0 h-screen overflow-hidden bg-ah-bg p-0 font-ah-fa text-ah-text">{children}</body>
    </html>
  );
}
