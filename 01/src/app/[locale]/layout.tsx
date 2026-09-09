import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Vazirmatn, Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import Atmosphere from "@/components/atmosphere";
import SiteNav from "@/components/site-nav";
import { AhosMark } from "@/components/primitives";
import { getDict, isLocale, locales, type Locale } from "@/lib/dict";
import "../globals.css";

const vazir = Vazirmatn({
  subsets: ["arabic", "latin"],
  variable: "--font-vazir",
  display: "swap",
});
const grotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-grotesk",
  display: "swap",
});
const plex = IBM_Plex_Mono({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-plex",
  display: "swap",
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDict(locale);
  return {
    title: dict.meta.title,
    description: dict.meta.description,
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const dict = getDict(locale);
  const loc: Locale = locale;

  return (
    <html
      lang={locale}
      dir={dict.dir}
      className={`${vazir.variable} ${grotesk.variable} ${plex.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-dvh bg-abyss-975 font-sans text-frost antialiased">
        <Atmosphere locale={loc} strings={dict.atmosphere} />
        <SiteNav
          locale={loc}
          labels={{
            dashboard: dict.nav.dashboard,
            opportunities: dict.nav.opportunities,
            council: dict.nav.council,
            wiseTree: dict.nav.wiseTree,
            paper: dict.nav.paper,
            switchTo: dict.nav.switchTo,
            brandName: dict.brand.name,
            brandTag: dict.brand.tag,
            live: dict.hero.live,
          }}
        />
        <main className="relative z-10 pt-[108px] lg:pt-[84px]">{children}</main>

        <footer className="relative z-10 mt-28 border-t border-white/5">
          <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 md:grid-cols-3">
            <div>
              <div className="flex items-center gap-2.5">
                <AhosMark size={34} />
                <div className="leading-none">
                  <div className="text-base font-black text-frost">{dict.brand.name}</div>
                  <div className="mt-1 text-[9px] tracking-[0.24em] text-mist">{dict.brand.tag}</div>
                </div>
              </div>
              <p className="mt-4 max-w-xs text-[12px] leading-6 text-mist">{dict.footer.line}</p>
            </div>
            <div className="flex flex-col gap-3">
              <span className="w-fit rounded-full border border-jade-400/25 bg-jade-400/8 px-3 py-1 text-[11px] font-semibold text-jade-300">
                {dict.footer.phase}
              </span>
              <nav className="flex flex-wrap gap-x-5 gap-y-2 text-[12px] text-mist">
                <Link className="transition hover:text-frost" href={`/${locale}/opportunities`}>{dict.nav.opportunities}</Link>
                <Link className="transition hover:text-frost" href={`/${locale}/council`}>{dict.nav.council}</Link>
                <Link className="transition hover:text-frost" href={`/${locale}/wise-tree`}>{dict.nav.wiseTree}</Link>
                <Link className="transition hover:text-frost" href={`/${locale}/paper`}>{dict.nav.paper}</Link>
              </nav>
              <span className="num text-[10px] tracking-wider text-mist/70">
                POLICY v1.4.2 · CANONICAL READ MODEL · LANE B
              </span>
            </div>
            <div className="md:text-end">
              <p className="text-[12px] leading-6 text-mist">{dict.footer.rights}</p>
              <p className="mt-4 text-[13px] font-semibold text-gild-300/90">{dict.footer.quote}</p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
