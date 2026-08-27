import type {
  Confidence,
  ExpertDefinition,
  ExpertVote,
  ExpertVoteKind,
  PairObservation,
  SecurityAssessment,
} from "./types";

const TEAMS: Array<{ id: string; fa: string; roles: string[] }> = [
  {
    id: "security",
    fa: "تیم امنیت قرارداد",
    roles: [
      "بازرس هانی‌پات",
      "بازرس محدودیت فروش",
      "بازرس مینت",
      "بازرس فریز",
      "بازرس مالکیت",
      "بازرس بلک‌لیست",
      "بازرس پروکسی",
      "بازرس مالیات پنهان",
      "بازرس نقدینگی قفل",
      "داور UNKNOWN≠SAFE",
    ],
  },
  {
    id: "liquidity",
    fa: "تیم نقدینگی و ریزساختار",
    roles: [
      "تحلیل‌گر عمق نقدینگی",
      "بازرس نسبت حجم به نقدینگی",
      "کاشف واش‌تریدینگ",
      "تحلیل‌گر اسپرد",
      "بازرس استخر نوپا",
      "متریک حجم واقعی",
      "نگهبان لغزش",
      "مقایسه‌گر DEX",
      "بازرس قفل LP",
      "داور کیفیت بازار",
    ],
  },
  {
    id: "onchain",
    fa: "تیم آن‌چین و نهنگ",
    roles: [
      "ردیاب نهنگ",
      "تحلیل‌گر توزیع هولدر",
      "بازرس کیف دیپلوییر",
      "کاشف اسمارت‌مانی",
      "بازرس خزانه",
      "تحلیل‌گر جریان صرافی",
      "نقشه‌کش خوشه کیف",
      "بازرس تراکنش غیرعادی",
      "داور نقش کیف UNKNOWN",
      "ناظر تمرکز عرضه",
    ],
  },
  {
    id: "news",
    fa: "تیم اخبار و روایت",
    roles: [
      "کاتالیزور یاب",
      "بازرس هک و رخنه",
      "ناظر قانون‌گذاری",
      "ردیاب لیست شدن",
      "تحلیل‌گر ETF",
      "بازرس اخبار ماکرو",
      "مترجم روایت فارسی",
      "سنجش تازگی خبر",
      "جداکننده شایعه از سند",
      "داور تأثیر بازار",
    ],
  },
  {
    id: "social",
    fa: "تیم اجتماعی و ضدهایپ",
    roles: [
      "سنجش ویرالیتی",
      "کاشف تبلیغ پولی",
      "بازرس DexScreener Boost",
      "ضد اینفلوئنسر",
      "کیفیت منبع اجتماعی",
      "ردیت‌خوان مجاز",
      "مسدودگر اسکرپ غیرمجاز",
      "هشدار اتاق پژواک",
      "داور هایپ ≠ خرید",
      "ناظر جامعه",
    ],
  },
  {
    id: "macro",
    fa: "تیم رژیم بازار و کلان",
    roles: [
      "تشخیص رژیم",
      "ترس و طمع",
      "بتای بیت‌کوین",
      "همبستگی سولانا",
      "نوسان‌سنج",
      "ناظر دامیننس",
      "TVL دیفای",
      "کارمزد شبکه",
      "رژیم نقدینگی کلان",
      "داور زمان‌بندی",
    ],
  },
  {
    id: "probability",
    fa: "تیم احتمال و کالیبراسیون",
    roles: [
      "بیزین",
      "نرخ پایه",
      "بریر اسکور",
      "خطای کالیبراسیون",
      "عدم‌قطعیت",
      "ارزش مورد انتظار",
      "احتمال بقا",
      "همبستگی رتبه‌ای",
      "ضد عدد تزئینی",
      "داور شواهد ناکافی",
    ],
  },
  {
    id: "risk",
    fa: "تیم ریسک و رد فرصت",
    roles: [
      "دروازه رد",
      "ریسک نقدشوندگی",
      "ریسک قرارداد",
      "ریسک تمرکز",
      "ریسک روایت",
      "حد ضرر مفهومی",
      "نسبت پاداش به ریسک",
      "ابطال‌پذیری",
      "ضد اطمینان جعلی",
      "داور اجتناب",
    ],
  },
  {
    id: "discovery",
    fa: "تیم لانچ‌پد و کشف",
    roles: [
      "کاشف DexScreener",
      "کاشف GeckoTerminal",
      "کاشف Pump.fun",
      "سنجش سن استخر",
      "اصالت لانچ‌پد",
      "ردیاب پروفایل توکن",
      "متا ترند",
      "فیلتر نویز میم",
      "اولویت شواهد چندمنبعی",
      "داور کاندید اولیه",
    ],
  },
  {
    id: "learning",
    fa: "تیم یادگیری و گذشته‌نگری",
    roles: [
      "ثبت پیش‌بینی",
      "برچسب نتیجه",
      "MFE/MAE",
      "طبقه‌بندی خطا",
      "درس از شکست",
      "تقویت نقطه قوت",
      "حافظه آزمایش",
      "جلوگیری از تکرار",
      "کالیبراسیون افق",
      "داور بهبود",
    ],
  },
];

export const EXPERTS: ExpertDefinition[] = TEAMS.flatMap((team, ti) =>
  team.roles.map((role, ri) => ({
    id: `T${String(ti + 1).padStart(2, "0")}-E${String(ri + 1).padStart(2, "0")}`,
    teamId: team.id,
    teamFa: team.fa,
    nameFa: role,
    specialty: `${team.id}:${ri}`,
  })),
);

export type CouncilInput = {
  token: PairObservation;
  security: SecurityAssessment | null;
  fearGreed: number | null;
  newsHits: number;
  negativeNews: boolean;
  paidPromo: boolean;
};

export type CouncilResult = {
  votes: ExpertVote[];
  verdict: string;
  disagreement: boolean;
  agreeWatch: number;
  reject: number;
  abstain: number;
  paper: number;
  summaryFa: string;
  disagreementFa: string[];
};

function vote(
  expert: ExpertDefinition,
  kind: ExpertVoteKind,
  confidence: Confidence,
  reasonFa: string,
  uncertaintyFa: string,
): ExpertVote {
  return {
    expertId: expert.id,
    teamId: expert.teamId,
    expertNameFa: `${expert.teamFa} / ${expert.nameFa}`,
    vote: kind,
    confidence,
    reasonFa,
    uncertaintyFa,
  };
}

function evaluate(expert: ExpertDefinition, input: CouncilInput): ExpertVote {
  const t = input.token;
  const s = input.security;
  const liq = t.liquidityUsd;
  const vol = t.volume24h;
  const ch = t.priceChange24h;
  const paid = input.paidPromo || t.paidPromotion;
  const unknownSec = !s || s.honeypot === "UNKNOWN";
  const ratio = liq && vol && liq > 0 ? vol / liq : null;
  const [team, idxStr] = expert.specialty.split(":");
  const idx = Number(idxStr);

  if (team === "security") {
    if (!s || s.status !== "SUCCESS") {
      return vote(expert, "ABSTAIN", "UNKNOWN", "داده امنیتی SUCCESS نیست — ABSTAIN.", "UNKNOWN ≠ SAFE");
    }
    if (s.honeypot === "YES" || s.flags.includes("HONEYPOT") || s.sellable === "NO") {
      return vote(expert, "REJECT", "HIGH", `شواهد امنیتی رد: ${s.flags.join("، ") || s.summaryFa}`, "هانی‌پات/عدم فروش");
    }
    if (s.flags.length >= 2) {
      return vote(expert, "REJECT", "MED", `چند پرچم امنیتی: ${s.flags.join("، ")}`, "ریسک قرارداد");
    }
    if (unknownSec) return vote(expert, "ABSTAIN", "UNKNOWN", "امنیت UNKNOWN است.", "UNKNOWN");
    return vote(expert, "WATCH", "LOW", "پرچم هانی‌پات قطعی نیست؛ فقط پایش.", "شواهد ناقص باقی است");
  }

  if (team === "liquidity") {
    if (liq == null) return vote(expert, "ABSTAIN", "UNKNOWN", "نقدینگی UNKNOWN — عدد صفر جعل نشد.", "NO_DATA");
    if (liq < 8000) return vote(expert, "REJECT", "HIGH", `نقدینگی ${Math.round(liq)} دلار خیلی نازک است.`, "ریسک خروج");
    if (ratio != null && ratio > 25) {
      return vote(expert, "REJECT", "MED", `نسبت حجم/نقدینگی ${ratio.toFixed(1)} مشکوک به شستشو است.`, "واش‌ترید احتمالی");
    }
    if (liq > 80000 && (vol ?? 0) > 20000) {
      return vote(expert, "WATCH", "MED", "عمق نقدینگی نسبتاً قابل مشاهده است.", "قفل LP هنوز UNKNOWN");
    }
    return vote(expert, "WATCH", "LOW", "نقدینگی متوسط؛ برای ورود کاغذی هم احتیاط.", "LP lock UNKNOWN");
  }

  if (team === "onchain") {
    if (idx === 8) {
      return vote(expert, "ABSTAIN", "UNKNOWN", "نقش کیف‌ها بدون سند = UNKNOWN. هویت جعل نشد.", "wallet_role=UNKNOWN");
    }
    if (t.buys24h == null && t.sells24h == null) {
      return vote(expert, "ABSTAIN", "UNKNOWN", "جریان خرید/فروش UNKNOWN است.", "NO_DATA");
    }
    if ((t.sells24h ?? 0) > (t.buys24h ?? 0) * 2 && (t.sells24h ?? 0) > 40) {
      return vote(expert, "REJECT", "LOW", "فشار فروش مشهودتر از خرید است.", "ممکن است رژیم خروج باشد");
    }
    return vote(expert, "WATCH", "LOW", "شواهد آن‌چین جزئی است؛ نهنگ هویت‌سازی نشد.", "holder concentration UNKNOWN");
  }

  if (team === "news") {
    if (input.negativeNews) {
      return vote(expert, "REJECT", "MED", "خبر منفی مرتبط (هک/قانون/رخنه) در چرخه فعلی دیده شد.", "کاتالیزور منفی");
    }
    if (input.newsHits === 0) {
      return vote(expert, "ABSTAIN", "UNKNOWN", "خبر اختصاصی این توکن پیدا نشد.", "INSUFFICIENT_EVIDENCE");
    }
    return vote(expert, "WATCH", "LOW", `${input.newsHits} خبر مرتبط یافت شد — روایت به‌تنهایی خرید نیست.`, "کیفیت منبع محدود");
  }

  if (team === "social") {
    if (paid) {
      return vote(expert, "REJECT", "HIGH", "Boost/پروفایل پولی DexScreener = تبلیغ پرداخت‌شده، نه تقاضای ارگانیک.", "PAID_PROMOTION");
    }
    if (ch != null && ch > 80 && (liq ?? 0) < 30000) {
      return vote(expert, "REJECT", "MED", "جهش قیمت + نقدینگی نازک = الگوی هایپ.", "anti-hype gate");
    }
    return vote(expert, "WATCH", "LOW", "سیگنال اجتماعی به‌تنهایی خرید نمی‌سازد.", "X/IG OUT_OF_POLICY");
  }

  if (team === "macro") {
    if (input.fearGreed == null) {
      return vote(expert, "ABSTAIN", "UNKNOWN", "شاخص ترس/طمع UNKNOWN.", "NO_DATA");
    }
    if (input.fearGreed >= 80 && (ch ?? 0) > 40) {
      return vote(expert, "REJECT", "LOW", "طمع افراطی بازار + مومنتوم توکن — زمان‌بندی ضعیف.", "regime=greed");
    }
    return vote(expert, "WATCH", "LOW", `رژیم ترس/طمع=${input.fearGreed}. فقط زمینه است نه سیگنال خرید.`, "correlation UNKNOWN");
  }

  if (team === "probability") {
    const fields = [t.priceUsd, t.liquidityUsd, t.volume24h, t.fdv, t.priceChange24h, s?.status === "SUCCESS"];
    const known = fields.filter((x) => x !== null && x !== undefined && x !== false).length;
    if (known < 3) {
      return vote(expert, "ABSTAIN", "UNKNOWN", "برای احتمال‌سازی عدد تزئینی ساخته نشد.", "INSUFFICIENT_EVIDENCE");
    }
    return vote(expert, "WATCH", "LOW", `پوشش شواهد ${known}/6. احتمال دقیق قابل ادعا نیست.`, "no decorative probability");
  }

  if (team === "risk") {
    if (s?.honeypot === "YES" || paid && (liq ?? 0) < 20000) {
      return vote(expert, "REJECT", "HIGH", "دروازه ریسک: امنیت بد یا هایپ پولی با نقدینگی نازک.", "REJECT > unsafe guess");
    }
    if (unknownSec && (liq ?? 0) < 25000) {
      return vote(expert, "REJECT", "MED", "امنیت UNKNOWN و نقدینگی محدود — اجتناب.", "UNKNOWN security");
    }
    return vote(expert, "WATCH", "LOW", "ریسک قابل رد قطعی نیست؛ ورود واقعی ممنوع.", "paper-only");
  }

  if (team === "discovery") {
    const multi = t.source.includes(",") || t.source.includes("+");
    if (t.source.includes("Pump.fun") && (liq ?? 0) < 5000) {
      return vote(expert, "REJECT", "MED", "کاندید لانچ‌پد با نقدینگی خیلی کم.", "launch noise");
    }
    if (multi && (liq ?? 0) > 20000) {
      return vote(expert, "WATCH", "MED", "چند منبع کشف این توکن را دیدند.", "still not a buy");
    }
    return vote(expert, "WATCH", "LOW", `منبع کشف: ${t.source}.`, "needs more evidence");
  }

  // learning team
  if (t.priceUsd == null) {
    return vote(expert, "ABSTAIN", "UNKNOWN", "بدون قیمت واقعی نمی‌توان later outcome ساخت.", "NO_DATA");
  }
  return vote(expert, "WATCH", "LOW", "اگر انتخاب شود باید پیش‌بینی و افق ثبت شود تا بعداً درس گرفته شود.", "no peeking");
}

// ONE BRAIN: the TS `runCouncil` opportunity/verdict authority is RETIRED.
// Opportunity verdicts are the Python canonical brain's sole authority. This
// module now only exposes `TEAM_META` — non-authoritative presentation metadata
// (team names/sizes) for the dashboard. It performs no scoring or verdict.

export const TEAM_META = TEAMS.map((t) => ({ id: t.id, fa: t.fa, size: t.roles.length }));
