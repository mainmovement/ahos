import { tr } from "@/src/lib/i18n";
import type { Language } from "@/src/lib/navigation";

/** Small ownership line — no filesystem paths in the UI. */
export function AppLegalFooter({ language }: { language: Language }) {
  const locale = language === "fa" ? "fa" : "en";
  return (
    <p className="ah-legal-footer" dir={language === "fa" ? "rtl" : "ltr"}>
      <span>{tr(locale, "legal.footerLine1")}</span>
      <span className="ah-legal-footer__sep"> · </span>
      <span>{tr(locale, "legal.footerLine2")}</span>
    </p>
  );
}
