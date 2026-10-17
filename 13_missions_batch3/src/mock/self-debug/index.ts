// FILE: 13_missions_batch3/src/mock/self-debug/index.ts
/**
 * DEMO fixture for «خطایابی خودکار». Adapter-only — components must never
 * import this module. Signatures/log lines are redacted; no secrets, no paths
 * containing usernames.
 */
import type { SelfDebugSnapshot } from "@/contract/types";

export const selfDebugDemo: SelfDebugSnapshot = {
  kind: "selfDebug",
  executionMode: "PAPER_ONLY",
  realTrading: false,
  source: "DEMO_FIXTURE",
  generatedAt: "2026-10-16T12:00:00+03:30",
  demo: true,
  incidents: [
    {
      id: "sd-01",
      time: "2026-10-16T06:12:00+03:30",
      component: "collector",
      errorSignature: "parse-error: unexpected token in payload <redacted>",
      diagnosisNote: "ساختار ورودی با قرارداد مغایرت دارد",
      status: "DIAGNOSED",
      evidencePath: "evidence/sd-01/trace.txt",
      timeline: [
        { time: "2026-10-16T06:12:00+03:30", event: "ثبت خطا", source: "collector-log" },
        { time: "2026-10-16T06:20:00+03:30", event: "بررسی اولیه", source: "agent-note" },
      ],
      logExcerpt: ["level=error component=collector code=parse payload=<<redacted>>"],
      demo: true,
    },
    {
      id: "sd-02",
      time: "2026-10-15T23:48:00+03:30",
      component: "scheduler",
      errorSignature: "timeout: job exceeded limit <redacted>",
      diagnosisNote: null,
      status: "OPEN",
      evidencePath: null,
      timeline: [{ time: "2026-10-15T23:48:00+03:30", event: "ثبت خطا", source: "scheduler-log" }],
      logExcerpt: ["level=error component=scheduler code=timeout job=<<redacted>>"],
      demo: true,
    },
    {
      id: "sd-03",
      time: null,
      component: "adapter",
      errorSignature: "contract mismatch: field missing <redacted>",
      diagnosisNote: "زمان رخداد نامشخص است",
      status: "UNKNOWN",
      evidencePath: null,
      timeline: [],
      logExcerpt: [],
      demo: true,
    },
    {
      id: "sd-04",
      time: "2026-10-14T17:05:00+03:30",
      component: "notifier",
      errorSignature: "rate-limit: too many messages <redacted>",
      diagnosisNote: "نرخ ارسال محدود شد",
      status: "CLOSED",
      evidencePath: "evidence/sd-04/report.md",
      timeline: [
        { time: "2026-10-14T17:05:00+03:30", event: "ثبت خطا", source: "notifier-log" },
        { time: "2026-10-14T19:00:00+03:30", event: "بسته‌شدن پرونده", source: "agent-note" },
      ],
      logExcerpt: ["level=warn component=notifier code=rate-limit count=<<redacted>>"],
      demo: true,
    },
    {
      id: "sd-05",
      time: "2026-10-13T09:30:00+03:30",
      component: "collector",
      errorSignature: "null reference in merge step <redacted>",
      diagnosisNote: "ورودی خالی در گام ادغام",
      status: "OPEN",
      evidencePath: "evidence/sd-05/core.txt",
      timeline: [{ time: "2026-10-13T09:30:00+03:30", event: "ثبت خطا", source: "collector-log" }],
      logExcerpt: ["level=error component=collector code=null-ref step=merge ref=<<redacted>>"],
      demo: true,
    },
  ],
};
