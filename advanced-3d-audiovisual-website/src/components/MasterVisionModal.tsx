"use client";

import React from "react";
import { soundFx } from "@/utils/audio";
import { X, BookOpen, FileText, Shield, Award, Terminal } from "lucide-react";

export function MasterVisionModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(5,7,12,0.9)] backdrop-blur-lg animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#0a0e17] border border-[rgba(0,243,255,0.3)] rounded-2xl p-6 shadow-[0_0_80px_rgba(0,243,255,0.2)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.1)] pb-4 mb-4">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-[#00f3ff]" />
            <div>
              <h2 className="text-lg font-bold font-mono text-white">
                AHOS — MASTER PROJECT VISION & SYSTEM SPECIFICATION
              </h2>
              <span className="text-xs font-mono text-[#00ff88]">
                نسخه: 1.0 | وضعیت: Master Vision / Foundational Specification
              </span>
            </div>
          </div>

          <button
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="p-2 rounded-lg hover:bg-[rgba(255,0,85,0.2)] text-gray-400 hover:text-[#ff0055] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Specification Document Body */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-6 text-gray-300 font-sans text-sm leading-relaxed text-right" dir="rtl">
          <section className="p-4 rounded-xl bg-[rgba(0,243,255,0.04)] border border-[rgba(0,243,255,0.2)]">
            <h3 className="font-bold font-mono text-[#00f3ff] text-base mb-2">۱. مقدمه و فلسفه اصلی AHOS</h3>
            <p>
              AHOS مخفف <strong>Artificial Hybrid Opportunity Scoring System</strong> است. AHOS یک بات معاملاتی ساده نیست؛ بلکه یک موجودیت هوشمند جستجوگر، تحلیلگر، ارزیاب ریسک و یادگیرنده است.
            </p>
            <p className="mt-2 text-xs font-mono text-[#00ff88]">
              اصل کلیدی: <strong>Evidence Before Decision (قبل از تصمیم، شواهد)</strong>
            </p>
          </section>

          <section className="p-4 rounded-xl bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)]">
            <h3 className="font-bold font-mono text-[#00ff88] text-base mb-2">۲. شورای ۱۰ تایی هوش مصنوعی (10-Team AI Council)</h3>
            <ul className="list-disc list-inside space-y-1.5 text-xs font-mono text-gray-300">
              <li><strong>تیم ۰۱ — Mathematical Intelligence:</strong> مدل‌های احتمالاتی و سری‌های زمانی</li>
              <li><strong>تیم ۰۲ — Crypto Market Intelligence:</strong> ساختار بازار و عمق نقدینگی DEX</li>
              <li><strong>تیم ۰۳ — Blockchain & On-Chain Intelligence:</strong> ردگیری نهنگ‌ها و Smart Money</li>
              <li><strong>تیم ۰۴ — Cybersecurity & Hacker Intelligence:</strong> گیت امنیت Red Team و کشف Honeypot</li>
              <li><strong>تیم ۰۵ — Investigative Intelligence:</strong> کارآگاه دیجیتال و OSINT</li>
              <li><strong>تیم ۰۶ — News & Journalism Intelligence:</strong> صحت‌سنجی اخبار و رسانه‌ها</li>
              <li><strong>تیم ۰۷ — Social & Narrative Intelligence:</strong> سنجش سرعت Narrative و فیلتر بات‌ها</li>
              <li><strong>تیم ۰۸ — Technology & Software Engineering:</strong> تحلیل گیت‌هاب و کیفیت کد</li>
              <li><strong>تیم ۰۹ — AI Research & Self-Evolution:</strong> سیستم‌های RAG و خودآموزی</li>
              <li><strong>تیم ۱۰ — Strategic Decision & Red-Team Council:</strong> چالش‌گری، خنثی‌سازی Confirmation Bias</li>
            </ul>
          </section>

          <section className="p-4 rounded-xl bg-[rgba(255,0,85,0.05)] border border-[rgba(255,0,85,0.2)]">
            <h3 className="font-bold font-mono text-[#ff0055] text-base mb-2">۳. گیت امنیت و فیلتر ضد Scam (Risk Gate)</h3>
            <p className="text-xs font-mono text-gray-300">
              قانون حیاتی AHOS: <br />
              <strong className="text-[#ff0055]">High Opportunity + Critical Security Risk = MANDATORY REJECT</strong>
              <br />
              حتی اگر امتیاز فرصت ۹۹ باشد، در صورت وجود ریسک امنیتی یا کدهای مخفی، توکن به‌طور مطلق رد خواهد شد.
            </p>
          </section>

          <section className="p-4 rounded-xl bg-[rgba(255,170,0,0.05)] border border-[rgba(255,170,0,0.2)]">
            <h3 className="font-bold font-mono text-[#ffaa00] text-base mb-2">۴. استعاره درخت دانا و اقیانوس دانش (Tree of Wisdom)</h3>
            <p className="text-xs font-mono text-gray-300">
              ریشه‌ها (دیتا)، تنه (معماری)، شاخه‌ها (تیم‌ها)، میوه‌ها (فرصت‌ها) و آب‌های زیرزمینی (اقیانوس هوش جمعی). سیستم از تمام معامله‌های فرضی (Paper Trading) و شکست‌ها، الگوی Failure Pattern استخراج کرده و دانش خود را خودتوسعه می‌دهد.
            </p>
          </section>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-[rgba(255,255,255,0.1)] flex justify-between items-center text-xs font-mono text-gray-400">
          <span>Master Node: GitHub & Local Python Compatible</span>
          <button
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="px-4 py-2 rounded-xl bg-[#00f3ff] text-black font-bold"
          >
            بستن سند
          </button>
        </div>
      </div>
    </div>
  );
}
