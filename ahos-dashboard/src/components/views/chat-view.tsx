"use client";

import { BookOpen, MessagesSquare, ShieldQuestion } from "lucide-react";
import type { AlertItem, ChatMessage, DataEnvelope } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { AlertsList } from "@/components/cards/alerts-list";
import { KianPanel } from "@/components/chat/kian-panel";

export function ChatView({ seed, alerts }: { seed: Record<"fa" | "en", ChatMessage[]>; alerts: DataEnvelope<AlertItem[]> }) {
  const { t, tx } = useI18n();
  const capabilities = [
    tx("قیمت‌ها با منبع و وضعیت داده", "Prices with source and data status"),
    tx("تصمیم‌های مرجع کانونی (فقط نمایش)", "Canonical decisions (presentation only)"),
    tx("ریسک و محدودیت‌های حساب کاغذی", "Paper-account risk and limits"),
    tx("امنیت توکن و دامنه‌های فیشینگ", "Token security and phishing domains"),
    tx("اخبار تأییدشده و متناقض", "Verified and conflicting news"),
    tx("وضعیت عامل‌ها و سامانه", "Agent and system status"),
  ];
  return (
    <PageBody>
      <PageHeader title={t.nav.items.chat} subtitle={t.kian.subtitle} icon={MessagesSquare} />
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <div className="glass gold-border flex h-[min(76vh,760px)] min-h-[520px] flex-col @4xl:col-span-8">
          <KianPanel seed={seed} variant="full" className="h-full" />
        </div>
        <div className="flex flex-col gap-3 @4xl:col-span-4">
          <DataCard title={tx("کیان چه می‌داند", "What Kian can answer")} icon={BookOpen}>
            <ul className="space-y-1.5 text-2xs text-fg-2">
              {capabilities.map((c) => (
                <li key={c} className="flex items-start gap-1.5">
                  <span aria-hidden className="mt-1.5 size-1 rounded-full bg-gold-400" />
                  {c}
                </li>
              ))}
            </ul>
            <div className="mt-3 flex items-start gap-1.5 rounded-[var(--radius-md)] border border-violet/30 bg-violet/[0.06] p-2.5 text-3xs leading-relaxed text-fg-2">
              <ShieldQuestion aria-hidden className="mt-0.5 size-3.5 shrink-0 text-violet" />
              {tx("وقتی شواهدی نیست، کیان «نامعلوم» پاسخ می‌دهد و حدس نمی‌زند. توصیه خرید/فروش و اجرای معامله واقعی خارج از اختیار اوست.", "When there is no evidence, Kian answers UNKNOWN instead of guessing. Buy/sell advice and real trade execution are outside its authority.")}
            </div>
          </DataCard>
          <DataCard title={t.rail.alerts} icon={ShieldQuestion} meta={alerts.meta}>
            <AlertsList alerts={alerts.data} />
          </DataCard>
        </div>
      </div>
    </PageBody>
  );
}
