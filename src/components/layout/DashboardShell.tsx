"use client";
import { tr } from "../../lib/i18n";
import { AhosIcon } from "../icons";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ArrowUpLeft, Check, Circle, Command, Crosshair, LockKeyhole, PanelRightOpen, Radar, Sparkles } from "lucide-react";
import {
  allItems,
  stageModules,
  type Language,
  type Quality,
} from "../../lib/navigation";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "./CommandPalette";
import { StarMark } from "../ui/Brand";
import { CommandDashboard } from "../dashboard/CommandDashboard";
import { AppLegalFooter } from "./AppLegalFooter";

type Preferences = { language: Language; quality: Quality; muted: boolean };
const defaultPreferences: Preferences = {
  language: "fa",
  quality: "balanced",
  muted: true,
};
const storageKey = "ahos.shell.preferences.v1";
export default function DashboardShell({
  activeId,
  children,
}: {
  /** Route mode: id of the nav item this route represents. */
  activeId?: string;
  /** Route mode: page content rendered in place of the dashboard body. */
  children?: ReactNode;
} = {}) {
  const router = useRouter();
  const [preferences, setPreferences] =
    useState<Preferences>(defaultPreferences);
  const [active, setActive] = useState(activeId ?? "command");
  const [searchOpen, setSearchOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [storageWarning, setStorageWarning] = useState(false);
  const { language, quality, muted } = preferences;
  const fa = language === "fa";
  const selected = allItems.find((item) => item.id === active) ?? allItems[0];
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      try {
        const saved: Partial<Preferences> = JSON.parse(
          localStorage.getItem(storageKey) ?? "{}",
        );
        setPreferences({
          language: saved.language === "en" ? "en" : "fa",
          quality: ["high", "balanced", "low"].includes(saved.quality ?? "")
            ? (saved.quality as Quality)
            : "balanced",
          muted: typeof saved.muted === "boolean" ? saved.muted : true,
        });
      } catch {
        setStorageWarning(true);
      }
    });
    return () => cancelAnimationFrame(frame);
  }, []);
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = fa ? "rtl" : "ltr";
  }, [language, fa]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  function navigate(id: string) {
    const item = allItems.find((entry) => entry.id === id);
    if (item?.href) {
      router.push(item.href);
      return;
    }
    if (children) {
      router.push("/arena");
      return;
    }
    setActive(id);
  }
  function updatePreferences(patch: Partial<Preferences>) {
    const next = { ...preferences, ...patch };
    setPreferences(next);
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      setStorageWarning(true);
    }
  }
  function toggleMute() {
    updatePreferences({ muted: !muted });
    if (muted && typeof window.AudioContext !== "undefined") {
      try {
        const context = new AudioContext();
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(640, context.currentTime);
        gain.gain.setValueAtTime(0, context.currentTime);
        gain.gain.linearRampToValueAtTime(0.035, context.currentTime + 0.015);
        gain.gain.exponentialRampToValueAtTime(
          0.001,
          context.currentTime + 0.18,
        );
        oscillator.connect(gain);
        gain.connect(context.destination);
        oscillator.start();
        oscillator.stop(context.currentTime + 0.2);
        oscillator.onended = () => {
          oscillator.disconnect();
          gain.disconnect();
          void context.close();
        };
      } catch {
        /* Audio is optional; never prevent navigation when unavailable. */
      }
    }
  }
  return (
    <div className="ah-shell" data-quality={quality}>
      <a className="ah-skip-link" href="#main-content">
        {fa ? "رفتن به محتوای اصلی" : "Skip to content"}
      </a>
      <Sidebar
        language={language}
        active={active}
        onNavigate={navigate}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="ah-main-shell" dir={fa ? "rtl" : "ltr"}>
        <Topbar
          language={language}
          setLanguage={(value) => updatePreferences({ language: value })}
          quality={quality}
          setQuality={(value) => updatePreferences({ quality: value })}
          muted={muted}
          toggleMute={toggleMute}
          onSearch={() => setSearchOpen(true)}
          onMenu={() => setSidebarOpen(true)}
          onSettings={() => setActive("settings")}
        />
        <main id="main-content" className="ah-main" tabIndex={-1}>
          <div className="ah-page-heading">
            <div>
              <div className="ah-breadcrumb">
                <span>AHOS</span>
                <span>/</span>
                <span>{fa ? "فضای کاری" : "Workspace"}</span>
                <span>/</span>
                <span>{selected[language]}</span>
              </div>
              <h1>
                {selected[language]}
                <span className="ah-heading-dot" />
              </h1>
              <p>
                {fa
                  ? "نگاهی یکپارچه. تصمیمی آگاهانه. آینده‌ای روشن‌تر."
                  : "A connected perspective. An informed decision. A clearer future."}
              </p>
            </div>
            <div className="ah-page-actions">
              <span className="ah-chip ah-chip-gold">
                <AhosIcon name="nav/paper-trading" size={14} /> {fa ? tr("fa", "paper.badge") : "PAPER ONLY"}
              </span>
              <button
                className="ah-secondary-button"
                onClick={() => setSearchOpen(true)}
              >
                <Command size={14} />
                {fa ? "دسترسی سریع" : "Quick access"}
              </button>
            </div>
          </div>
          {storageWarning && (
            <p role="status" className="ah-warning">
              {fa
                ? "ذخیره‌سازی مرورگر در دسترس نیست؛ تنظیمات فقط در این نشست حفظ می‌شوند."
                : "Browser storage is unavailable. Preferences apply to this session only."}
            </p>
          )}
          {children ? (
            children
          ) : active === "command" ? (
            <CommandDashboard language={language} quality={quality} />
          ) : (
            <>
              <section
                className="ah-welcome-panel"
                aria-labelledby="welcome-heading"
              >
                <div className="ah-welcome-copy">
                  <div className="ah-eyebrow">
                    <span /> INTELLIGENCE, WITH INTENTION
                  </div>
                  <h2 id="welcome-heading">
                    {fa ? (
                      <>
                        جهان پیچیده است.
                        <br />
                        دید شما، <em>شفاف.</em>
                      </>
                    ) : (
                      <>
                        A complex world.
                        <br />A <em>clearer</em> perspective.
                      </>
                    )}
                  </h2>
                  <p>
                    {fa
                      ? "به فضای فرماندهی AHOS خوش آمدید؛ محیطی برای پیوند داده، پژوهش و هوش مصنوعی — با شواهد در مرکز هر تصمیم."
                      : "Welcome to the AHOS command workspace. A place for data, research and AI — with evidence at the heart of every decision."}
                  </p>
                  <div className="ah-welcome-actions">
                    <button
                      className="ah-gold-button"
                      onClick={() => setSearchOpen(true)}
                    >
                      {fa ? "کاوش در فضای کاری" : "Explore workspace"}
                      <ArrowUpLeft size={16} />
                    </button>
                    <span>
                      <LockKeyhole size={12} />
                      {fa
                        ? "فقط شبیه‌سازی · بدون سرمایهٔ واقعی"
                        : "Simulation only · No real funds"}
                    </span>
                  </div>
                </div>
                <div className="ah-orbital-art" aria-hidden="true">
                  <div className="ah-orbit-grid" />
                  <div className="ah-orbit ah-orbit-outer" />
                  <div className="ah-orbit ah-orbit-middle" />
                  <div className="ah-orbit ah-orbit-inner" />
                  <div className="ah-orbit-cross ah-orbit-cross-h" />
                  <div className="ah-orbit-cross ah-orbit-cross-v" />
                  <div className="ah-orbit-core">
                    <StarMark />
                    <span>AHOS</span>
                    <small>CONNECTED INTELLIGENCE</small>
                  </div>
                  <span className="ah-coordinate ah-coordinate-top">
                    35.6892° N / 51.3890° E
                  </span>
                  <span className="ah-coordinate ah-coordinate-bottom">
                    HUMAN · EVIDENCE · INTELLIGENCE
                  </span>
                  <span className="ah-orbit-node ah-node-one" />
                  <span className="ah-orbit-node ah-node-two" />
                  <span className="ah-orbit-node ah-node-three" />
                </div>
                <div className="ah-welcome-bottom">
                  <span>
                    <Crosshair size={13} />
                    {fa
                      ? "طراحی‌شده برای دیدن تصویر بزرگ‌تر"
                      : "DESIGNED TO SEE THE BIGGER PICTURE"}
                  </span>
                  <span>AHOS / CONSOLE 001</span>
                </div>
              </section>
              <div className="ah-section-heading">
                <h2>{fa ? "زیرساخت تجربه" : "Workspace foundation"}</h2>
                <span>
                  {fa ? "مرحلهٔ ۰۱ از مسیر ساخت" : "BUILD STAGE 01"}
                  <span className="ah-hairline" />
                </span>
              </div>
              <div className="ah-foundation-grid">
                <section className="ah-foundation-card">
                  <div className="ah-card-title">
                    <span className="ah-card-icon">
                      <PanelRightOpen size={19} />
                    </span>
                    <h3>{fa ? "پوستهٔ فرماندهی" : "Command shell"}</h3>
                    <span className="ah-chip">STAGE 01</span>
                  </div>
                  <p>
                    {fa
                      ? "زیرساخت رابط آماده است. داده‌ها، نمودارها و صفحات تخصصی در مراحل بعد پیاده‌سازی می‌شوند."
                      : "The interface foundation is in place. Data, charts and specialist pages will be implemented in subsequent stages."}
                  </p>
                  <div className="ah-checklist">
                    {(fa
                      ? [
                          "چیدمان راست‌به‌چپ و قلم‌های محلی",
                          "ناوبری گروه‌بندی‌شده و جست‌وجوی سریع",
                          "تنظیمات پایدارِ زبان، کیفیت و صدا",
                        ]
                      : [
                          "RTL layout and locally bundled fonts",
                          "Grouped navigation and command search",
                          "Persistent language, quality and sound",
                        ]
                    ).map((label) => (
                      <div key={label}>
                        <span>
                          <Check size={12} />
                        </span>
                        {label}
                      </div>
                    ))}
                  </div>
                  <footer>
                    <span>
                      {fa
                        ? "منبع: وضعیت پیاده‌سازی رابط"
                        : "Source: interface implementation"}
                    </span>
                    <span className="ah-text-gold">LOCAL</span>
                  </footer>
                </section>
                <section className="ah-foundation-card ah-roadmap">
                  <div className="ah-card-title">
                    <span className="ah-card-icon">
                      <Radar size={19} />
                    </span>
                    <h3>{fa ? "افق بعدی" : "On the horizon"}</h3>
                    <span className="ah-chip">PLANNED</span>
                  </div>
                  <div className="ah-module-grid">
                    {stageModules.map((module) => (
                      <div className="ah-module" key={module.en}>
                        <AhosIcon name={module.icon} size={21} />
                        <div>
                          <strong>{module[language]}</strong>
                          <small>{module.sub}</small>
                        </div>
                        <Circle size={7} />
                      </div>
                    ))}
                  </div>
                  <footer>
                    <span>
                      {fa
                        ? "این ماژول‌ها هنوز متصل یا اجرا نشده‌اند"
                        : "These modules are not connected or running"}
                    </span>
                    <Sparkles size={13} />
                  </footer>
                </section>
              </div>
              {!children && active !== "command" && (
                <section className="ah-selection-notice" aria-live="polite">
                  <AhosIcon name={selected.icon} size={20} />
                  <div>
                    <h3>{selected[language]}</h3>
                    <p>
                      {fa
                        ? "بخش انتخاب شد. صفحهٔ تخصصی این بخش در مراحل بعد ساخته می‌شود؛ در این مرحله فقط پوسته و کنترل‌های محیط فعال‌اند."
                        : "Section selected. Its dedicated page is scheduled for a later stage. Only the shell and workspace controls are implemented now."}
                    </p>
                  </div>
                  <span className="ah-chip">PLANNED</span>
                </section>
              )}
            </>
          )}
          <footer className="ah-main-footer">
            <AppLegalFooter language={language} />
          </footer>
        </main>
      </div>
      <CommandPalette
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        onNavigate={navigate}
        language={language}
      />
    </div>
  );
}
