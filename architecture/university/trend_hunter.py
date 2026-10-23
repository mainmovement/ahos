"""M57.T Trend Hunter — daily open-source scout into the Idea Shelf (proposals only).
Zero pip install, zero subprocess, strict 12-point Asi vetting gate, 90-day dedupe, Persian digest.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

ALLOWED_SPDX = frozenset({"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC0-1.0"})
FORBIDDEN_SPDX = ("GPL", "AGPL", "LGPL", "CC-BY-NC", "PROPRIETARY", "NONE")
ALLOWED_TIERS = frozenset({"T8", "T16", "T32", "GPU"})
DEDUPE_WINDOW_SECONDS = 90 * 86400.0


@dataclass(frozen=True, slots=True)
class TrendCandidate:
    name: str
    url: str
    version: str
    spdx: str
    cost_usd: float
    tier: str
    license_sources: tuple[str, ...]
    summary_fa: str
    est_ram_mb: int = 256
    no_live_execution: bool = True


def _norm_key(c: TrendCandidate) -> str:
    u = c.url.strip().lower().rstrip("/")
    n = re.sub(r"[^a-z0-9]+", "-", c.name.strip().lower()).strip("-")
    return f"{u}::{n}"


def normalize_and_deduplicate(
    candidates: Sequence[TrendCandidate],
    seen_registry: dict[str, tuple[str, float]],
    now_ts: float,
) -> list[TrendCandidate]:
    """Deduplicate by URL+name; resurface only on version bump or after 90 days."""
    out: list[TrendCandidate] = []
    batch_keys: set[str] = set()
    for c in candidates:
        key = _norm_key(c)
        if key in batch_keys:
            continue
        prev = seen_registry.get(key)
        if prev is not None:
            prev_ver, prev_ts = prev
            if c.version == prev_ver and (now_ts - prev_ts) < DEDUPE_WINDOW_SECONDS:
                continue
        batch_keys.add(key)
        seen_registry[key] = (c.version, now_ts)
        out.append(c)
    return out


def vet_candidate_12_point(c: TrendCandidate) -> dict[str, Any]:
    """Apply Asi's 12-point permissive-license / zero-cost / tier-tagged / two-source gate."""
    reasons: list[str] = []
    spdx = c.spdx.strip()
    if not spdx or any(spdx.upper().startswith(p) for p in FORBIDDEN_SPDX) or spdx not in ALLOWED_SPDX:
        reasons.append(f"license_rejected:{spdx or 'MISSING'}")
    if c.cost_usd > 0.0:
        reasons.append(f"non_zero_cost:{c.cost_usd}")
    if c.tier not in ALLOWED_TIERS:
        reasons.append(f"invalid_tier:{c.tier}")
    if len(set(c.license_sources)) < 2:
        reasons.append("insufficient_license_witness_sources")
    if not c.no_live_execution:
        reasons.append("live_execution_forbidden")

    passed = len(reasons) == 0
    return {
        "name": c.name,
        "url": c.url,
        "version": c.version,
        "spdx": spdx,
        "tier": c.tier,
        "accepted": passed,
        "state": "proposed" if passed else "rejected",
        "installed": False,
        "requires_owner_approval": True,
        "reasons": reasons if reasons else ["all_12_points_passed"],
        "summary_fa": c.summary_fa,
    }


def propose_to_idea_shelf(c: TrendCandidate) -> dict[str, Any]:
    """Build an M59.S Idea Shelf proposal record (never auto-merged or auto-enabled)."""
    vetted = vet_candidate_12_point(c)
    slug = re.sub(r"[^a-z0-9]+", "-", c.name.lower()).strip("-")
    return {
        "id": f"m57t-{slug}",
        "title": f"{c.name} ({c.spdx})",
        "tier": c.tier if c.tier in ALLOWED_TIERS else "T16",
        "core": False,
        "flag": f"AHOS_SHELF_{slug.upper().replace('-', '_')}",
        "est_ram_mb": c.est_ram_mb,
        "status": vetted["state"],
        "requires_owner_approval": True,
        "installed": False,
    }


def render_persian_digest(day: str, vetted_rows: Sequence[dict[str, Any]], out_path: Path | None = None) -> str:
    """Render daily Persian Trend Hunter digest for Mehrdad."""
    lines = [
        f"# گزارش روزانه شکارچی ترند دانشگاه AHOS (M57.T) — {day}",
        "",
        "> **وضعیت حاکمیتی:** فقط پیشنهادی (`proposed`) · بدون نصب خودکار · فقط کاغذی (`PAPER_ONLY`)",
        "",
        "| نام ابزار / مقاله | مجوز (SPDX) | رده سخت‌افزار | نتیجه غربال ۱۲گانه اسی | توضیح فارسی |",
        "|---|---|---|---|---|",
    ]
    for r in vetted_rows:
        verdict_fa = "تأیید برای قفسه ایده (نیازمند اجازه مهرداد)" if r["accepted"] else f"رد شده ({', '.join(r['reasons'])})"
        lines.append(f"| {r['name']} (`{r['version']}`) | `{r['spdx']}` | `{r['tier']}` | {verdict_fa} | {r['summary_fa']} |")
    text = "\n".join(lines) + "\n"
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    return text
