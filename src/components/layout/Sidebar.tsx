"use client";
import { AhosIcon } from "../icons";
import { useState } from "react";
import { ChevronDown, ChevronLeft, X } from "lucide-react";
import { navigation, type Language } from "../../lib/navigation";
import { StarMark } from "../ui/Brand";

type Props = {
  language: Language;
  active: string;
  onNavigate: (id: string) => void;
  open: boolean;
  onClose: () => void;
};
export function Sidebar({
  language,
  active,
  onNavigate,
  open,
  onClose,
}: Props) {
  const [collapsed, setCollapsed] = useState<string[]>(navigation.filter((g) => g.id === "operations" && !g.items.some((i) => i.id === active)).map((g) => g.id));
  const fa = language === "fa";
  return (
    <>
      {open && (
        <button
          className="ah-mobile-scrim"
          aria-label={fa ? "بستن فهرست" : "Close navigation"}
          onClick={onClose}
        />
      )}
      <aside
        id="primary-sidebar"
        className={`ah-sidebar ${open ? "is-open" : ""}`}
        aria-label={fa ? "ناوبری اصلی" : "Main navigation"}
      >
        <div className="ah-brand">
          <StarMark />
          <div>
            <strong>
              AHOS<span>®</span>
            </strong>
            <small>
              {fa ? "هوشمندی فراتر از داده" : "INTELLIGENCE BEYOND DATA"}
            </small>
          </div>
          <button
            className="ah-icon-button ah-mobile-only"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>
        <div className="ah-workspace">
          <span className="ah-workspace-symbol">A</span>
          <div>
            <strong>{fa ? "فضای کاری شخصی" : "Personal workspace"}</strong>
            <small>AHOS / INTELLIGENCE OS</small>
          </div>
          <span className="ah-tiny-label">V.01</span>
        </div>
        <nav className="ah-navigation">
          {navigation.map((group) => (
            <section key={group.id} className="ah-nav-group">
              <button
                className="ah-group-title"
                aria-expanded={!collapsed.includes(group.id)}
                aria-controls={`nav-${group.id}`}
                onClick={() =>
                  setCollapsed((old) =>
                    old.includes(group.id)
                      ? old.filter((id) => id !== group.id)
                      : [...old, group.id],
                  )
                }
              >
                <span>{group[language]}</span>
                <ChevronDown
                  size={12}
                  className={collapsed.includes(group.id) ? "is-collapsed" : ""}
                />
              </button>
              <div id={`nav-${group.id}`} hidden={collapsed.includes(group.id)}>
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    className={`ah-nav-item ${active === item.id ? "is-active" : ""}`}
                    onClick={() => {
                      onNavigate(item.id);
                      onClose();
                    }}
                    aria-current={active === item.id ? "page" : undefined}
                  >
                    <AhosIcon name={item.icon} size={20} />
                    <span>{item[language]}</span>
                    {item.id === "command" ? (
                      <span className="ah-nav-badge">01</span>
                    ) : item.id === "kian" ? (
                      <span className="ah-nav-ai">AI</span>
                    ) : active === item.id ? (
                      <ChevronLeft size={12} />
                    ) : null}
                  </button>
                ))}
              </div>
            </section>
          ))}
        </nav>
        <div className="ah-sidebar-bottom">
          <div className="ah-safe-mode">
            <AhosIcon name="nav/paper-trading" size={20} />
            <div>
              <strong>
                {fa ? "محیط امن آزمایشی" : "Paper-only workspace"}
              </strong>
              <small>
                {fa ? "بدون اتصال به سرمایهٔ واقعی" : "No real funds connected"}
              </small>
            </div>
            <span className="ah-status-dot" />
          </div>
          <div className="ah-sidebar-foot">
            <span>AHOS CONSOLE</span>
            <span>BUILD 0.1</span>
          </div>
        </div>
      </aside>
    </>
  );
}
