/**
 * MOCK — agent roster.
 *
 * Roster mirrors the AHOS repo: the 19 provisional roles from
 * `docs/agents/PLANNED_19_AGENT_MAP.md` (STATUS = PLANNED, maturity 0) plus
 * the components that actually exist in code. Runtime states and events are
 * DEMO values. A decorated avatar never implies a running task — the UI
 * always renders the explicit runtime chip.
 */
import type { Agent, AgentEvent, AgentsOverview, DepartmentId, ImplementationStatus, Localized } from "@/lib/api/types";
import { L, minutesAgo } from "./_seed";

const DEPARTMENTS: AgentsOverview["departments"] = [
  { id: "architecture", name: L("معماری", "Architecture") },
  { id: "governance", name: L("حاکمیت", "Governance") },
  { id: "research", name: L("پژوهش", "Research") },
  { id: "markets", name: L("بازار و داده", "Markets & data") },
  { id: "security", name: L("امنیت", "Security") },
  { id: "quant", name: L("ریسک و کمّی", "Risk & quant") },
  { id: "runtime", name: L("زمان اجرا", "Runtime") },
  { id: "product", name: L("محصول و تجربه", "Product & UX") },
  { id: "verification", name: L("راستی‌آزمایی", "Verification") },
];

interface PlannedSpec {
  n: number;
  slug: string;
  name: Localized;
  role: Localized;
  dept: DepartmentId;
  impl: ImplementationStatus;
  doc: string | null;
}

const PLANNED: PlannedSpec[] = [
  { n: 1, slug: "chief-architect", name: L("معمار ارشد", "Chief Architect"), role: L("رهبری معماری سازمان و سامانه (مستند)", "Organizational / system architecture leadership"), dept: "architecture", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_01_ORGANIZATIONAL_FEDERATION_ARCHITECTURE.md" },
  { n: 2, slug: "systems-architect", name: L("معمار سامانه‌ها", "Systems Architect"), role: L("ساختار سامانه‌ها و رابط‌ها", "Systems structure and interfaces"), dept: "architecture", impl: "PLANNED", doc: null },
  { n: 3, slug: "security-architect", name: L("معمار امنیت", "Security Architect"), role: L("بازبینی معماری امنیت (نه سندباکس)", "Security architecture review (not a sandbox)"), dept: "security", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md" },
  { n: 4, slug: "governance-constitution", name: L("حاکمیت و قانون اساسی", "Governance & Constitution"), role: L("سازگاری متون حاکمیتی و پروتکل‌ها", "Governance text and protocol consistency"), dept: "governance", impl: "DOCUMENTED_ONLY", doc: "docs/governance/AGENT_04_GOVERNANCE_AND_CONSTITUTION_ARCHITECTURE.md" },
  { n: 5, slug: "epistemic-reasoning", name: L("استدلال معرفتی", "Epistemic Reasoning"), role: L("انضباط شواهد، ادعا و فرضیه", "Evidence/claim/hypothesis discipline"), dept: "research", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md" },
  { n: 6, slug: "research-methodology", name: L("روش‌شناسی پژوهش", "Research Methodology"), role: L("طراحی روش و مطالعه", "Method and study design"), dept: "research", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md" },
  { n: 7, slug: "data-intelligence", name: L("هوش داده", "Data Intelligence"), role: L("کیفیت داده و استدلال طرح‌واره", "Data quality and schema reasoning"), dept: "markets", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 8, slug: "crypto-market-intelligence", name: L("هوش بازار رمزارز", "Crypto Market Intelligence"), role: L("پژوهش ساختار بازار (بدون معامله زنده)", "Market structure research (no live trade)"), dept: "markets", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 9, slug: "on-chain-intelligence", name: L("هوش زنجیره‌ای", "On-Chain Intelligence"), role: L("پژوهش درون‌زنجیره‌ای (بدون اتصال تولیدی)", "On-chain research (no production connectors)"), dept: "markets", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 10, slug: "token-security-scam-intelligence", name: L("امنیت توکن و ضدکلاهبرداری", "Token Security / Scam Intelligence"), role: L("تحلیل توکن و کلاهبرداری (بدون اعتبارنامه)", "Token/scam analysis (no credential use)"), dept: "security", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 11, slug: "risk-intelligence", name: L("هوش ریسک", "Risk Intelligence"), role: L("شناسایی و قاب‌بندی ریسک", "Risk identification and framing"), dept: "quant", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 12, slug: "quant-backtesting", name: L("کمّی و بک‌تست", "Quant / Backtesting"), role: L("طراحی پژوهش کمّی (بدون امتیازدهی پنهان)", "Quant research design (no silent prod scoring)"), dept: "quant", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_12_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 13, slug: "ai-ml-intelligence", name: L("هوش مصنوعی و یادگیری ماشین", "AI / ML Intelligence"), role: L("پژوهش مدل و ارزیابی (بدون ادعای آموزش)", "Model/eval research (no training runtime claimed)"), dept: "quant", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_13_AI_ML_INTELLIGENCE_ARCHITECTURE.md" },
  { n: 14, slug: "agent-runtime-engineering", name: L("مهندسی زمان اجرای عامل", "Agent Runtime Engineering"), role: L("مهندسی زمان اجرای سازمان", "Org runtime engineering"), dept: "runtime", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_14_AGENT_RUNTIME_ARCHITECTURE.md" },
  { n: 15, slug: "prompt-instruction-engineering", name: L("مهندسی دستور و منشور", "Prompt & Instruction Engineering"), role: L("مهندسی دستورالعمل و منشور", "Instruction/charter engineering"), dept: "governance", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_15_PROMPT_INSTRUCTION_DELEGATION_ARCHITECTURE.md" },
  { n: 16, slug: "qa-verification", name: L("تضمین کیفیت و راستی‌آزمایی", "QA / Verification"), role: L("طراحی راستی‌آزمایی مستقل", "Independent verification design"), dept: "verification", impl: "DOCUMENTED_ONLY", doc: "docs/verification/AGENT_16_INDEPENDENT_VERIFICATION_AND_ORGANIZATIONAL_FORENSICS.md" },
  { n: 17, slug: "product-ux-intelligence", name: L("هوش محصول و تجربه کاربری", "Product / UX Intelligence"), role: L("پژوهش محصول و تجربه کاربری", "Product/UX research"), dept: "product", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_17_HUMAN_AGENT_ORGANIZATION_UX_AND_PRODUCT_ARCHITECTURE.md" },
  { n: 18, slug: "frontend-visualization", name: L("رابط کاربری و بصری‌سازی", "Frontend / Visualization"), role: L("طراحی رابط و بصری‌سازی", "Frontend/visualization design"), dept: "product", impl: "DOCUMENTED_ONLY", doc: "docs/architecture/AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE.md" },
  { n: 19, slug: "independent-red-team", name: L("تیم قرمز مستقل", "Independent Red Team"), role: L("بازبینی تقابلی ادعاهای سازمان", "Adversarial review of org claims"), dept: "security", impl: "DOCUMENTED_ONLY", doc: "docs/security/AGENT_19_RED_TEAM_AND_ADVERSARIAL_ORGANIZATIONAL_SECURITY_ARCHITECTURE.md" },
];

function ev(agentId: string, minAgo: number, kind: AgentEvent["kind"], text: Localized, now: number, i = 0): AgentEvent {
  return { id: `${agentId}:${i}:${minAgo}`, agentId, at: minutesAgo(minAgo, now), kind, text };
}

export function mockAgents(now = Date.now()): AgentsOverview {
  const planned: Agent[] = PLANNED.map((p) => {
    const id = `agent.org.${String(p.n).padStart(2, "0")}-${p.slug}`;
    return {
      id,
      code: `A-${String(p.n).padStart(2, "0")}`,
      name: p.name,
      role: p.role,
      department: p.dept,
      implementation: p.impl,
      runtime: "planned",
      maturity: 0,
      currentTask: null,
      lastActivityAt: null,
      capabilities: [],
      limitations: [L("عملیاتی نیست — فقط نقشه نقش", "Not operational — role blueprint only"), L("هیچ قابلیتی اعطا نشده", "No capability granted")],
      verification: { status: "UNVERIFIED", kind: null },
      metrics: { tasks24h: null, successRate: null, avgLatencyMs: null },
      events: [ev(id, 60 * 24 * 9, "registered", L("در نقشه ۱۹ عامل ثبت شد (PLANNED)", "Listed in the 19-agent map (PLANNED)"), now)],
      sourceDoc: p.doc,
    };
  });

  const operational: Agent[] = [
    {
      id: "agent.research-analyst",
      code: "R-01",
      name: L("تحلیلگر پژوهش", "Research Analyst"),
      role: L("تحلیل فرضیه در کارگر پژوهشی ایزوله", "Hypothesis analysis in a process-isolated worker"),
      department: "research",
      implementation: "PARTIAL",
      runtime: "running",
      maturity: 1,
      currentTask: L("بررسی فرضیه H-12: هم‌گرایی DeFi و هوش مصنوعی", "Reviewing hypothesis H-12: DeFi × AI convergence"),
      lastActivityAt: minutesAgo(1, now),
      capabilities: [L("خواندن شواهد ثبت‌شده", "Read registered evidence"), L("پیشنهاد ادعا (نیازمند تأیید)", "Propose claims (requires approval)")],
      limitations: [L("بدون دسترسی شبکه", "No network access"), L("خروجی = ادعا، نه واقعیت", "Output = claim, not fact")],
      verification: { status: "PASS", kind: "SELF_CHECK" },
      metrics: { tasks24h: 38, successRate: 0.89, avgLatencyMs: 4200 },
      events: [],
      sourceDoc: "docs/architecture/RESEARCH_ANALYST_AGENT.md",
    },
    {
      id: "agent.discovery-scout",
      code: "D-01",
      name: L("پیشاهنگ کشف", "Discovery Scout"),
      role: L("کشف جفت‌های جدید از منابع عمومی (Lane A — منجمد)", "Discovers new pairs from public sources (Lane A — frozen)"),
      department: "markets",
      implementation: "IMPLEMENTED",
      runtime: "running",
      maturity: 2,
      currentTask: L("چرخه کشف #4812 — سولانا و بیس", "Discovery cycle #4812 — Solana & Base"),
      lastActivityAt: minutesAgo(0.5, now),
      capabilities: [L("خواندن APIهای عمومی", "Read public APIs"), L("نوشتن مشاهده (نه تصمیم)", "Write observations (not decisions)")],
      limitations: [L("کد منجمد — بدون ویرایش", "Frozen code — no edits"), L("بدون اختیار تصمیم", "No decision authority")],
      verification: { status: "PASS", kind: "INDEPENDENT" },
      metrics: { tasks24h: 1_234, successRate: 0.97, avgLatencyMs: 820 },
      events: [],
      sourceDoc: "discovery/",
    },
    {
      id: "agent.news-pipeline",
      code: "N-01",
      name: L("خط لوله خبر", "News Pipeline"),
      role: L("دریافت ۳۰+ منبع، بازنویسی فارسی و منشأ", "Ingests 30+ sources, Persian rewrite + provenance"),
      department: "markets",
      implementation: "IMPLEMENTED",
      runtime: "blocked",
      maturity: 2,
      currentTask: L("در انتظار سهمیه ترجمه", "Waiting for translation quota"),
      lastActivityAt: minutesAgo(18, now),
      capabilities: [L("دریافت RSS", "RSS ingest"), L("ترجمه و خلاصه", "Translate & summarize")],
      limitations: [L("سهمیه ترجمه رایگان محدود است", "Free translation quota is limited")],
      verification: { status: "INCONCLUSIVE", kind: "SELF_CHECK" },
      metrics: { tasks24h: 412, successRate: 0.81, avgLatencyMs: 2600 },
      events: [],
      sourceDoc: "news.ts",
    },
    {
      id: "agent.telegram-edge",
      code: "T-01",
      name: L("لبه تلگرام", "Telegram Edge"),
      role: L("لبه تعامل — ارسال هشدارهای مجاز", "Interaction edge — sends permitted alerts"),
      department: "runtime",
      implementation: "PARTIAL",
      runtime: "failed",
      maturity: 1,
      currentTask: null,
      lastActivityAt: minutesAgo(95, now),
      capabilities: [L("ارسال پیام (پس از تأیید مرجع)", "Send messages (after authority approval)")],
      limitations: [L("نیازمند توکن BotFather", "Requires a BotFather token")],
      verification: { status: "FAIL", kind: "SELF_CHECK" },
      metrics: { tasks24h: 0, successRate: null, avgLatencyMs: null },
      events: [],
      sourceDoc: "telegram_ai/",
    },
    {
      id: "agent.paper-trader",
      code: "P-01",
      name: L("معامله‌گر کاغذی", "Paper Trader"),
      role: L("اجرای سفارش کاغذی پس از مجوز مرجع (Lane A — منجمد)", "Executes paper orders after authority approval (Lane A — frozen)"),
      department: "quant",
      implementation: "IMPLEMENTED",
      runtime: "idle",
      maturity: 2,
      currentTask: null,
      lastActivityAt: minutesAgo(42, now),
      capabilities: [L("باز/بستن موقعیت کاغذی", "Open/close paper positions")],
      limitations: [L("معامله واقعی غیرفعال", "Real trading DISABLED"), L("بدون کیف پول", "No wallets")],
      verification: { status: "PASS", kind: "INDEPENDENT" },
      metrics: { tasks24h: 6, successRate: 1, avgLatencyMs: 140 },
      events: [],
      sourceDoc: "paper_trading/",
    },
    {
      id: "agent.n8n-automation",
      code: "W-01",
      name: L("لبه خودکارسازی n8n", "n8n Automation Edge"),
      role: L("گردش‌کارهای زمان‌بندی‌شده", "Scheduled workflows"),
      department: "runtime",
      implementation: "PARTIAL",
      runtime: "registered",
      maturity: 0,
      currentTask: null,
      lastActivityAt: null,
      capabilities: [],
      limitations: [L("عملیاتی بودن n8n ادعا نشده", "n8n operational status not claimed")],
      verification: { status: "UNVERIFIED", kind: null },
      metrics: { tasks24h: null, successRate: null, avgLatencyMs: null },
      events: [],
      sourceDoc: "n8n/",
    },
  ];

  const scripted: [string, number, AgentEvent["kind"], Localized][] = [
    ["agent.discovery-scout", 0.5, "task_started", L("چرخه کشف #4812 آغاز شد", "Discovery cycle #4812 started")],
    ["agent.research-analyst", 1, "task_started", L("بررسی فرضیه H-12", "Reviewing hypothesis H-12")],
    ["agent.discovery-scout", 2, "task_completed", L("چرخه #4811: ۳۴ جفت جدید، ۲۹ رد شد", "Cycle #4811: 34 new pairs, 29 rejected")],
    ["agent.research-analyst", 9, "task_completed", L("خلاصه مقاله «ریزساختار بازار سولانا» ثبت شد (SELF_CHECK)", "Paper summary 'Solana microstructure' recorded (SELF_CHECK)")],
    ["agent.news-pipeline", 18, "blocked", L("ترجمه متوقف شد: سهمیه MyMemory تمام شد", "Translation paused: MyMemory quota exhausted")],
    ["agent.paper-trader", 42, "task_completed", L("بستن موقعیت کاغذی SOL با +۳٫۱٪", "Closed paper SOL position at +3.1%")],
    ["agent.telegram-edge", 95, "failed", L("اتصال ناموفق: توکن ربات تنظیم نشده", "Connect failed: bot token not configured")],
    ["agent.discovery-scout", 120, "heartbeat", L("ضربان سالم", "Healthy heartbeat")],
  ];
  const events = scripted.map(([agentId, m, kind, text], i) => ev(agentId, m, kind, text, now, i));
  for (const a of operational) a.events = events.filter((e) => e.agentId === a.id);

  return { agents: [...operational, ...planned], departments: DEPARTMENTS };
}

export function mockAgentActivity(now = Date.now()): AgentEvent[] {
  return mockAgents(now)
    .agents.flatMap((a) => a.events)
    .filter((e) => e.kind !== "registered")
    .sort((a, b) => b.at.localeCompare(a.at));
}
