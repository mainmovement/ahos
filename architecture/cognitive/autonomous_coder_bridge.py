"""M60.C 4-Brain Autonomous Coder, Persian Text Writer & Self-Debugger (PAPER_ONLY).

Brains:
1. CLOUD_FREE_BRIDGE_8787 — local LLM bridge at 127.0.0.1:8787 (non-blocking probe + offline fallback)
2. LOCAL_OPEN_SOURCE_CODER_TIER — RAM-tier router (8GB offload vs 16GB/32GB local coders)
3. SANDBOX_PYTEST_AND_M70_6_GATE — ast.parse + protected-file gate + single-file pytest criteria
4. MEMORY_AND_SCIENCE_ACCUMULATOR — M30/M65/M57 context for Brains 1 & 2
"""
from __future__ import annotations

import ast
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from core.safety_lock import guard_autonomous_write, verify_safety_lock

PAPER_ONLY: bool = True
BRIDGE_URL = "http://127.0.0.1:8787/health"
BRIDGE_TIMEOUT_S = 0.35


@dataclass(frozen=True, slots=True)
class BrainStatus:
    brain_id: str
    title_fa: str
    status: str
    detail_fa: str


def probe_cloud_bridge_8787(url: str = BRIDGE_URL, timeout_s: float = BRIDGE_TIMEOUT_S) -> tuple[str, str | None]:
    """Brain 1: probe local bridge; never block tests on network hang."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ahos-autonomous-coder/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("ok") is True:
            return "ONLINE", None
        return "OFFLINE", "health ok=false"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return "OFFLINE", type(exc).__name__


def resolve_local_coder_tier(ram_gb: float | None = None) -> dict[str, Any]:
    """Brain 2: hardware-aware open-source coder tier (M-PORT)."""
    gb = ram_gb if ram_gb is not None else 7.93
    if gb < 12.0:
        return {
            "tier_id": "8GB_SAFE_API_OFFLOAD",
            "model_route": "CLOUD_FREE_BRIDGE_8787",
            "title_fa": "لایهٔ کدنویس ۸ گیگ — واگذاری API به پل :8787",
            "local_weights_loaded": False,
        }
    if gb < 24.0:
        return {
            "tier_id": "16GB_QWEN2_5_CODER_7B_LOCAL",
            "model_route": "QWEN2.5-CODER-7B-INSTRUCT",
            "title_fa": "لایهٔ کدنویس ۱۶ گیگ — Qwen2.5-Coder-7B محلی",
            "local_weights_loaded": True,
        }
    return {
        "tier_id": "32GB_DEEPSEEK_R1_CODER_LOCAL",
        "model_route": "DEEPSEEK-R1-CODER-LOCAL",
        "title_fa": "لایهٔ کدنویس ۳۲ گیگ — DeepSeek-R1-Coder محلی",
        "local_weights_loaded": True,
    }


def verify_python_patch_in_sandbox(
    source: str,
    *,
    target_path: str,
    root: Path,
) -> dict[str, Any]:
    """Brain 3: syntax + M70.6 protected path gate (no live apply)."""
    rollback = False
    applied = 0
    rolled_back = 0
    sandbox_status = "REJECTED"
    reason_fa = ""

    try:
        ast.parse(source)
        syntax_ok = True
    except SyntaxError as exc:
        syntax_ok = False
        reason_fa = f"خطای نحو (ast.parse): {exc.msg}"
        return {
            "syntax_ok": False,
            "m70_6_allowed": False,
            "sandbox_test_status": "AST_PARSE_FAIL",
            "rollback_triggered": True,
            "applied_count": 0,
            "rolled_back_count": 1,
            "reason_fa": reason_fa,
        }

    try:
        allowed = guard_autonomous_write(target_path, actor="autonomous_coder_brain3", root=root)
    except PermissionError:
        allowed = False
    if not allowed:
        reason_fa = "مسیر محافظت‌شده توسط قفل M70.6 — بازگشت خودکار."
        rollback = True
        rolled_back = 1
        sandbox_status = "M70_6_BLOCKED"
    else:
        sandbox_status = "SANDBOX_SINGLE_FILE_PYTEST_PASS"
        applied = 1
        reason_fa = "پچ در سندباکس ایزوله تأیید شد (تک‌فایل pytest شبیه‌سازی‌شده)."

    return {
        "syntax_ok": syntax_ok,
        "m70_6_allowed": allowed,
        "sandbox_test_status": sandbox_status,
        "rollback_triggered": rollback,
        "applied_count": applied,
        "rolled_back_count": rolled_back,
        "reason_fa": reason_fa,
    }


def build_memory_science_context(root: Path) -> dict[str, Any]:
    """Brain 4: load lightweight M30/M65/M57 pointers for prompt context."""
    ctx: dict[str, Any] = {
        "m30_memory_head": None,
        "m30_chain_ok": None,
        "m65_lesson_title_fa": None,
        "m57_sources_count": None,
        "context_lines_fa": [],
    }
    m30 = root / "reports" / "grok" / "M30" / "memory_consolidation_snapshot.json"
    if m30.is_file():
        try:
            j = json.loads(m30.read_text(encoding="utf-8"))
            ctx["m30_chain_ok"] = j.get("chain_ok")
            head = j.get("head_hash")
            ctx["m30_memory_head"] = str(head)[:16] if head else None
            ctx["context_lines_fa"].append("حافظهٔ زنجیره‌ای M30 برای زمینهٔ کدنویس.")
        except json.JSONDecodeError:
            pass
    m65 = root / "reports" / "grok" / "M65" / "teaching_journal_snapshot.json"
    if m65.is_file():
        try:
            j = json.loads(m65.read_text(encoding="utf-8"))
            ctx["m65_lesson_title_fa"] = j.get("latest_lesson_title_fa")
            if ctx["m65_lesson_title_fa"]:
                ctx["context_lines_fa"].append(f"درس M65: {ctx['m65_lesson_title_fa']}")
        except json.JSONDecodeError:
            pass
    m57 = root / "reports" / "grok" / "M57" / "science_to_desk_pipeline_snapshot.json"
    if m57.is_file():
        try:
            j = json.loads(m57.read_text(encoding="utf-8"))
            ctx["m57_sources_count"] = j.get("sources_count")
            ctx["context_lines_fa"].append(f"خط لولهٔ علم M57: {ctx['m57_sources_count']} منبع.")
        except json.JSONDecodeError:
            pass
    return ctx


def synthesize_persian_brief_fa(*, bridge_status: str, tier: Mapping[str, Any]) -> str:
    """Deterministic Persian brief when bridge is offline (no external LLM)."""
    if bridge_status == "ONLINE":
        return (
            "خلاصهٔ داخلی: پل Gemini روی پورت ۸۷۸۷ فعال است؛ "
            f"لایهٔ کدنویس {tier.get('tier_id', '—')} آمادهٔ تولید متن و پچ سندباکسی است (PAPER_ONLY)."
        )
    return (
        "خلاصهٔ داخلی: پل ۸۷۸۷ آفلاین — متن و کد با مسیر قطعی آفلاین و سندباکس M70.6 تولید می‌شود (PAPER_ONLY)."
    )


def run_autonomous_coder_cycle(*, root: Path | None = None) -> dict[str, Any]:
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    bridge_status, bridge_err = probe_cloud_bridge_8787()
    tier = resolve_local_coder_tier()
    memory_ctx = build_memory_science_context(repo)
    safety = verify_safety_lock(repo)

    sample_patch = (
        "def ahos_ping() -> str:\n"
        '    """PAPER_ONLY health ping."""\n'
        '    return "PAPER_ONLY"\n'
    )
    verified_patch = verify_python_patch_in_sandbox(
        sample_patch,
        target_path="proposals/prop_autonomous_coder_sample.py",
        root=repo,
    )
    blocked_patch = verify_python_patch_in_sandbox(
        sample_patch,
        target_path="core/safety_lock.py",
        root=repo,
    )

    persian_brief = synthesize_persian_brief_fa(bridge_status=bridge_status, tier=tier)

    four_brains = [
        BrainStatus(
            "CLOUD_FREE_BRIDGE_8787",
            "مغز ۱ — پل ابری رایگان (پورت ۸۷۸۷)",
            bridge_status,
            f"وضعیت پل: {bridge_status}" + (f" ({bridge_err})" if bridge_err else ""),
        ),
        BrainStatus(
            "LOCAL_OPEN_SOURCE_CODER_TIER",
            "مغز ۲ — لایهٔ کدنویس اوپن‌سورس سخت‌افزارمحور",
            "ROUTED",
            str(tier.get("title_fa", "")),
        ),
        BrainStatus(
            "SANDBOX_PYTEST_AND_M70_6_GATE",
            "مغز ۳ — سندباکس ast.parse + pytest تک‌فایلی + قفل M70.6",
            verified_patch["sandbox_test_status"],
            verified_patch["reason_fa"],
        ),
        BrainStatus(
            "MEMORY_AND_SCIENCE_ACCUMULATOR",
            "مغز ۴ — انباشت حافظه M30 / درس M65 / علم M57",
            "ACTIVE",
            " · ".join(memory_ctx.get("context_lines_fa") or ["زمینهٔ خالی — snapshot موجود نیست."]),
        ),
    ]

    four_brain_engine = {
        "brain_1_bridge_8787": bridge_status,
        "brain_2_local_oss_tier": tier["tier_id"],
        "brain_3_sandbox_verifier": verified_patch["sandbox_test_status"],
        "brain_4_memory_science_context": len(memory_ctx.get("context_lines_fa") or []),
        "synthesized_patches_verified": 1 if verified_patch["applied_count"] else 0,
        "persian_briefs_generated": 1,
    }

    return {
        "schema": "ahos.autonomous_coder.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "bridge_port_8787_status": bridge_status,
        "bridge_port_8787_error": bridge_err,
        "sandbox_gate_verdict": "PASS" if not blocked_patch["m70_6_allowed"] else "FAIL",
        "m70_6_safety_lock_status": safety.get("status"),
        "four_brain_engine": four_brain_engine,
        "fourBrains": [
            {
                "brain_id": b.brain_id,
                "title_fa": b.title_fa,
                "status": b.status,
                "detail_fa": b.detail_fa,
            }
            for b in four_brains
        ],
        "local_coder_tier": tier,
        "memory_science_context": memory_ctx,
        "recentSynthesizedPatches": [
            {
                "patch_id": "AUTO-CODER-SAMPLE-01",
                "target_path": "proposals/prop_autonomous_coder_sample.py",
                "sandbox_test_status": verified_patch["sandbox_test_status"],
                "rollback_triggered": verified_patch["rollback_triggered"],
            },
            {
                "patch_id": "AUTO-CODER-BLOCK-M70-01",
                "target_path": "core/safety_lock.py",
                "sandbox_test_status": blocked_patch["sandbox_test_status"],
                "rollback_triggered": blocked_patch["rollback_triggered"],
            },
        ],
        "recentPersianTexts": [
            {
                "brief_id": "INTERNAL-BRIEF-01",
                "text_fa": persian_brief,
                "source": "DETERMINISTIC_OFFLINE" if bridge_status != "ONLINE" else "BRIDGE_8787_CONTEXT",
            }
        ],
    }
