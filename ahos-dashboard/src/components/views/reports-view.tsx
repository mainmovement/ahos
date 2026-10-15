"use client";

import { useState } from "react";
import { CalendarClock, CircleCheck, CircleX, Download, Eye, FileText, Loader } from "lucide-react";
import type { DataEnvelope, ReportItem } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { CardFooter } from "@/components/cards/data-card";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { TimeAgo } from "@/components/ui/primitives";
import { StatusChip } from "@/components/ui/status";
import { Tip } from "@/components/ui/tooltip";

export function ReportsView({ reports }: { reports: DataEnvelope<ReportItem[]> }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const [preview, setPreview] = useState<ReportItem | null>(null);
  const kind = { daily: tx("روزانه", "Daily"), weekly: tx("هفتگی", "Weekly"), audit: tx("ممیزی", "Audit"), research: tx("پژوهشی", "Research"), incident: tx("حادثه", "Incident") } as const;
  const state = {
    READY: { label: tx("آماده", "Ready"), tone: "up", icon: CircleCheck },
    GENERATING: { label: tx("در حال تولید", "Generating"), tone: "gold", icon: Loader },
    FAILED: { label: tx("ناموفق", "Failed"), tone: "down", icon: CircleX },
    SCHEDULED: { label: tx("زمان‌بندی‌شده", "Scheduled"), tone: "info", icon: CalendarClock },
  } as const;
  return (
    <PageBody>
      <PageHeader title={t.nav.items.reports} subtitle={tx("گزارش‌های روزانه، هفتگی، ممیزی، پژوهشی و حادثه", "Daily, weekly, audit, research and incident reports")} icon={FileText} />
      <section className="grid grid-cols-1 gap-3 @2xl:grid-cols-2 @6xl:grid-cols-3">
        {reports.data.map((r) => {
          const s = state[r.state];
          return (
            <article key={r.id} className="glass gold-border card-sheen flex flex-col">
              <div className="flex flex-1 flex-col gap-2 p-3.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Chip tone={s.tone} icon={s.icon}>{s.label}</Chip>
                  <Chip tone="muted">{kind[r.kind]}</Chip>
                  <span className="ms-auto"><StatusChip status="DEMO" /></span>
                </div>
                <h2 className="text-sm font-semibold text-fg-1">{l(r.title)}</h2>
                <p className="text-2xs leading-relaxed text-fg-3">{l(r.summary)}</p>
                <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 text-3xs text-fg-4">
                  <span>{tx("نویسنده", "Author")}: <bdi className="mono text-fg-3">{r.author.replace("agent.", "")}</bdi></span>
                  {r.pages !== null && <span>{f.num(r.pages, 0)} {tx("صفحه", "pages")}</span>}
                  {r.generatedAt && <TimeAgo iso={r.generatedAt} />}
                </div>
                <div className="flex gap-2 pt-1">
                  <Button size="sm" variant="outline" disabled={r.state !== "READY"} onClick={() => setPreview(r)}>
                    <Eye aria-hidden />
                    {tx("پیش‌نمایش", "Preview")}
                  </Button>
                  <Tip content={t.common.disabledInDemo}>
                    <span tabIndex={0}>
                      <Button size="sm" variant="ghost" disabled aria-disabled>
                        <Download aria-hidden />
                        PDF
                      </Button>
                    </span>
                  </Tip>
                </div>
              </div>
            </article>
          );
        })}
      </section>
      <div className="glass gold-border">
        <CardFooter meta={reports.meta} />
      </div>
      <Dialog open={!!preview} onOpenChange={(o) => !o && setPreview(null)}>
        {preview && (
          <DialogContent className="w-[min(720px,94vw)] p-0">
            <div className="border-b border-[var(--line-hairline)] p-4 pe-12">
              <DialogTitle className="text-base font-bold text-fg-1">{l(preview.title)}</DialogTitle>
              <DialogDescription className="mt-0.5 text-2xs text-fg-4">{tx("پیش‌نمایش نمایشی — محتوای واقعی از مولد گزارش می‌آید", "Demo preview — real content comes from the report generator")}</DialogDescription>
            </div>
            <div className="max-h-[60vh] space-y-3 overflow-y-auto p-5 text-2xs leading-loose text-fg-2">
              <p className="text-fg-1">{l(preview.summary)}</p>
              <div className="rounded-[var(--radius-md)] border border-dashed border-status-demo/40 bg-status-demo/[0.05] p-3 text-3xs text-status-demo">
                {tx("این متن جایگزین است. هیچ عدد یا ادعای جدیدی در پیش‌نمایش ساخته نمی‌شود.", "This is placeholder text. No new numbers or claims are fabricated in the preview.")}
              </div>
              <ol className="list-decimal space-y-1 ps-5">
                <li>{tx("خلاصه اجرایی", "Executive summary")}</li>
                <li>{tx("بازارها و شواهد", "Markets and evidence")}</li>
                <li>{tx("امنیت و ریسک", "Security and risk")}</li>
                <li>{tx("عامل‌ها و سامانه", "Agents and system")}</li>
                <li>{tx("ناشناخته‌ها و محدودیت‌ها", "Unknowns and limitations")}</li>
              </ol>
            </div>
          </DialogContent>
        )}
      </Dialog>
    </PageBody>
  );
}
