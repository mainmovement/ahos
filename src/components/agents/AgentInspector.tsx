"use client";
import { tr } from "../../lib/i18n";
import { useEffect, useRef } from "react";
import { Bot, X } from "lucide-react";
import type { Agent } from "../../lib/api/types";
import type { Language } from "../../lib/navigation";
import { StatusChip } from "../cards/DataCard";
export function AgentInspector({
  agent,
  language,
  onClose,
}: {
  agent: Agent | null;
  language: Language;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const fa = language === "fa";
  useEffect(() => {
    if (agent && !ref.current?.open) ref.current?.showModal();
    if (!agent && ref.current?.open) ref.current.close();
  }, [agent]);
  return (
    <dialog
      className="dc-inspector"
      ref={ref}
      onClose={onClose}
      onCancel={onClose}
      aria-labelledby="agent-title"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {agent && (
        <div className="dc-inspector-inner">
          <header>
            <Bot size={24} />
            <span>AGENT INSPECTOR</span>
            <button
              className="ah-icon-button"
              onClick={onClose}
              aria-label={fa ? "بستن مشخصات عامل" : "Close agent inspector"}
            >
              <X size={19} />
            </button>
          </header>
          <span className="dc-inspector-id">{agent.id}</span>
          <h2 id="agent-title">{agent.name[language]}</h2>
          <div className="dc-inspector-status">
            <StatusChip />
            <span className={`dc-agent-state dc-state-${agent.state}`}>
              {agent.state}
            </span>
          </div>
          <p className="dc-demo-disclaimer">
            {fa
              ? "تمام وضعیت‌ها شبیه‌سازی‌شده‌اند. هیچ عامل واقعی در حال اجرا نیست."
              : "All states are simulated. No actual agent process is executing."}
          </p>
          <dl>
            {[
              { name: fa ? tr("fa", "pages.agents.agents.table.role") : "Role", value: agent.role[language] },
              {
                name: fa ? tr("fa", "common.labels.department") : "Department",
                value: agent.department[language],
              },
              {
                name: fa ? "وضعیت پیاده‌سازی" : "Implementation",
                value: agent.implementation[language],
              },
              {
                name: fa ? "مأموریت فعلی" : "Current task",
                value: agent.task[language],
              },
              {
                name: fa ? "آخرین فعالیت نمونه" : "Fixture activity",
                value: agent.activityAt,
              },
              {
                name: fa ? "شناسهٔ شاهد" : "Evidence ID",
                value: agent.evidence,
              },
            ].map((row) => (
              <div key={row.name}>
                <dt>{row.name}</dt>
                <dd dir="auto">{row.value}</dd>
              </div>
            ))}
          </dl>
          <div className="dc-progress">
            <span style={{ width: `${agent.progress}%` }} />
          </div>
          <small>
            {fa ? "پیشرفت مأموریت نمونه" : "Fixture task progress"}:{" "}
            {agent.progress}%
          </small>
        </div>
      )}
    </dialog>
  );
}
