import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import type { Language } from "../../lib/navigation";
import type { DataStatus, Provenance } from "../../lib/api/types";
import { getDemoProvenance } from "../../lib/api/dashboard";

export function StatusChip({ status = "DEMO" }: { status?: DataStatus }) {
  return (
    <span className={`dc-status dc-status-${status.toLowerCase()}`}>
      {status}
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
      <StatusChip status={provenance.status} />
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
  icon?: LucideIcon;
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
          {Icon && <Icon size={16} strokeWidth={1.6} />} {title}
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
