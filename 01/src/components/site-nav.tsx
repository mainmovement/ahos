"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FlaskConical, LayoutDashboard, Languages, Radar, TreePine, Users,
} from "lucide-react";
import { AhosMark } from "@/components/primitives";
import type { Locale } from "@/lib/dict";
import { cx } from "@/lib/ui";

type NavLabels = {
  dashboard: string;
  opportunities: string;
  council: string;
  wiseTree: string;
  paper: string;
  switchTo: string;
  brandName: string;
  brandTag: string;
  live: string;
};

export default function SiteNav({ locale, labels }: { locale: Locale; labels: NavLabels }) {
  const pathname = usePathname() || `/${locale}`;
  const other: Locale = locale === "fa" ? "en" : "fa";
  const switchHref = pathname.replace(/^\/(fa|en)/, `/${other}`);

  const links = [
    { href: `/${locale}`, label: labels.dashboard, icon: LayoutDashboard, exact: true },
    { href: `/${locale}/opportunities`, label: labels.opportunities, icon: Radar, exact: false },
    { href: `/${locale}/council`, label: labels.council, icon: Users, exact: false },
    { href: `/${locale}/wise-tree`, label: labels.wiseTree, icon: TreePine, exact: false },
    { href: `/${locale}/paper`, label: labels.paper, icon: FlaskConical, exact: false },
  ];

  const isActive = (href: string, exact: boolean) =>
    exact ? pathname === href : pathname.startsWith(href);

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-7xl px-3 sm:px-5">
        <div className="glass mt-3 flex h-14 items-center justify-between rounded-2xl px-3.5 shadow-[0_18px_50px_-30px_rgba(0,0,0,0.9)] sm:px-5">
          <Link href={`/${locale}`} className="group flex items-center gap-2.5">
            <AhosMark size={30} />
            <span className="leading-none">
              <span className="block text-[15px] font-black tracking-tight text-frost">
                {labels.brandName}
              </span>
              <span className="mt-1 block text-[9px] font-medium tracking-[0.22em] text-mist">
                {labels.brandTag}
              </span>
            </span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" aria-label="main">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={cx(
                  "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12.5px] font-medium transition-colors",
                  isActive(l.href, l.exact)
                    ? "bg-jade-400/12 text-jade-200 shadow-[inset_0_0_0_1px_rgba(52,211,153,0.28)]"
                    : "text-mist hover:bg-white/5 hover:text-frost",
                )}
              >
                <l.icon className="size-3.5" />
                {l.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <span className="hidden items-center gap-1.5 rounded-full border border-jade-400/25 bg-jade-400/8 px-2.5 py-1 text-[10px] font-bold tracking-wider text-jade-300 sm:flex">
              <span className="relative flex size-1.5">
                <span className="absolute size-full animate-ping rounded-full bg-jade-400 opacity-50" />
                <span className="relative size-1.5 rounded-full bg-jade-400" />
              </span>
              {labels.live}
            </span>
            <Link
              href={switchHref}
              className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-bold text-frost/90 transition hover:border-gild-400/40 hover:text-gild-300"
            >
              <Languages className="size-3.5" />
              {labels.switchTo}
            </Link>
          </div>
        </div>

        {/* mobile nav strip */}
        <nav
          aria-label="mobile"
          className="glass-soft mt-2 flex items-center gap-1 overflow-x-auto rounded-2xl px-2 py-1.5 lg:hidden"
        >
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cx(
                "flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 text-[11.5px] font-medium",
                isActive(l.href, l.exact)
                  ? "bg-jade-400/12 text-jade-200"
                  : "text-mist",
              )}
            >
              <l.icon className="size-3.5" />
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
