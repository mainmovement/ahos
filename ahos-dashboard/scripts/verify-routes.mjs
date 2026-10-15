#!/usr/bin/env node
/**
 * Smoke-test every dashboard route against a running server.
 *   BASE_URL=http://localhost:3000 npm run verify:routes
 * Fails (exit 1) if any route is not HTTP 200 or is missing its marker text.
 */
const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const routes = [
  ["/", "مرکز فرماندهی"],
  ["/digital-world", "جهان دیجیتال"],
  ["/earth", "زمین و جهان"],
  ["/earth?focus=iran", "زمین و جهان"],
  ["/markets", "قیمت‌های بازار"],
  ["/markets?symbol=xau", "XAU/USD"],
  ["/opportunities", "تصمیم‌های کانونی"],
  ["/oil", "نفت"],
  ["/gold", "طلا"],
  ["/equities/us", "سهام آمریکا"],
  ["/equities/eu", "سهام اروپا"],
  ["/equities/asia", "سهام آسیا"],
  ["/crypto", "بازار رمزارز"],
  ["/tokens", "هوش توکن"],
  ["/news", "اتاق خبر"],
  ["/security", "مرکز امنیت"],
  ["/workshop", "کارگاه فناوری"],
  ["/university", "دانشگاه"],
  ["/research", "پژوهشکده"],
  ["/chat", "گفتگو با کیان"],
  ["/agents", "مرکز عامل‌ها"],
  ["/paper-trading", "PAPER_ONLY"],
  ["/portfolio", "سبد دارایی"],
  ["/memory", "حافظه و یادگیری"],
  ["/errors", "خطاها و بازیابی"],
  ["/reports", "گزارش‌ها"],
  ["/system", "سامانه و اجرا"],
  ["/governance", "حاکمیت"],
  ["/settings", "تنظیمات"],
];

let failed = 0;
for (const [path, marker] of routes) {
  const t0 = Date.now();
  try {
    const res = await fetch(BASE + path, { headers: { "user-agent": "ahos-verify" } });
    const html = await res.text();
    const ok = res.status === 200 && html.includes(marker) && html.includes('dir="rtl"');
    if (!ok) failed++;
    console.log(`${ok ? "✓" : "✗"} ${String(res.status).padEnd(3)} ${path.padEnd(22)} ${String(Date.now() - t0).padStart(4)}ms ${(html.length / 1024).toFixed(0)}KB${ok ? "" : `  (marker "${marker}" ${html.includes(marker) ? "found" : "MISSING"})`}`);
  } catch (err) {
    failed++;
    console.log(`✗ ERR ${path} ${err instanceof Error ? err.message : String(err)}`);
  }
}
const notFound = await fetch(BASE + "/equities/mars");
console.log(`${notFound.status === 404 ? "✓" : "✗"} ${notFound.status} /equities/mars (expected 404)`);
if (notFound.status !== 404) failed++;
console.log(failed ? `\n${failed} route(s) failed` : `\nAll ${routes.length + 1} checks passed`);
process.exit(failed ? 1 : 0);
