import { NextResponse, type NextRequest } from "next/server";
import { defaultLocale, locales } from "@/lib/i18n/config";

/**
 * Persian-first routing: every path without a locale prefix is redirected to
 * the Persian (default) variant. `/en/...` routes are the secondary locale.
 * Static assets (fonts, icons, manifest) bypass the redirect entirely.
 */
export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const firstSegment = pathname.split("/")[1] ?? "";
  if ((locales as readonly string[]).includes(firstSegment)) {
    return NextResponse.next();
  }

  // never touch static assets — they must 200 from the root
  if (
    pathname.startsWith("/fonts/") ||
    pathname.startsWith("/brand/") ||
    pathname.startsWith("/_next/") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const target = new URL(
    `/${defaultLocale}${pathname === "/" ? "" : pathname}`,
    req.url,
  );
  return NextResponse.redirect(target);
}

export const config = {
  matcher: ["/((?!_next/|api/).*)"],
};
