"use client";
import { useEffect, useState } from "react";
import {
  Bell,
  ChevronDown,
  Command,
  Menu,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Volume2,
  VolumeX,
} from "lucide-react";
import type { Language, Quality } from "../../lib/navigation";

type Props = {
  language: Language;
  setLanguage: (value: Language) => void;
  quality: Quality;
  setQuality: (value: Quality) => void;
  muted: boolean;
  toggleMute: () => void;
  onSearch: () => void;
  onMenu: () => void;
  onSettings: () => void;
};
function Clock({
  zone,
  label,
  date,
}: {
  zone?: string;
  label: string;
  date: Date | null;
}) {
  return (
    <div className="ah-clock">
      <span>{label}</span>
      <time>
        {date
          ? new Intl.DateTimeFormat("en-GB", {
              timeZone: zone,
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
            }).format(date)
          : "––:––"}
      </time>
    </div>
  );
}
export function Topbar({
  language,
  setLanguage,
  quality,
  setQuality,
  muted,
  toggleMute,
  onSearch,
  onMenu,
  onSettings,
}: Props) {
  const fa = language === "fa";
  const [date, setDate] = useState<Date | null>(null);
  const [popover, setPopover] = useState<"notifications" | "user" | null>(null);
  useEffect(() => {
    const update = () => setDate(new Date());
    update();
    const timer = setInterval(update, 30000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!popover) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPopover(null);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [popover]);
  return (
    <header className="ah-topbar">
      <button
        className="ah-icon-button ah-mobile-only"
        aria-label={fa ? "باز کردن فهرست" : "Open menu"}
        aria-controls="primary-sidebar"
        onClick={onMenu}
      >
        <Menu size={20} />
      </button>
      <button className="ah-search-trigger" onClick={onSearch}>
        <Search size={17} />
        <span>
          {fa ? "جست‌وجو در جهان AHOS..." : "Search the AHOS universe…"}
        </span>
        <kbd dir="ltr">
          <Command size={11} /> K
        </kbd>
      </button>
      <div className="ah-clocks" dir="ltr">
        <Clock zone="Asia/Tehran" label="TEHRAN" date={date} />
        <Clock zone="UTC" label="UTC" date={date} />
        <Clock label="LOCAL" date={date} />
      </div>
      <div className="ah-toolbar">
        <label
          className="ah-quality"
          title={fa ? "کیفیت نمایش" : "Visual quality"}
        >
          <SlidersHorizontal size={14} />
          <select
            aria-label={fa ? "کیفیت نمایش" : "Visual quality"}
            value={quality}
            onChange={(event) => setQuality(event.target.value as Quality)}
          >
            <option value="high">{fa ? "کیفیت بالا" : "High"}</option>
            <option value="balanced">{fa ? "متعادل" : "Balanced"}</option>
            <option value="low">{fa ? "سبک" : "Low"}</option>
          </select>
        </label>
        <button
          className="ah-language"
          onClick={() => setLanguage(fa ? "en" : "fa")}
          aria-label={fa ? "Switch to English" : "تغییر به فارسی"}
        >
          <span className={fa ? "selected" : ""}>FA</span>
          <span>/</span>
          <span className={!fa ? "selected" : ""}>EN</span>
        </button>
        <button
          className="ah-icon-button"
          onClick={toggleMute}
          aria-pressed={!muted}
          aria-label={
            fa
              ? muted
                ? "فعال‌سازی صدای رابط"
                : "بی‌صدا کردن"
              : muted
                ? "Enable interface sound"
                : "Mute sound"
          }
          title={fa ? "صدای رابط" : "Interface sound"}
        >
          {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
        </button>
        <div className="ah-popover-anchor">
          <button
            className={`ah-icon-button ${popover === "notifications" ? "is-selected" : ""}`}
            aria-label={fa ? "اعلان‌ها" : "Notifications"}
            aria-expanded={popover === "notifications"}
            onClick={() =>
              setPopover((old) =>
                old === "notifications" ? null : "notifications",
              )
            }
          >
            <Bell size={18} />
          </button>
          {popover === "notifications" && (
            <>
              <button
                className="ah-popover-dismiss"
                aria-label="Close notifications"
                onClick={() => setPopover(null)}
              />
              <section className="ah-popover">
                <h3>{fa ? "مرکز اعلان‌ها" : "Notifications"}</h3>
                <div className="ah-empty-icon">
                  <Bell size={24} />
                </div>
                <strong>
                  {fa ? "اعلان جدیدی ندارید" : "No new notifications"}
                </strong>
                <p>
                  {fa
                    ? "هیچ منبع دادهٔ زنده‌ای متصل نیست. اعلان‌های بازار در مراحل بعد اضافه می‌شوند."
                    : "No live data sources are connected. Market notifications arrive in a later stage."}
                </p>
                <span className="ah-chip">OFFLINE</span>
              </section>
            </>
          )}
        </div>
        <div className="ah-topbar-divider" />
        <div className="ah-popover-anchor">
          <button
            className="ah-user"
            aria-expanded={popover === "user"}
            onClick={() =>
              setPopover((old) => (old === "user" ? null : "user"))
            }
          >
            <span className="ah-avatar">M</span>
            <span className="ah-user-text">
              <strong>{fa ? "مهرداد" : "Mehrdad"}</strong>
              <small>{fa ? "فضای نمایشی" : "Demo workspace"}</small>
            </span>
            <ChevronDown size={12} />
          </button>
          {popover === "user" && (
            <>
              <button
                className="ah-popover-dismiss"
                aria-label="Close user menu"
                onClick={() => setPopover(null)}
              />
              <section className="ah-popover ah-user-popover">
                <h3>{fa ? "پروفایل محلی" : "Local profile"}</h3>
                <p>
                  {fa
                    ? "این پروفایل نمایشی است؛ ورود به حساب انجام نشده."
                    : "Display profile only. You are not signed in."}
                </p>
                <button
                  className="ah-secondary-button"
                  onClick={() => {
                    onSettings();
                    setPopover(null);
                  }}
                >
                  {fa ? "تنظیمات محیط" : "Workspace settings"}
                </button>
              </section>
            </>
          )}
        </div>
      </div>
      <div className="ah-sessionbar">
        <div className="ah-session-label">
          <ShieldCheck size={13} />
          <span>PAPER ONLY</span>
          <i />
          <span>
            {fa
              ? "محیط مستقل · بدون اتصال زنده"
              : "LOCAL WORKSPACE · NO LIVE CONNECTION"}
          </span>
        </div>
        <div className="ah-sessions">
          <span>{fa ? "جلسات بازار" : "SESSIONS"}</span>
          {["ASIA", "EUROPE", "US"].map((market) => (
            <span className="ah-session-pill" key={market}>
              {market}
              <span>UNKNOWN</span>
            </span>
          ))}
        </div>
      </div>
    </header>
  );
}
