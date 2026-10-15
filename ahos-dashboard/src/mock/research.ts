/** MOCK — research institute. */
import type { ResearchOverview } from "@/lib/api/types";
import { L, minutesAgo } from "./_seed";

export function mockResearch(now = Date.now()): ResearchOverview {
  return {
    missions: [
      { id: "M-041", title: L("الگوی شناسایی میم‌کوین‌های سولانا", "Solana memecoin pattern recognition"), leadAgentId: "agent.research-analyst", state: "ACTIVE", evidence: "PARTIAL", verification: "PENDING", verificationKind: null, acceptance: "NOT_REQUIRED", updatedAt: minutesAgo(12, now), tags: ["DeFi", "ML", "on-chain"] },
      { id: "M-042", title: L("فرصت‌های آربیتراژ بین‌زنجیره‌ای", "Cross-chain arbitrage structure"), leadAgentId: "agent.research-analyst", state: "VERIFICATION", evidence: "SUFFICIENT", verification: "PENDING", verificationKind: "INDEPENDENT", acceptance: "PENDING", updatedAt: minutesAgo(48, now), tags: ["arbitrage"] },
      { id: "M-039", title: L("کالیبراسیون اطمینان شورای ۱۰۰ نقش", "100-role council confidence calibration"), leadAgentId: "agent.org.05-epistemic-reasoning", state: "BLOCKED", evidence: "STALE", verification: "NOT_REQUESTED", verificationKind: null, acceptance: "NOT_REQUIRED", updatedAt: minutesAgo(60 * 26, now), tags: ["calibration"] },
      { id: "M-037", title: L("احساسات بازار از داده درون‌زنجیره", "Market sentiment from on-chain data"), leadAgentId: "agent.research-analyst", state: "COMPLETE", evidence: "SUFFICIENT", verification: "PASS", verificationKind: "SELF_CHECK", acceptance: "ACCEPTED", updatedAt: minutesAgo(60 * 12, now), tags: ["NLP", "on-chain"] },
      { id: "M-043", title: L("هم‌گرایی DeFi و هوش مصنوعی", "DeFi × AI convergence"), leadAgentId: "agent.research-analyst", state: "PLANNING", evidence: "NONE", verification: "NOT_REQUESTED", verificationKind: null, acceptance: "NOT_REQUIRED", updatedAt: minutesAgo(25, now), tags: ["AI", "DeFi"] },
      { id: "M-035", title: L("اثر حباب سکه بر تقاضای طلای داخلی", "Coin premium effect on domestic gold demand"), leadAgentId: "agent.org.11-risk-intelligence", state: "FAILED", evidence: "CONTRADICTED", verification: "FAIL", verificationKind: "INDEPENDENT", acceptance: "REJECTED", updatedAt: minutesAgo(60 * 50, now), tags: ["gold", "iran"] },
    ],
    hypotheses: [
      { id: "H-12", statement: L("هم‌زمانی رشد TVL و حجم توکن‌های AI پیش‌نشانگر روند است", "TVL growth co-moving with AI-token volume leads trend"), posture: "UNCERTAIN", support: 4, against: 2, missionId: "M-043" },
      { id: "H-09", statement: L("توکن‌های با تبلیغ پولی و دفتر کم‌عمق در ۷۲ ساعت ۶۰٪+ افت می‌کنند", "Paid-promo + thin-book tokens fall 60%+ within 72h"), posture: "KNOWN", support: 41, against: 3, missionId: "M-041" },
      { id: "H-14", statement: L("اختلاف قیمت پل‌ها پس از ۹۰ ثانیه بسته می‌شود", "Bridge price gaps close within 90 seconds"), posture: "CONTRADICTORY", support: 7, against: 6, missionId: "M-042" },
      { id: "H-15", statement: L("نرخ تأمین مالی منفی پیش از بازگشت قیمت رخ می‌دهد", "Negative funding precedes price reversals"), posture: "NOVEL", support: 1, against: 0, missionId: "M-041" },
      { id: "H-07", statement: L("حجم اجتماعی بدون شواهد زنجیره‌ای پیش‌بینی‌کننده نیست", "Social volume without on-chain evidence is not predictive"), posture: "KNOWN", support: 28, against: 2, missionId: "M-037" },
      { id: "H-16", statement: L("ریسک ژئوپلیتیک خلیج فارس بر اسپرد برنت-دبی اثر دارد", "Persian Gulf geopolitical risk moves the Brent–Dubai spread"), posture: "UNKNOWN", support: 0, against: 0, missionId: "M-039" },
    ],
    papers: [
      { id: "p1", title: "Market Microstructure of Automated Market Makers", venue: "arXiv", year: 2025, relevance: 0.92, state: "SUMMARIZED" },
      { id: "p2", title: "Detecting Pump-and-Dump Schemes on Solana", venue: "FC Workshop", year: 2025, relevance: 0.88, state: "READ" },
      { id: "p3", title: "Calibration of LLM Confidence in Financial QA", venue: "ACL Findings", year: 2025, relevance: 0.81, state: "QUEUED" },
      { id: "p4", title: "Cross-Chain MEV and Bridge Latency", venue: "arXiv", year: 2026, relevance: 0.77, state: "QUEUED" },
    ],
    experiments: [
      { id: "x1", title: L("بک‌تست فیلتر ضدهیاهو v3", "Anti-hype filter v3 backtest"), state: "DONE", metric: "precision", value: 0.84 },
      { id: "x2", title: L("آزمایش ترجمه خبر با سه مدل", "3-model news translation trial"), state: "RUNNING", metric: "BLEU", value: null },
      { id: "x3", title: L("شبیه‌سازی محدودیت ریسک کاغذی", "Paper risk-limit simulation"), state: "QUEUED", metric: "max DD", value: null },
      { id: "x4", title: L("خوشه‌بندی کیف پول‌های واش", "Wash-wallet clustering"), state: "FAILED", metric: "F1", value: 0.41 },
    ],
  };
}
