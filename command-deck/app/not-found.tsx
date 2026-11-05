import Link from "next/link";

export default function NotFound() {
  return (
    <html lang="fa" dir="rtl">
      <body className="flex min-h-dvh items-center justify-center bg-[#0B1020] p-6 font-sans text-slate-200">
        <div className="max-w-md text-center">
          <p className="text-6xl font-extrabold text-[#D4AF37]" dir="ltr">
            404
          </p>
          <p className="mt-4 text-lg font-bold">صفحه پیدا نشد</p>
          <p className="mt-2 text-sm text-slate-400">آدرس واردشده در این عرشه وجود ندارد.</p>
          <Link
            href="/fa"
            className="mt-6 inline-flex rounded-xl border border-[#D4AF37]/40 bg-[#D4AF37]/10 px-4 py-2 text-sm font-bold text-[#D4AF37]"
          >
            بازگشت به مرکز فرماندهی
          </Link>
        </div>
      </body>
    </html>
  );
}
