import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-10 text-center">
      <div className="text-gold-gradient text-5xl font-bold" dir="ltr">
        404
      </div>
      <p className="text-sm text-fg-2">این صفحه وجود ندارد · Page not found</p>
      <Link href="/" className="rounded-[var(--radius-md)] border border-gold-400/30 px-3 py-1.5 text-xs text-gold-100 hover:bg-[var(--surface-hover)]">
        مرکز فرماندهی · Command Center
      </Link>
    </div>
  );
}
