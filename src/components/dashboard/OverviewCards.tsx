"use client";
import { AhosIcon } from "../icons";
import { useState } from "react";
import { ArrowUpLeft } from "lucide-react";
import type { Language } from "../../lib/navigation";
import type { DashboardSnapshot } from "../../lib/api/types";
import { DataCard } from "../cards/DataCard";
import { Sparkline } from "../charts/Sparkline";
export function OverviewCards({
  language,
  snapshot,
}: {
  language: Language;
  snapshot: DashboardSnapshot;
}) {
  const fa = language === "fa";
  const [expandedNews, setExpandedNews] = useState<string | null>(null);
  const [showPositions, setShowPositions] = useState(false);
  const openPnl = snapshot.positions.reduce(
    (sum, item) => sum + (item.mark - item.entry) * item.quantity,
    0,
  );
  return (
    <div className="dc-bottom-grid">
      <DataCard
        title={fa ? "سبد آزمایشی" : "Paper portfolio"}
        icon="nav/portfolio"
        language={language}
        action={
          <button
            className="ah-icon-button"
            aria-expanded={showPositions}
            aria-label={fa ? "نمایش موقعیت‌ها" : "Show positions"}
            onClick={() => setShowPositions(!showPositions)}
          >
            <ArrowUpLeft size={13} />
          </button>
        }
      >
        <div className="dc-paper-total">
          <div>
            <small>{fa ? "ارزش فرضی سبد" : "Virtual portfolio value"}</small>
            <strong dir="ltr">
              $10,476<span>.00</span>
            </strong>
          </div>
          <span className="dc-up">+4.76%</span>
        </div>
        <Sparkline values={snapshot.metrics[5].trend} tone="gold" />
        <div className="dc-mini-stats">
          <span>
            {fa ? "بازده باز" : "Open PnL"}
            <bdi className="dc-up">+${openPnl.toFixed(2)}</bdi>
          </span>
          <span>
            {fa ? "بازده بسته" : "Realized PnL"}
            <bdi>+$181.00</bdi>
          </span>
          <span>
            {fa ? "موقعیت باز" : "Open positions"}
            <bdi>{snapshot.positions.length}</bdi>
          </span>
        </div>
        {showPositions && (
          <div className="dc-inline-detail">
            {snapshot.positions.map((position) => (
              <div key={position.id}>
                <bdi>
                  {position.symbol} × {position.quantity}
                </bdi>
                <bdi className="dc-up">
                  +$
                  {(
                    (position.mark - position.entry) *
                    position.quantity
                  ).toFixed(2)}
                </bdi>
              </div>
            ))}
          </div>
        )}
      </DataCard>
      <DataCard
        title={fa ? "اتاق خبر" : "Newsroom"}
        icon="nav/newsroom"
        language={language}
      >
        <div className="dc-news-list">
          {snapshot.news.map((news) => (
            <article key={news.id}>
              <button
                onClick={() =>
                  setExpandedNews(expandedNews === news.id ? null : news.id)
                }
                aria-expanded={expandedNews === news.id}
              >
                <div>
                  <span
                    className={`dc-verification dc-verify-${news.verification}`}
                  >
                    {news.verification}
                  </span>
                  <time>{news.time}</time>
                </div>
                <h3>{news.title[language]}</h3>
                <small>
                  {news.category[language]} · {news.sources}{" "}
                  {fa ? "منبع فرضی" : "fictional sources"}
                </small>
              </button>
              {expandedNews === news.id && (
                <p className="dc-news-body">{news.body[language]}</p>
              )}
            </article>
          ))}
        </div>
      </DataCard>
      <DataCard
        title={fa ? "دانشگاه AHOS" : "AHOS University"}
        icon="nav/university"
        language={language}
      >
        <div className="dc-university-score">
          <div className="dc-score-ring">
            <strong>
              {snapshot.university.passed}
              <small>/ 19</small>
            </strong>
          </div>
          <div>
            <strong>
              {fa ? "آزمون‌های سناریوی نمونه" : "Demo evaluations"}
            </strong>
            <small>
              {fa
                ? "نتایج مصنوعی، نه عملکرد واقعی"
                : "Synthetic results, not real performance"}
            </small>
          </div>
        </div>
        <div className="dc-mini-stats">
          <span>
            {fa ? "قبول" : "Passed"}
            <bdi className="dc-up">{snapshot.university.passed}</bdi>
          </span>
          <span>
            {fa ? "مردود" : "Failed"}
            <bdi className="dc-down">{snapshot.university.failed}</bdi>
          </span>
          <span>
            {fa ? "در صف" : "Queued"}
            <bdi>{snapshot.university.queued}</bdi>
          </span>
        </div>
        <div className="dc-course-list">
          {snapshot.university.courses.map((course) => (
            <div key={course.en}>
              <AhosIcon name="nav/university" size={14} />
              <span>{course[language]}</span>
              <span className="dc-agent-state dc-state-planned">planned</span>
            </div>
          ))}
        </div>
      </DataCard>
      <DataCard
        title={fa ? "سلامت سیستم" : "System health"}
        icon="nav/market-prices"
        language={language}
      >
        <div className="dc-system-status">
          <span className="dc-outline-dot" />
          <strong>{fa ? "نمایش تله‌متری نمونه" : "Sample telemetry"}</strong>
          <span className="dc-agent-state dc-state-registered">DEMO</span>
        </div>
        <div className="dc-system-bars">
          {snapshot.system.map((item) => (
            <div key={item.name}>
              <div>
                <span>{item.name}</span>
                <bdi>
                  {item.value}
                  {item.unit}
                </bdi>
              </div>
              <div className="dc-progress">
                <span style={{ width: `${item.value}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="dc-system-note">
          <span>{fa ? "اتصال به اجرا" : "Runtime connection"}</span>
          <bdi>UNAVAILABLE</bdi>
        </div>
        <p className="dc-small-note">
          {fa
            ? "این درصدها اندازه‌گیری دستگاه شما نیستند."
            : "These values do not measure your device."}
        </p>
      </DataCard>
    </div>
  );
}
