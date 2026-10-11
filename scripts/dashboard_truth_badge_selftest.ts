/**
 * M-D3 truth badge selftest — the precedence, as an assertion.
 *
 * Run: npm run test:truth-badge
 * Self-test, not independent verification.
 *
 * What this proves is the negative: that no input to this module can dress an
 * unmeasured state as a PASS. VERIFIED has the only success `kind`, the only ✓,
 * the only glow, and the only success sound id, and precedence is
 * downgrade-only — so the assertion is not "the right value comes out" but "there
 * exists no argument that makes a CONFLICT or an UNKNOWN come out success".
 *
 * The real enum values the mapping table is allowed to key on (mission step 1),
 * each read from the module that declares it:
 *
 *   CanonicalReadStatus  canonical_read_model.ts          AVAILABLE UNAVAILABLE STALE
 *   IdentityState        architecture/identity/types.py   VERIFIED CONFLICT UNRESOLVED
 *                                                        INVALID STALE UNSUPPORTED
 *   SecurityState        architecture/security/gate.py    PASS REJECT INCOMPLETE STALE
 *   CanonicalOutcome     architecture/decision/authority.py
 *                                                       BUY WATCH SKIP REJECT
 *                                                       INSUFFICIENT_EVIDENCE HIGH_RISK
 *                                                       MONITOR_ONLY NO_TRADE
 *   council verdict      architecture/knowledge/feedback.py  DISAGREEMENT
 *
 * Only BUY is a positive outcome (`POSITIVE_OUTCOMES = frozenset({BUY})`).
 * CanonicalOutcome's abstentions are absent from the table by design: they are
 * not measurements, so the fall-through to UNKNOWN is their honest rendering.
 * Anything else — any value none of those modules declares — maps to UNKNOWN
 * too, and the "real enums" test below re-reads the declarations and asserts
 * every key is among them, so an invented key cannot slip in.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

import {
  applyFreshness,
  BADGE_STATES,
  badgeForState,
  isUnmeasured,
  labelFor,
  STATE_TO_BADGE,
  STATUS_COLOURS,
  styleFor,
  styleForState,
  worstOf,
} from "../dashboard_truth_badge.ts";
import {
  deriveEdge,
  IMPERIAL,
  NEON,
  resolveTheme,
  THEMES,
  TOKEN_HEXES,
} from "../dashboard_tokens.ts";

const SUCCESS_KIND = "success";
const SUCCESS_SOUND = "verified";

/**
 * None of the four markers the mission names: the VERIFIED colour, the ✓ glyph,
 * the glow class, and the success sound id. An *alert* sound is a different
 * thing — a conflict deserves to be announced, just never celebrated — so what
 * is forbidden here is the success sound specifically.
 */
function assertNeverSuccess(badge: ReturnType<typeof styleFor>): void {
  assert.notEqual(badge.kind, SUCCESS_KIND, "an unmeasured state must not be kind=success");
  assert.notEqual(badge.glyph, "✓", "an unmeasured state must not show the tick");
  assert.equal(badge.glow, false, "an unmeasured state must not glow");
  assert.notEqual(badge.soundId, SUCCESS_SOUND, "an unmeasured state must not carry the success sound");
  assert.ok(
    badge.colorVar !== STATUS_COLOURS.VERIFIED.var,
    "an unmeasured state must not read the verified colour variable",
  );
}

describe("M-D3: VERIFIED is the only success", () => {
  it("is the only state whose kind is success", () => {
    const kinds = new Set(BADGE_STATES.map((s) => styleFor(s).kind));
    assert.equal([...kinds].filter((k) => k === SUCCESS_KIND).length, 1);
    assert.equal(styleFor("VERIFIED").kind, SUCCESS_KIND);
  });

  it("is the only state with the tick and the glow", () => {
    for (const s of BADGE_STATES) {
      const st = styleFor(s);
      const isVerified = s === "VERIFIED";
      assert.equal(st.glyph === "✓", isVerified, `${s}: tick only on VERIFIED`);
      assert.equal(st.glow, isVerified, `${s}: glow only on VERIFIED`);
    }
  });

  it("is the only state that plays the success sound", () => {
    for (const s of BADGE_STATES) {
      if (s === "VERIFIED") continue;
      assert.notEqual(
        styleFor(s).soundId,
        SUCCESS_SOUND,
        `${s}: the success sound id is VERIFIED's alone`,
      );
    }
    assert.equal(styleFor("VERIFIED").soundId, SUCCESS_SOUND);
  });

  it("gives every non-VERIFIED state none of the four success markers", () => {
    for (const s of BADGE_STATES) {
      if (s === "VERIFIED") continue;
      assertNeverSuccess(styleFor(s));
    }
  });

  it("gives UNKNOWN no sound at all — an unmeasured state has nothing to announce", () => {
    // CONFLICT and REJECTED are results (the council: "DISAGREEMENT IS A
    // RESULT"), so they may alert. UNKNOWN is the absence of a measurement and
    // must stay silent: sounding it would present a non-result as an event.
    assert.equal(styleFor("UNKNOWN").soundId, null);
  });

  it("is the only state whose CSS variable is the turquoise", () => {
    for (const s of BADGE_STATES) {
      const isVerified = s === "VERIFIED";
      assert.equal(
        styleFor(s).colorVar === STATUS_COLOURS.VERIFIED.var,
        isVerified,
        `${s} must not read --ahos-status-verified`,
      );
    }
  });
});

describe("M-D3: colour is never the only cue", () => {
  it("gives every state a distinct border treatment", () => {
    const shapes = BADGE_STATES.map((s) => styleFor(s).border);
    assert.equal(new Set(shapes).size, BADGE_STATES.length, "two states share a border shape");
  });

  it("gives every state a glyph, so it reads in monochrome", () => {
    for (const s of BADGE_STATES) {
      assert.ok(styleFor(s).glyph, `${s} has no glyph`);
    }
  });

  it("emits only valid CSS in its fills — a bare custom property name is not", () => {
    // `color-mix(in srgb, --ahos-x 16%, …)` looks plausible and renders nothing;
    // every variable used in a fill must be wrapped in var(). Caught here because
    // a broken fill is invisible in a unit test and visible only as a missing
    // tint in the browser.
    for (const s of BADGE_STATES) {
      const f = styleFor(s).fill;
      if (f === "none") continue;
      assert.ok(
        !/--ahos-[a-z-]+(?!\s*\))/.test(f.replace(/var\(--ahos-[a-z-]+\)/g, "")),
        `${s}'s fill names a CSS variable without var()`,
      );
      assert.ok(
        f.includes(`var(${styleFor(s).colorVar})`),
        `${s}'s fill must use its own colour variable`,
      );
    }
  });

  it("uses the spec's palette for every state", () => {
    for (const s of BADGE_STATES) {
      assert.equal(STATUS_COLOURS[s].var, `--ahos-status-${s.toLowerCase()}`);
    }
  });
});

describe("M-D3: the real enums map honestly", () => {
  it("canonicalUnavailable is UNKNOWN, never VERIFIED", () => {
    assert.equal(badgeForState("UNAVAILABLE"), "UNKNOWN");
  });

  it("canonical AVAILABLE is VERIFIED", () => {
    assert.equal(badgeForState("AVAILABLE"), "VERIFIED");
  });

  it("a single source is UNKNOWN — one source is not a measurement", () => {
    assert.equal(badgeForState("UNRESOLVED"), "UNKNOWN");   // the two-source arbiter
    assert.equal(badgeForState("INVALID"), "UNKNOWN");
    assert.equal(badgeForState("UNSUPPORTED"), "UNKNOWN");
  });

  it("a security PASS is the only verdict that becomes VERIFIED", () => {
    assert.equal(badgeForState("PASS"), "VERIFIED");
    assert.equal(badgeForState("INCOMPLETE"), "UNKNOWN");
  });

  it("a security rejection is REJECTED", () => {
    assert.equal(badgeForState("REJECT"), "REJECTED");
  });

  it("a council disagreement is CONFLICT — disagreement is a result", () => {
    assert.equal(badgeForState("DISAGREEMENT"), "CONFLICT");
  });

  it("an abstention is UNKNOWN, never a verification", () => {
    // CanonicalOutcome's SKIP / MONITOR_ONLY / NO_TRADE are deliberately absent
    // from the table; the fall-through to UNKNOWN is the honest rendering.
    assert.equal(badgeForState("SKIP"), "UNKNOWN");
    assert.equal(badgeForState("MONITOR_ONLY"), "UNKNOWN");
    assert.equal(badgeForState("NO_TRADE"), "UNKNOWN");
    assert.equal(badgeForState("HIGH_RISK"), "UNKNOWN");
  });

  it("an unrecognised enum is UNKNOWN — never a guess", () => {
    assert.equal(badgeForState("TOTALLY_NEW_STATUS"), "UNKNOWN");
    assert.equal(badgeForState("verified"), "VERIFIED");   // case-insensitive, exact word
    assert.equal(badgeForState("VERIFIED_OK"), "UNKNOWN"); // a near-miss is still unrecognised
  });

  it("maps every key it declares to a real enum in the authority chain", () => {
    // The table must not invent vocabulary. Every key is a value that is
    // actually declared in one of the four sources named in the docstring; this
    // reads those declarations and asserts membership, so a fabricated key is
    // caught here rather than presented as a mapping of something real.
    const declared = new Set<string>();
    for (const py of [
      "architecture/identity/types.py",
      "architecture/security/gate.py",
      "architecture/decision/authority.py",
      "architecture/knowledge/feedback.py",
    ]) {
      const text = readFileSync(new URL(`../${py}`, import.meta.url), "utf8");
      for (const m of text.matchAll(/=\s*"([A-Z][A-Z0-9_]{2,})"/g)) declared.add(m[1]!);
    }
    const ts = readFileSync(
      new URL("../canonical_read_model.ts", import.meta.url), "utf8");
    for (const m of ts.matchAll(/"([A-Z][A-Z0-9_]{2,})"/g)) declared.add(m[1]!);

    for (const key of Object.keys(STATE_TO_BADGE)) {
      assert.ok(
        declared.has(key),
        `STATE_TO_BADGE key ${key} is not an enum value the authority chain declares`,
      );
    }
  });

  it("absent, empty and non-string states are UNKNOWN", () => {
    assert.equal(badgeForState(null), "UNKNOWN");
    assert.equal(badgeForState(undefined), "UNKNOWN");
    assert.equal(badgeForState(""), "UNKNOWN");
    assert.equal(badgeForState("   "), "UNKNOWN");
    assert.equal(badgeForState(42 as never), "UNKNOWN");
  });

  it("labels every state in both languages", () => {
    for (const s of BADGE_STATES) {
      const l = labelFor(s);
      assert.ok(l.en, `${s} has no English label`);
      assert.ok(l.fa, `${s} has no Persian label`);
    }
  });
});

describe("M-D3: precedence is downgrade-only", () => {
  it("disagreement beats a VERIFIED in the same view", () => {
    assert.equal(worstOf("VERIFIED", "DISAGREEMENT"), "CONFLICT");
    assert.equal(worstOf("DISAGREEMENT", "VERIFIED"), "CONFLICT");
  });

  it("a REJECTED and a CONFLICT together show CONFLICT, never the upgrade", () => {
    // REJECTED is the more severe, so it wins — but the point is the direction:
    // neither input can pull the other up to VERIFIED.
    assert.equal(worstOf("REJECTED", "CONFLICT"), "REJECTED");
    assert.equal(worstOf("CONFLICT", "VERIFIED"), "CONFLICT");
  });

  it("an UNKNOWN with a VERIFIED is UNKNOWN", () => {
    assert.equal(worstOf("VERIFIED", "UNAVAILABLE"), "UNKNOWN");
    assert.equal(worstOf("AVAILABLE", "INSUFFICIENT_EVIDENCE"), "UNKNOWN");
  });
  it("never returns VERIFIED when any input is unmeasured", () => {
    // The exhaustive proof over the whole cartesian product would be noise; the
    // invariant is that a severe input can never be outvoted, so check the
    // boundary against every other state.
    for (const severe of ["REJECTED", "CONFLICT", "UNKNOWN", "STALE"] as const) {
      for (const other of BADGE_STATES) {
        assert.notEqual(worstOf(severe, other), "VERIFIED", `${severe} + ${other} must not verify`);
        assert.notEqual(worstOf(other, severe), "VERIFIED", `${other} + ${severe} must not verify`);
      }
    }
  });

  it("two verifications still verify", () => {
    assert.equal(worstOf("AVAILABLE", "PASS"), "VERIFIED");
    assert.equal(worstOf(), "VERIFIED", "no evidence at all is vacuously VERIFIED — call it with states");
  });

  it("isUnmeasured names exactly the states the display may never upgrade", () => {
    assert.equal(isUnmeasured("UNKNOWN"), true);
    assert.equal(isUnmeasured("CONFLICT"), true);
    assert.equal(isUnmeasured("REJECTED"), true);
    assert.equal(isUnmeasured("STALE"), false);
    assert.equal(isUnmeasured("VERIFIED"), false);
  });
});

describe("M-D3: a stale verification is not a verification", () => {
  it("a VERIFIED whose evidence went stale shows STALE", () => {
    assert.equal(applyFreshness("AVAILABLE", "STALE"), "STALE");
    assert.equal(applyFreshness("PASS", "STALE"), "STALE");
  });

  it("a VERIFIED whose freshness is unknown shows UNKNOWN", () => {
    assert.equal(applyFreshness("AVAILABLE", "UNKNOWN"), "UNKNOWN");
  });

  it("a VERIFIED whose freshness violated shows REJECTED", () => {
    assert.equal(applyFreshness("AVAILABLE", "VIOLATION"), "REJECTED");
  });

  it("a fresh VERIFIED stays VERIFIED", () => {
    assert.equal(applyFreshness("AVAILABLE", "OK"), "VERIFIED");
  });

  it("never upgrades: an UNKNOWN stays UNKNOWN whatever the freshness says", () => {
    assert.equal(applyFreshness("UNAVAILABLE", "OK"), "UNKNOWN");
    assert.equal(applyFreshness("INSUFFICIENT_EVIDENCE", "OK"), "UNKNOWN");
    assert.equal(applyFreshness(null, "OK"), "UNKNOWN");
  });

  it("a stale UNKNOWN is not laundered into a STALE that reads as a warning", () => {
    // UNKNOWN is already below STALE in precedence; freshness must not move it.
    assert.equal(applyFreshness("UNAVAILABLE", "STALE"), "UNKNOWN");
  });

  it("styleForState maps straight through", () => {
    assert.equal(styleForState("DISAGREEMENT").state, "CONFLICT");
    assert.equal(styleForState("UNRESOLVED").state, "UNKNOWN");
    assert.equal(styleForState("REJECT").state, "REJECTED");
    assert.equal(styleForState("AVAILABLE").kind, "success");
  });
});

describe("M-D3: the tokens are the spec's", () => {
  it("carries every hex the spec gives", () => {
    for (const hex of [
      "#0B0709", "#160E12", "#3A2A1C", "#EFE4CC", "#A99A80", "#D4AF5A",
      "#F1D58E", "#9E1C26", "#D2343E", "#E8834A",
      "#040714", "#0A1330", "#E6F6FF", "#8FA6C8", "#3FD0FF", "#4C82FF",
    ]) {
      assert.ok(TOKEN_HEXES.has(hex), `spec hex ${hex} missing from the token table`);
    }
  });

  it("gold is the same hex in both themes, as the spec gives it twice", () => {
    assert.equal(IMPERIAL.gold, NEON.gold);
    assert.equal(IMPERIAL.gold, "#D4AF5A");
  });

  it("resolves to the owner-approved default", () => {
    assert.equal(resolveTheme("imperial"), "imperial");
    assert.equal(resolveTheme("neon"), "neon");
    assert.equal(resolveTheme(null), "imperial");
    assert.equal(resolveTheme("vaporwave"), "imperial");
  });

  it("declares the spec's status palette once, for both themes", () => {
    assert.equal(STATUS_COLOURS.VERIFIED.hex, "#2EC4A6");
    assert.equal(STATUS_COLOURS.UNKNOWN.hex, "#9AA3B2");
    assert.equal(STATUS_COLOURS.CONFLICT.hex, "#E07BE8");
    assert.equal(STATUS_COLOURS.STALE.hex, "#B8A27A");
    assert.equal(STATUS_COLOURS.REJECTED.hex, "#FF5A4E");
  });

  it("derives a hairline only where the spec is silent, and stays in-family", () => {
    // Neon has no panel-edge row in §2.2, so its edge is derived.
    assert.equal(NEON.panelEdge, null);
    const edge = deriveEdge(NEON.panel, NEON.text);
    assert.equal(edge, "#2B354F");
    // Imperial has one, so the spec's value stands and is never derived over.
    assert.equal(IMPERIAL.panelEdge, "#3A2A1C");
  });

  it("names the same theme set the CSS switches on", () => {
    assert.deepEqual(Object.keys(THEMES).sort(), ["imperial", "neon"]);
  });
});

describe("M-D3: the stylesheet agrees with the tables", () => {
  const css = readFileSync(new URL("../globals.css", import.meta.url), "utf8");

  it("defines the status palette at the spec's hexes", () => {
    for (const s of BADGE_STATES) {
      assert.ok(
        css.includes(`--ahos-status-${s.toLowerCase()}: ${STATUS_COLOURS[s].hex};`),
        `globals.css must define --ahos-status-${s.toLowerCase()} at the spec hex`,
      );
    }
  });

  it("declares the two themes the token table declares", () => {
    assert.ok(css.includes(`[data-theme="imperial"]`), "no imperial block");
    assert.ok(css.includes(`[data-theme="neon"]`), "no neon block");
    for (const [name, tokens] of Object.entries(THEMES)) {
      assert.ok(css.includes(`--ahos-bg: ${tokens.bg};`), `${name} bg missing from CSS`);
      assert.ok(css.includes(`--ahos-panel: ${tokens.panel};`), `${name} panel missing from CSS`);
    }
  });

  it("uses the spec's Imperial edge and marks the Neon edge derived", () => {
    assert.ok(css.includes("--ahos-border: #3A2A1C;"), "Imperial's spec edge must be the CSS value");
    assert.ok(css.includes("--ahos-border: #2B354F;"), "Neon's derived edge must be the CSS value");
    assert.ok(/DERIVED/.test(css), "the derivation must be documented in the stylesheet");
  });

  it("styles the non-colour cue for every state", () => {
    assert.ok(css.includes("truth-badge--ok"), "missing the VERIFIED modifier");
    assert.ok(css.includes("truth-badge--stale"), "missing the STALE modifier");
    assert.ok(css.includes("truth-badge--unknown"), "missing the UNKNOWN modifier");
    assert.ok(css.includes("truth-badge--conflict"), "missing the CONFLICT modifier");
    assert.ok(css.includes("truth-badge--rejected"), "missing the REJECTED modifier");
    assert.ok(css.includes("truth-badge--glow"), "missing the glow treatment");
  });
});

describe("M-D5.F: the badge's label is solid and legible", () => {
  // Owner QA (M-D5.5 item 1): the top-left chip read as struck-through. The
  // cause was §2.3's fill painted as the *badge's* background — the 45° hatch of
  // an UNKNOWN crossed the Persian word behind the glyph strokes. The pattern is
  // a cue and may not be a text background; this keeps it on a swatch.
  const css = readFileSync(new URL("../globals.css", import.meta.url), "utf8");
  const tsx = readFileSync(new URL("../TruthBadge.tsx", import.meta.url), "utf8");

  /** WCAG relative luminance, for the contrast floor M-D5.F sets. */
  const luminance = (hex: string): number => {
    const channels = [1, 3, 5].map((at) => {
      const c = Number.parseInt(hex.slice(at, at + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0]! + 0.7152 * channels[1]! + 0.0722 * channels[2]!;
  };
  const contrast = (a: string, b: string): number => {
    const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (hi + 0.05) / (lo + 0.05);
  };

  it("never paints §2.3's fill as the badge's own background", () => {
    const start = css.indexOf(".truth-badge {");
    assert.ok(start > -1, "no .truth-badge rule to guard");
    // The base rule is flat, so the first closing brace after it ends it.
    const rule = css.slice(start, css.indexOf("}", start));
    assert.ok(!rule.includes("--badge-fill"), "the badge root must not carry the fill");
    assert.ok(rule.includes("background: transparent"), "the badge root must be transparent");
  });

  it("gives the fill a swatch and the label a span of its own", () => {
    assert.ok(css.includes(".truth-badge__fill"), "missing the swatch rule");
    assert.ok(css.includes("var(--badge-fill, transparent)"), "the swatch must read the fill var");
    assert.ok(css.includes(".truth-badge__label"), "missing the label rule");
    assert.ok(tsx.includes('className="truth-badge__fill"'), "the component renders the swatch");
    assert.ok(tsx.includes('className="truth-badge__label"'), "the component wraps the label");
  });

  it("keeps every state's label at 4.5:1 or better on both theme surfaces", () => {
    for (const state of BADGE_STATES) {
      for (const [name, tokens] of Object.entries(THEMES)) {
        for (const surface of [tokens.bg, tokens.panel]) {
          const ratio = contrast(STATUS_COLOURS[state].hex, surface);
          assert.ok(
            ratio >= 4.5,
            `${state}'s label on the ${name} ${surface === tokens.bg ? "bg" : "panel"} is ${ratio.toFixed(2)}:1, under 4.5:1`,
          );
        }
      }
    }
  });
});
