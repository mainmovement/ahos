"use client";

import { FlaskConical, X } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { useSettings } from "@/components/providers/settings-provider";
import { Button } from "@/components/ui/button";

/** One-time (dismissable) honesty banner shown at the top of Command Center. */
export function DatasetBanner() {
  const { dict } = useLocale();
  const { prefs, setPref, hydrated } = useSettings();
  if (!hydrated || prefs.datasetBannerDismissed) return null;

  return (
    <section
      aria-label={dict.common.datasetBannerTitle}
      className="mb-6 flex items-start gap-3 rounded-2xl border border-violet/40 bg-violet/[0.07] p-4"
    >
      <span className="mt-0.5 inline-flex size-8 shrink-0 items-center justify-center rounded-xl bg-violet/15 text-violet">
        <FlaskConical className="size-4" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-violet">{dict.common.datasetBannerTitle}</p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{dict.common.datasetBannerBody}</p>
      </div>
      <Button variant="ghost" size="sm" onClick={() => setPref("datasetBannerDismissed", true)}>
        <X aria-hidden />
        {dict.common.datasetBannerDismiss}
      </Button>
    </section>
  );
}
