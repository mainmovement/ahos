"use client";

import { useEffect } from "react";

export default function ErrorBoundary({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <div role="alert" className="flex h-full flex-col items-center justify-center gap-3 p-10 text-center">
      <div className="text-lg font-semibold text-fg-1">خطا در نمایش این صفحه · Something went wrong</div>
      <p className="max-w-md text-xs text-fg-3">
        خطا ثبت شد. داده‌ای جعل نمی‌شود؛ می‌توانید دوباره تلاش کنید. · The error was logged; nothing is fabricated. You can retry.
      </p>
      <button type="button" onClick={reset} className="rounded-[var(--radius-md)] border border-gold-400/30 px-3 py-1.5 text-xs text-gold-100 hover:bg-[var(--surface-hover)]">
        تلاش دوباره · Retry
      </button>
    </div>
  );
}
