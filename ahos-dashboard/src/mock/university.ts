/** MOCK — AHOS University (agent training, exams, retraining queue). */
import type { UniversityOverview } from "@/lib/api/types";
import { L, minutesAgo } from "./_seed";

export function mockUniversity(now = Date.now()): UniversityOverview {
  return {
    students: [
      { agentId: "agent.research-analyst", name: L("تحلیلگر پژوهش", "Research Analyst"), program: L("روش‌شناسی شواهد", "Evidence methodology"), level: 2, progress: 0.72, state: "examining" },
      { agentId: "agent.discovery-scout", name: L("پیشاهنگ کشف", "Discovery Scout"), program: L("ضدهیاهو پیشرفته", "Advanced anti-hype"), level: 3, progress: 1, state: "passed" },
      { agentId: "agent.news-pipeline", name: L("خط لوله خبر", "News Pipeline"), program: L("تأیید چندمنبعی", "Cross-source verification"), level: 2, progress: 0.41, state: "retraining" },
      { agentId: "agent.paper-trader", name: L("معامله‌گر کاغذی", "Paper Trader"), program: L("مدیریت ریسک", "Risk management"), level: 2, progress: 0.88, state: "enrolled" },
      { agentId: "agent.telegram-edge", name: L("لبه تلگرام", "Telegram Edge"), program: L("ارتباط فارسی شفاف", "Clear Persian comms"), level: 1, progress: 0.2, state: "failed" },
    ],
    exams: [
      { id: "e1", title: L("آزمون کالیبراسیون اطمینان", "Confidence calibration exam"), agentId: "agent.research-analyst", agentName: L("تحلیلگر پژوهش", "Research Analyst"), score: 81, passMark: 75, result: "PASS", kind: "SELF_CHECK", at: minutesAgo(35, now) },
      { id: "e2", title: L("شناسایی هانی‌پات (۲۰۰ نمونه)", "Honeypot detection (200 cases)"), agentId: "agent.discovery-scout", agentName: L("پیشاهنگ کشف", "Discovery Scout"), score: 94, passMark: 90, result: "PASS", kind: "INDEPENDENT", at: minutesAgo(180, now) },
      { id: "e3", title: L("تشخیص خبر متناقض", "Conflicting-news detection"), agentId: "agent.news-pipeline", agentName: L("خط لوله خبر", "News Pipeline"), score: 63, passMark: 80, result: "FAIL", kind: "INDEPENDENT", at: minutesAgo(300, now) },
      { id: "e4", title: L("رعایت محدودیت‌های ریسک", "Risk-limit compliance"), agentId: "agent.paper-trader", agentName: L("معامله‌گر کاغذی", "Paper Trader"), score: null, passMark: 85, result: "PENDING", kind: "INDEPENDENT", at: minutesAgo(10, now) },
      { id: "e5", title: L("نگارش هشدار بدون FOMO", "FOMO-free alert writing"), agentId: "agent.telegram-edge", agentName: L("لبه تلگرام", "Telegram Edge"), score: 48, passMark: 70, result: "FAIL", kind: "SELF_CHECK", at: minutesAgo(1440, now) },
    ],
    retraining: [
      { agentId: "agent.news-pipeline", agentName: L("خط لوله خبر", "News Pipeline"), reason: L("نرخ خطای تشخیص تناقض بالاتر از آستانه", "Conflict-detection error above threshold"), priority: "HIGH", queuedAt: minutesAgo(290, now) },
      { agentId: "agent.telegram-edge", agentName: L("لبه تلگرام", "Telegram Edge"), reason: L("زبان فوریت‌آمیز در پیش‌نویس هشدار", "Urgency language in alert drafts"), priority: "MEDIUM", queuedAt: minutesAgo(1400, now) },
    ],
    programs: [
      { id: "p1", name: L("روش‌شناسی شواهد", "Evidence methodology"), enrolled: 3, passRate: 0.67 },
      { id: "p2", name: L("ضدهیاهو پیشرفته", "Advanced anti-hype"), enrolled: 2, passRate: 0.9 },
      { id: "p3", name: L("تأیید چندمنبعی", "Cross-source verification"), enrolled: 2, passRate: 0.5 },
      { id: "p4", name: L("مدیریت ریسک", "Risk management"), enrolled: 1, passRate: null },
    ],
    calibration: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map((b, i) => ({
      bucket: b,
      predicted: b,
      observed: i === 8 ? null : Math.max(0, Math.min(1, b + [0.04, 0.03, -0.02, -0.05, -0.04, -0.07, -0.09, -0.11, 0][i]!)),
    })),
    passRateTrend: [0.58, 0.61, 0.6, 0.64, 0.66, 0.63, 0.69, 0.71, 0.7, 0.74, 0.72, 0.76],
  };
}
