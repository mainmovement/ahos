import type { Metadata, Viewport } from "next";
import { notFound } from "next/navigation";
import { dirFor, isLocale, locales } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { Providers } from "@/components/providers/providers";
import { AppShell } from "@/components/layout/app-shell";
import "@/app/globals.css";

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return {
    title: {
      default: `${dict.common.appName} — ${dict.common.taglineEn}`,
      template: `%s · AHOS`,
    },
    description: dict.command.description,
    applicationName: dict.common.appName,
    robots: { index: false, follow: false },
  };
}

export const viewport: Viewport = {
  themeColor: "#0B1020",
  width: "device-width",
  initialScale: 1,
};

/** Applies stored density/motion prefs before first paint (no flash). */
const EARLY_PREFS_SCRIPT = `(function(){try{var p=JSON.parse(localStorage.getItem("ahos-deck-prefs.v1")||"{}");var d=document.documentElement;if(p.density)d.dataset.density=p.density;if(p.motion)d.dataset.motion=p.motion==="reduce"?"reduce":"full";}catch(e){}})();`;

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale = rawLocale;
  const dict = getDictionary(locale);
  const dir = dirFor(locale);

  return (
    <html lang={locale} dir={dir} className="dark" suppressHydrationWarning>
      <head>
        <link
          rel="preload"
          href="/fonts/vazirmatn-arabic-400-normal.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/vazirmatn-arabic-700-normal.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <link
          rel="preload"
          href="/fonts/inter-latin-wght-normal.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <script dangerouslySetInnerHTML={{ __html: EARLY_PREFS_SCRIPT }} />
      </head>
      <body className="min-h-dvh font-sans antialiased">
        <Providers locale={locale} dict={dict}>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
