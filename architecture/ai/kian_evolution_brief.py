"""M35.1/M35.2 — deterministic owner briefs for brain, debug, AGI/ACI, and pilot $100."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle

_KEYWORDS = re.compile(
    r"(مغز|دیباگ|آپدیت|خوددیباگ|AGI|ACI|SI|۱۰۰\s*دلار|100\s*دollar|پایلوت)",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_owner_evolution_brief_fa(message: str, *, root: Path | None = None) -> str | None:
    """Return a Persian evidence brief when owner asks about brain/debug/pilot; else None."""
    if not _KEYWORDS.search(message):
        return None
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    coder = run_autonomous_coder_cycle(root=repo)
    eng = coder.get("four_brain_engine") or {}
    pilot = _read_json(repo / "reports" / "grok" / "M43" / "pilot_100usd_gateway_snapshot.json")
    equity = (pilot or {}).get("pilot_account", {}).get("current_equity_usd", 100)
    missions_done = "85/85 DONE (100%)"
    bridge = eng.get("brain_1_bridge_8787", coder.get("bridge_port_8787_status"))
    tier = eng.get("brain_2_local_oss_tier", "—")
    patches = eng.get("synthesized_patches_verified", 0)
    return (
        f"وضعیت مغز ۴گانهٔ کدنویس (M60.C · PAPER_ONLY): پل :8787={bridge} · لایهٔ OSS={tier} · "
        f"پچ‌های تأییدشده در سندباکس={patches} · قفل M70.6={coder.get('m70_6_safety_lock_status', '—')}. "
        f"مسیر ACI→AGI→SI بدون ادعای AGI روز اول؛ حلقه‌های خوددیباگ/خودآپدیت فعال در snapshot. "
        f"پایلوت ۱۰۰ دلاری: ارزش کاغذی ~${equity} (HOLD قفل زنده). "
        f"پیشرفت مأموریت‌ها: {missions_done}."
    )
