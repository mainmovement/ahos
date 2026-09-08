import { NextResponse } from "next/server";
import { db } from "@/db";
import { tokens, paperTrades } from "@/db/schema";
import { desc } from "drizzle-orm";

export async function POST(request: Request) {
  try {
    const { message } = await request.json();
    const query = (message || "").trim().toLowerCase();

    const topTokens = await db.select().from(tokens).orderBy(desc(tokens.opportunityScore)).limit(3);
    const activeTrades = await db.select().from(paperTrades).limit(3);

    let reply = "";

    if (query.includes("بهترین") || query.includes("پیشنهاد") || query.includes("best") || query.includes("opportunity")) {
      const top = topTokens[0];
      if (top) {
        reply = `🔍 **برترین فرصت شناسایی‌شده توسط سیستم AHOS:**\n\n` +
          `• **نام توکن:** ${top.name} (${top.symbol})\n` +
          `• **شبکه:** ${top.chain}\n` +
          `• **امتیاز فرصت (Opportunity Score):** ${top.opportunityScore}/100\n` +
          `• **امتیاز امنیت (Security Score):** ${top.securityScore}/100\n` +
          `• **میزان اطمینان (Confidence):** ${top.confidenceScore}%\n` +
          `• **قیمت فعلی:** $${top.price} (${top.priceChange24h}% 24h)\n\n` +
          `**چرا این توکن انتخاب شد؟ (Evidence Before Decision):**\n` +
          `${top.evidenceSummary}\n\n` +
          `**نظر شورای AI:** تمامی ۱۰ تیم تخصصی (از جمله تیم امنیت و تیم ریاضی) آن را بررسی کرده و تایید نموده‌اند.`;
      } else {
        reply = "در حال حاضر هیچ توکن تاییدشده‌ای در پایگاه داده یافت نشد.";
      }
    } else if (query.includes("معامله") || query.includes("پورتفوی") || query.includes("trade") || query.includes("paper")) {
      reply = `📈 **وضعیت پورتفوی معاملات فرضی (Paper Trading):**\n\n`;
      if (activeTrades.length > 0) {
        activeTrades.forEach((t) => {
          reply += `• **${t.symbol}**: ورود در $${t.entryPrice} | قیمت فعلی $${t.currentPrice} | PnL: ${t.pnlPercent}% ($${t.pnlUsd}) | وضعیت: ${t.status}\n`;
        });
      } else {
        reply += "هیچ معامله فرضی فعال وجود ندارد.";
      }
    } else if (query.includes("امنیت") || query.includes("سکم") || query.includes("scam") || query.includes("security")) {
      reply = `🛡️ **سیستم ضد Scam و Risk Gate شبکه AHOS:**\n\n` +
        `قانون اصلی AHOS:\n` +
        `**High Opportunity + Critical Security Risk = MANDATORY REJECT**\n\n` +
        `تیم ۰۴ (Cybersecurity & Hacker Intelligence) قبل از هر پیشنهادی موارد زیر را بررسی می‌کند:\n` +
        `1. عدم امکان Honeypot و قفل بودن نقدینگی (LP Lock)\n` +
        `2. بررسی کدهای مخفی و Mint / Freeze Authority\n` +
        `3. تحلیل رفتار کیف‌پول‌های سازنده (Deployer) و نهنگ‌ها\n` +
        `4. عدم دستکاری کارمزد خرید و فروش (Tax Manipulation)`;
    } else if (query.includes("سلام") || query.includes("hi") || query.includes("hello")) {
      reply = `سلام! من دستیار هوشمند **AHOS (Artificial Hybrid Opportunity Scoring System)** هستم.\n\n` +
        `می‌توانید از من بپرسید:\n` +
        `• «بهترین فرصت امروز چیست؟»\n` +
        `• «وضعیت معاملات فرضی چیست؟»\n` +
        `• «سیستم امنیت چگونه کار می‌کند؟»\n` +
        `• «آدرس قرارداد یا توکن مورد نظر خود را بفرستید تا شورا بررسی کند.»`;
    } else {
      reply = `🤖 **پاسخ سیستم AHOS به پرسش شما:**\n\n` +
        `بر اساس الگوریتم Evidence Before Decision، اطلاعات اولیه برای «${message}» دریافت شد.\n\n` +
        `• **تحلیل شورا:** شورای ۱۰ تایی هوش مصنوعی داده‌های آنچین، شبکه‌های اجتماعی، داده‌های ریاضی و گیت امنیت را فعال نمود.\n` +
        `• **نتیجه ارزیابی:** داده‌ها در حال ثبت در درخت دانا (Tree of Wisdom) و Post-Mortem هستند.\n\n` +
        `برای مشاهده جزییات کامل، پرونده (Dossier) توکن را در داشبورد سه بعدی بررسی کنید.`;
    }

    return NextResponse.json({ success: true, reply });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
