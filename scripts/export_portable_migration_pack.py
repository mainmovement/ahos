#!/usr/bin/env python3
"""M-PORT / M62 One-Click Portable Hardware Auto-Tier & Migration Pack Exporter.
Detects system RAM, CPU cores, and dynamic AHOS root path (zero hardcoded C:\\ dependency),
auto-selects the hardware tier (`TIER_8GB_SAFE` | `TIER_16GB_BALANCED` | `TIER_32GB_ULTRA`),
verifies M70.6 safety lock & HOLD.flag, and writes `reports/grok/M62/portable_migration_pack.json` (UTF-8 no BOM).
"""
from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.safety_lock import verify_safety_lock


def detect_system_ram_gb() -> float:
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if pages > 0 and page_size > 0:
                return round((pages * page_size) / (1024.0 ** 3), 2)
    except (ValueError, OSError):
        pass
    if sys.platform.startswith("win"):
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return round(stat.ullTotalPhys / (1024.0 ** 3), 2)
        except Exception:
            pass
    return 8.0


def select_auto_tier(ram_gb: float, cpu_cores: int) -> dict[str, Any]:
    if ram_gb <= 9.5:
        return {
            "auto_tier": "TIER_8GB_SAFE",
            "arena_quality_default": "low",
            "heavy_features_allowed": False,
            "max_pytest_files_per_invocation": 2,
            "allow_local_next_build": False,
            "description_fa": "حالت ایمن ۸ گیگابایت (TIER_8GB_SAFE): غیرفعال‌سازی بیلدهای سنگین محلی و اجرای سبک بدون فریز.",
        }
    if ram_gb <= 20.0 or cpu_cores < 12:
        return {
            "auto_tier": "TIER_16GB_BALANCED",
            "arena_quality_default": "balanced",
            "heavy_features_allowed": False,
            "max_pytest_files_per_invocation": 8,
            "allow_local_next_build": True,
            "description_fa": "حالت متعادل ۱۶ گیگابایت (TIER_16GB_BALANCED): رندر متعادل و اجرای دسته‌ای تست‌ها.",
        }
    return {
        "auto_tier": "TIER_32GB_ULTRA",
        "arena_quality_default": "high",
        "heavy_features_allowed": True,
        "max_pytest_files_per_invocation": 50,
        "allow_local_next_build": True,
        "description_fa": "حالت قدرتمند ۳۲+ گیگابایت (TIER_32GB_ULTRA): تمام قابلیت‌های گرافیکی و آزمایشگاهی فعال.",
    }


def build_portable_migration_pack(root: Path | None = None) -> dict[str, Any]:
    repo = (root or ROOT).resolve()
    workspace_root = repo.parent
    ram_gb = detect_system_ram_gb()
    cores = os.cpu_count() or 4
    tier_cfg = select_auto_tier(ram_gb, cores)
    safety = verify_safety_lock(repo)
    hold_ahos = (repo / "HOLD.flag").is_file()
    hold_arena = (workspace_root / "ahos_arena" / "HOLD.flag").is_file()

    # Verify zero C:\ hardcoded requirement and portable runtimes under ahos_runtime/
    drive_or_mount = repo.drive if repo.drive else "/"
    rt_dir = workspace_root / "ahos_runtime"
    portable_node = (rt_dir / "node" / "node.exe").is_file() or (rt_dir / "node" / "bin" / "node").is_file()
    portable_python = (rt_dir / "python" / "python.exe").is_file() or (rt_dir / "python" / "bin" / "python3").is_file()
    pyvenv_cfg = repo / ".venv" / "pyvenv.cfg"
    venv_zero_c = True
    if pyvenv_cfg.is_file():
        venv_zero_c = "c:\\" not in pyvenv_cfg.read_text(encoding="utf-8", errors="ignore").lower()
    zero_c_drive_dependency = (drive_or_mount.upper() != "C:") and venv_zero_c

    return {
        "schema": "ahos.portable_migration_pack.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "portable_ready": bool(safety["ok"] and hold_ahos),
        "dynamic_root_resolved": str(workspace_root),
        "drive_or_mount": drive_or_mount,
        "zero_c_drive_dependency": zero_c_drive_dependency,
        "portable_runtimes": {
            "runtime_dir": str(rt_dir),
            "portable_node_bundled": portable_node,
            "portable_python_bundled": portable_python,
            "venv_pyvenv_cfg_zero_c": venv_zero_c,
        },
        "hardware": {
            "platform": platform.system(),
            "ram_gb": ram_gb,
            "cpu_cores": cores,
            **tier_cfg,
        },
        "safety_verification": {
            "m70_6_safety_lock": safety["status"],
            "verified_files_count": safety["verified_files"],
            "hold_flag_ahos": hold_ahos,
            "hold_flag_arena": hold_arena,
        },
        "migration_steps_fa": [
            "۱. پوشهٔ کامل robat را روی هر درایو دلخواه در سیستم مقصد (مثلاً D:\\robat یا G:\\robat) کپی کنید (بدون هیچ وابستگی به درایو C).",
            "۲. اسکریپت Verify-PortableMigration.ps1 را اجرا کنید تا به صورت خودکار مقدار رم سیستم جدید را تشخیص داده و سطح سخت‌افزاری (8GB Safe / 16GB Balanced / 32GB Ultra) و قفل‌های ایمنی M70.6 را تنظیم کند.",
            "۳. با اجرای AHOS_LightStart.ps1 داشبورد Arena روی پورت 3200 و موتور کاغذی طلا با همان تاریخچهٔ زنجیره‌ای بدون نیاز به نصب مجدد بالا می‌آیند.",
        ],
    }


def main() -> int:
    payload = build_portable_migration_pack(ROOT)
    out_dir = ROOT / "reports" / "grok" / "M62"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "portable_migration_pack.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {out_path} tier={payload['hardware']['auto_tier']} "
        f"ram_gb={payload['hardware']['ram_gb']} safety={payload['safety_verification']['m70_6_safety_lock']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
