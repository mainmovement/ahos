import type { ReactNode } from "react";
import { AhosIcon, type AhosIconName } from "../icons";
import type { Language } from "../../lib/navigation";
import type { DataStatus, Provenance } from "../../lib/api/types";
import { getDemoProvenance } from "../../lib/api/dashboard";

import { tr } from "../../lib/i18n";

export function StatusChip({
  status = "DEMO",
  language = "en",
}: {
  status?: DataStatus;
  language?: Language;
}) {
  return (
    <span className={`dc-status dc-status-${status.toLowerCase()}`}>
      <AhosIcon name={`status/${status.toLowerCase()}` as AhosIconName} variant="color" size={12} />
      {language === "fa" && status !== "UNAVAILABLE" ? tr("fa", `status.${status}.label`) : status}
    </span>
  );
}
export function ProvenanceFooter({
  language,
  provenance = getDemoProvenance(),
}: {
  language: Language;
  provenance?: Provenance;
}) {
  return (
    <footer className="dc-provenance">
      <span title={provenance.source}>
        {provenance.source.replace("AHOS / ", "")}
      </span>
      <time dateTime={provenance.retrievedAt} title={provenance.retrievedAt}>
        {language === "fa" ? "دریافت" : "Retrieved"}{" "}
        <bdi>{provenance.retrievedAt.slice(11, 16)} UTC</bdi>
      </time>
      <StatusChip status={provenance.status} language={language} />
    </footer>
  );
}
export function DataCard({
  title,
  icon: Icon,
  language,
  children,
  action,
  className = "",
  provenance,
}: {
  title: string;
  icon?: AhosIconName;
  language: Language;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
  provenance?: Provenance;
}) {
  return (
    <section className={`dc-card ${className}`}>
      <header className="dc-card-header">
        <h2>
          {Icon && <AhosIcon name={Icon} size={18} />} {title}
        </h2>
        <div className="dc-card-actions">
          {action}
          <StatusChip status={provenance?.status} />
        </div>
      </header>
      <div className="dc-card-body">{children}</div>
      <ProvenanceFooter language={language} provenance={provenance} />
    </section>
  );
}
