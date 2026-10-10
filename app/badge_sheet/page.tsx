/**
 * M-D3 badge sheet — a DEV-ONLY fixture page, not a dashboard surface.
 *
 * Renders every state of the truth-badge contract in both themes so the styling
 * can be reviewed at a glance. It contains **no data**: every state here is a
 * literal written into this file, watermarked FIXTURE, and the badges are fed by
 * the same `styleFor` the real dashboard uses — so what this page shows is the
 * contract, and only the contract. It cannot misrepresent a token, because it
 * names no token.
 *
 * Reachable at /badge_sheet in dev and in the app window. It is deliberately not
 * linked from the command center: a fixture sheet is a review tool, not a view.
 */

"use client";

import { useState, type ReactNode } from "react";

import {
  BADGE_STATES,
  badgeForState,
  labelFor,
  styleFor,
  worstOf,
} from "@/dashboard_truth_badge";
import { resolveTheme, THEMES, type ThemeName } from "@/dashboard_tokens";
import { TruthBadge } from "@/TruthBadge";

const FIXTURE_STATES: Array<{ state: string; note: string }> = [
  { state: "AVAILABLE", note: "CanonicalReadStatus — the read model is live" },
  { state: "VERIFIED", note: "IdentityState — two independent sources agree" },
  { state: "PASS", note: "SecurityState — the overlay did not veto" },
  { state: "STALE", note: "IdentityState — a measurement that has aged out" },
  { state: "UNAVAILABLE", note: "CanonicalReadStatus — no read model" },
  { state: "UNRESOLVED", note: "IdentityState — not enough independent sources" },
  { state: "INVALID", note: "IdentityState — the sources disagree about validity" },
  { state: "UNSUPPORTED", note: "IdentityState — the chain cannot resolve identity" },
  { state: "INCOMPLETE", note: "SecurityState — the overlay could not finish" },
  { state: "REJECT", note: "SecurityState — the overlay vetoed" },
  { state: "CONFLICT", note: "IdentityState — two sources disagree" },
  { state: "DISAGREEMENT", note: "Council verdict — disagreement is a result" },
  { state: "BUY", note: "CanonicalOutcome — the only positive outcome" },
  { state: "INSUFFICIENT_EVIDENCE", note: "CanonicalOutcome — an abstention, not a result" },
  { state: "SKIP", note: "CanonicalOutcome — unmapped, so UNKNOWN by the fall-through" },
  { state: "NO_TRADE", note: "CanonicalOutcome — unmapped, so UNKNOWN by the fall-through" },
  { state: "SOMETHING_NEW", note: "An enum nobody declares yet — UNKNOWN, never a guess" },
];

function Row({ children, note }: { children: ReactNode; note: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "1rem", padding: "0.45rem 0" }}>
      <div style={{ minWidth: "12rem" }}>{children}</div>
      <code style={{ fontSize: "0.72rem", opacity: 0.6 }}>{note}</code>
    </div>
  );
}

export default function BadgeSheetPage() {
  const [theme, setTheme] = useState<ThemeName>(resolveTheme(null));
  const t = THEMES[theme];
  return (
    <div
      data-theme={theme}
      style={{
        background: "var(--ahos-bg)", color: "var(--ahos-text)",
        fontFamily: "var(--font-vazir), Tahoma, sans-serif",
        minHeight: "100vh", padding: "2rem", direction: "rtl",
      }}
    >
      <header style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.4rem", margin: 0 }}>
          پالت نشان حقیقت — Truth badge palette sheet
        </h1>
        <p style={{ color: "var(--ahos-text-muted)", fontSize: "0.85rem", margin: "0.4rem 0" }}>
          <strong>FIXTURE</strong> — این صفحه فقط برای بازبینی طراحی است و هیچ داده واقعی
          ندارد. / Review tool only; it holds no real data and names no token.
        </p>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {(Object.keys(THEMES) as ThemeName[]).map((name) => (
            <button
              key={name}
              onClick={() => setTheme(name)}
              style={{
                padding: "0.35rem 0.9rem", borderRadius: "0.4rem", cursor: "pointer",
                border: `1px solid ${theme === name ? "var(--ahos-gold)" : "var(--ahos-border)"}`,
                background: theme === name ? "var(--ahos-panel)" : "transparent",
                color: "var(--ahos-text)",
              }}
            >
              {name === "imperial" ? "شاهنشاهی (Imperial)" : "نئون (Neon)"}
            </button>
          ))}
        </div>
      </header>

      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.5rem" }}>پنج حالت — the five states</h2>
        {BADGE_STATES.map((s) => {
          const st = styleFor(s);
          return (
            <Row key={s} note={`${labelFor(s).en} — colour ${st.colorVar}, border ${st.border}`}>
              <TruthBadge state={s} />
            </Row>
          );
        })}
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.5rem" }}>مقادیر واقعی — the real enums</h2>
        {FIXTURE_STATES.map(({ state, note }) => (
          <Row key={state} note={`${state} → ${badgeForState(state)}  ·  ${note}`}>
            <TruthBadge state={state} />
          </Row>
        ))}
      </section>

      <section>
        <h2 style={{ fontSize: "1.05rem", margin: "0 0 0.5rem" }}>
          تقدم — precedence is downgrade-only
        </h2>
        <Row note="worstOf(VERIFIED, DISAGREEMENT)">
          <TruthBadge state={worstOf("VERIFIED", "DISAGREEMENT")} />
        </Row>
        <Row note="worstOf(AVAILABLE, INSUFFICIENT_EVIDENCE)">
          <TruthBadge state={worstOf("AVAILABLE", "INSUFFICIENT_EVIDENCE")} />
        </Row>
        <Row note="worstOf(REJECT, CONFLICT)">
          <TruthBadge state={worstOf("REJECT", "CONFLICT")} />
        </Row>
      </section>

      <footer style={{ marginTop: "2rem", color: "var(--ahos-text-muted)", fontSize: "0.72rem" }}>
        Theme tokens — bg {t.bg} · panel {t.panel} · text {t.text} · gold {t.gold}.
        Status colours are fixed in both themes and never used as decoration (spec §2.3).
      </footer>
    </div>
  );
}
