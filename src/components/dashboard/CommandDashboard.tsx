"use client";
import { AhosIcon } from "../icons";
import { useState } from "react";
import { ArrowUpLeft, Layers3 } from "lucide-react";
import { getDashboardSnapshot } from "../../lib/api/dashboard";
import type { Agent } from "../../lib/api/types";
import type { Language, Quality } from "../../lib/navigation";
import { DataCard, ProvenanceFooter, StatusChip } from "../cards/DataCard";
import { MarketTable } from "../cards/MarketTable";
import { Sparkline } from "../charts/Sparkline";
import { MarketChart } from "../charts/MarketChart";
import { AgentInspector } from "../agents/AgentInspector";
import { KianChat } from "./KianChat";
import { OverviewCards } from "./OverviewCards";
import { EarthPanel } from "../globe/EarthPanel";
import { OrbSlot } from "../orb/OrbSlot";
import { getContentDemoNotice, getContentDepartments, getContentGate, getContentHealth, getContentSignals } from "../../lib/api/content";
export function CommandDashboard({
  language,
  quality,
}: {
  language: Language;
  quality: Quality;
}) {
  const [snapshot] = useState(getDashboardSnapshot);
  const [symbol, setSymbol] = useState("BTC");
  const [agent, setAgent] = useState<Agent | null>(null);
  const [acknowledged, setAcknowledged] = useState<string[]>([]);
  const fa = language === "fa";
  return (
    <div className="dc-dashboard">
      <div className="dc-demo-strip">
        <span>
          <AhosIcon name="status/demo" variant="color" size={14} />
          {fa ? "سناریوی نمایشی" : "DEMO WORKSPACE"}
        </span>
        <p>{getContentDemoNotice()[language]}</p>
        <bdi>16 OCT 2026 · 08:00 UTC</bdi>
      </div>
      <OrbSlot
        health={getContentHealth()}
        departments={getContentDepartments()}
        signals={getContentSignals()}
        gate={getContentGate()}
        calm={quality === "low"}
        language={language}
      />
      <div className="dc-kpi-grid">
        {snapshot.metrics.map((metric, index) => (
          <section className={`dc-kpi dc-tone-${metric.tone}`} key={metric.id}>
            <div className="dc-kpi-title">
              <span>{metric.title[language]}</span>
              <StatusChip />
            </div>
            <div className="dc-kpi-middle">
              <strong dir="ltr">{metric.value}</strong>
              <Sparkline
                values={metric.trend}
                tone={metric.tone}
                label={`${metric.title[language]} DEMO trend`}
              />
            </div>
            <div className="dc-kpi-note">
              <bdi>{metric.change}</bdi>
              <span>{metric.note[language]}</span>
              <span className="dc-kpi-index">0{index + 1}</span>
            </div>
            <ProvenanceFooter language={language} />
          </section>
        ))}
      </div>
      <div className="dc-command-grid">
        <div className="dc-primary">
          <EarthPanel language={language} quality={quality} />
          <div className="dc-analysis-grid">
            <MarketChart language={language} symbol={symbol} />
            <MarketTable
              language={language}
              selected={symbol}
              onSelect={setSymbol}
            />
          </div>
          <div className="dc-evidence-banner">
            <span className="dc-evidence-symbol">
              <AhosIcon name="status/unknown" variant="color" size={21} />
            </span>
            <div>
              <strong>
                {fa ? "شواهد، پیش از تصمیم" : "Evidence before decisions"}
              </strong>
              <p>
                {fa
                  ? "دادهٔ نامشخص هرگز به‌عنوان امن یا تأییدشده نمایش داده نمی‌شود."
                  : "Unknown evidence is never presented as safe or verified."}
              </p>
            </div>
            <span className="ah-chip">UNKNOWN ≠ SAFE</span>
          </div>
        </div>
        <aside
          className="dc-intelligence-column"
          aria-label={fa ? "دستیار و فعالیت‌ها" : "Assistant and activity"}
        >
          <KianChat language={language} />
          <DataCard
            title={fa ? "فعالیت عامل‌ها" : "Agent activity"}
            icon="nav/agents"
            language={language}
          >
            <p className="dc-small-note">
              {fa
                ? "وضعیت‌های نمونه · بدون پردازش واقعی"
                : "Simulated states · No running processes"}
            </p>
            <div className="dc-agent-feed">
              {snapshot.agents.map((item) => (
                <button
                  className="dc-agent-item"
                  key={item.id}
                  onClick={() => setAgent(item)}
                >
                  <span className={`dc-agent-symbol dc-state-${item.state}`}>
                    <Layers3 size={15} />
                  </span>
                  <span>
                    <strong>{item.name[language]}</strong>
                    <small>{item.task[language]}</small>
                  </span>
                  <span className="dc-agent-meta">
                    <span className={`dc-agent-state dc-state-${item.state}`}>
                      {item.state}
                    </span>
                    <time>{item.activityAt.slice(0, 5)}</time>
                  </span>
                  <ArrowUpLeft size={10} />
                </button>
              ))}
            </div>
          </DataCard>
          <DataCard
            title={fa ? "هشدارها و شواهد" : "Alerts & evidence"}
            icon="status/warning"
            language={language}
          >
            <div className="dc-alert-list">
              {snapshot.alerts.map((alert) => (
                <article key={alert.id}>
                  <div className="dc-alert-title">
                    <AhosIcon name="status/warning" variant="color" size={14} />
                    <h3>{alert.title[language]}</h3>
                    <time>{alert.time}</time>
                  </div>
                  <p>{alert.body[language]}</p>
                  <button
                    onClick={() =>
                      setAcknowledged((old) =>
                        old.includes(alert.id) ? old : [...old, alert.id],
                      )
                    }
                    disabled={acknowledged.includes(alert.id)}
                  >
                    {acknowledged.includes(alert.id)
                      ? fa
                        ? "خوانده شد · ریسک برطرف نشده"
                        : "Read · Risk not resolved"
                      : fa
                        ? "علامت‌گذاری به‌عنوان خوانده‌شده"
                        : "Mark as read"}
                  </button>
                </article>
              ))}
            </div>
          </DataCard>
        </aside>
      </div>
      <OverviewCards language={language} snapshot={snapshot} />
      <AgentInspector
        agent={agent}
        language={language}
        onClose={() => setAgent(null)}
      />
    </div>
  );
}
