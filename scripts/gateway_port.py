#!/usr/bin/env python3
"""Single source of truth for the local Conversation Gateway URL (GM-05).

Resolution order (first non-empty wins):
  1. ``AHOS_GATEWAY_URL``  - full URL (existing operator contract, unchanged)
  2. ``AHOS_GATEWAY_PORT`` - port only; URL = http://127.0.0.1:<port>/api/chat
  3. default              - http://127.0.0.1:3000/api/chat (Next.js default)

The default stays 3000 on purpose: ~40 repo references, tests and launchers
use it. Running the gateway elsewhere (e.g. ``next dev -p 3500``) is an
operator choice expressed through one of the two variables above.

Diagnostic (read-only, loopback only): reports whether the configured port
has a listener and which candidate ports do::

    CONFIGURED_PORT_LISTENING     - configured port accepts TCP
    CONFIGURED_PORT_NO_LISTENER   - nothing there, but a candidate port does
    NO_GATEWAY_LISTENING          - nothing on the configured or candidate ports
    NON_LOCAL_URL_NOT_PROBED      - configured host is not loopback; no probe

This module never writes ``.env`` and never starts/stops anything.

CLI::

    python scripts/gateway_port.py              # human summary
    python scripts/gateway_port.py --json       # machine-readable diagnosis
    python scripts/gateway_port.py --url-only   # print the resolved URL
    python scripts/gateway_port.py --env-file .env   # read keys from .env (read-only)
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlsplit

DEFAULT_GATEWAY_HOST = "127.0.0.1"
DEFAULT_GATEWAY_PORT = 3000
CHAT_PATH = "/api/chat"
DEFAULT_CANDIDATE_PORTS = (3000, 3500)
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
GATEWAY_ENV_KEYS = ("AHOS_GATEWAY_URL", "AHOS_GATEWAY_PORT", "AHOS_GATEWAY_CANDIDATE_PORTS")


def _parse_port(raw: str | None) -> int | None:
    s = (raw or "").strip()
    if not s.isdigit():
        return None
    p = int(s)
    return p if 1 <= p <= 65535 else None


def default_gateway_url(port: int = DEFAULT_GATEWAY_PORT) -> str:
    return f"http://{DEFAULT_GATEWAY_HOST}:{port}{CHAT_PATH}"


def resolve_gateway(env: Mapping[str, str] | None = None) -> dict:
    """Resolve the gateway URL. Pure: reads only the given mapping."""
    env = os.environ if env is None else env
    warnings: list[str] = []
    raw_url = (env.get("AHOS_GATEWAY_URL") or "").strip()
    raw_port = (env.get("AHOS_GATEWAY_PORT") or "").strip()
    port_override = _parse_port(raw_port)
    if raw_port and port_override is None:
        warnings.append("AHOS_GATEWAY_PORT_INVALID_IGNORED")

    if raw_url:
        parts = urlsplit(raw_url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            warnings.append("AHOS_GATEWAY_URL_UNPARSEABLE")
            return {"url": raw_url, "host": None, "port": None,
                    "source": "AHOS_GATEWAY_URL", "warnings": warnings}
        try:
            url_port = parts.port or (443 if parts.scheme == "https" else 80)
        except ValueError:
            warnings.append("AHOS_GATEWAY_URL_UNPARSEABLE")
            return {"url": raw_url, "host": parts.hostname, "port": None,
                    "source": "AHOS_GATEWAY_URL", "warnings": warnings}
        if port_override is not None and port_override != url_port:
            # URL wins (existing contract); surface the disagreement loudly.
            warnings.append("AHOS_GATEWAY_PORT_DISAGREES_WITH_URL")
        return {"url": raw_url, "host": parts.hostname, "port": url_port,
                "source": "AHOS_GATEWAY_URL", "warnings": warnings}

    if port_override is not None:
        return {"url": default_gateway_url(port_override), "host": DEFAULT_GATEWAY_HOST,
                "port": port_override, "source": "AHOS_GATEWAY_PORT", "warnings": warnings}

    return {"url": default_gateway_url(), "host": DEFAULT_GATEWAY_HOST,
            "port": DEFAULT_GATEWAY_PORT, "source": "DEFAULT", "warnings": warnings}


def candidate_ports(env: Mapping[str, str] | None = None) -> tuple[int, ...]:
    env = os.environ if env is None else env
    raw = (env.get("AHOS_GATEWAY_CANDIDATE_PORTS") or "").strip()
    if not raw:
        return DEFAULT_CANDIDATE_PORTS
    ports = tuple(p for p in (_parse_port(x) for x in raw.split(",")) if p is not None)
    return ports or DEFAULT_CANDIDATE_PORTS


def port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    """TCP connect probe. Callers must only pass loopback hosts."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def diagnose(env: Mapping[str, str] | None = None,
             probe: Callable[[str, int], bool] | None = None) -> dict:
    env = os.environ if env is None else env
    probe = probe or port_listening
    res = resolve_gateway(env)
    out = {
        "schema": "ahos.gateway_port_diagnosis.v1",
        "configured_url": res["url"],
        "configured_port": res["port"],
        "source": res["source"],
        "warnings": list(res["warnings"]),
        "configured_listening": None,
        "listening_candidates": [],
        "verdict": None,
        "hint": None,
    }
    host = (res["host"] or "").lower()
    if host not in LOOPBACK_HOSTS or res["port"] is None:
        out["verdict"] = "NON_LOCAL_URL_NOT_PROBED"
        return out
    probe_host = DEFAULT_GATEWAY_HOST if host == "localhost" else host
    out["configured_listening"] = bool(probe(probe_host, res["port"]))
    others = [p for p in candidate_ports(env) if p != res["port"]]
    out["listening_candidates"] = [p for p in others if probe(probe_host, p)]
    if out["configured_listening"]:
        out["verdict"] = "CONFIGURED_PORT_LISTENING"
    elif out["listening_candidates"]:
        out["verdict"] = "CONFIGURED_PORT_NO_LISTENER"
        alt = out["listening_candidates"][0]
        out["hint"] = (
            f"Configured {res['url']} has no listener but 127.0.0.1:{alt} does. "
            f"OWNER_ACTION: either start the gateway on {res['port']} or set "
            f"AHOS_GATEWAY_URL={default_gateway_url(alt)} (or AHOS_GATEWAY_PORT={alt}). "
            "This tool does not change .env."
        )
    else:
        out["verdict"] = "NO_GATEWAY_LISTENING"
        out["hint"] = "No local gateway listener found; start 'npm run dev' (OWNER_ACTION)."
    return out


def read_env_file(path: Path) -> dict[str, str]:
    """Read only the gateway keys from a dotenv file (never writes)."""
    vals: dict[str, str] = {}
    if not path.is_file():
        return vals
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        t = line.strip()
        if not t or t.startswith("#") or "=" not in t:
            continue
        k, _, v = t.partition("=")
        k = k.strip()
        if k not in GATEWAY_ENV_KEYS:
            continue
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        vals[k] = v
    return vals


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS gateway URL resolution + read-only port diagnosis")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--url-only", action="store_true")
    ap.add_argument("--env-file", default="", help="read gateway keys from this dotenv file (read-only; overrides process env like the gate does)")
    args = ap.parse_args(argv)
    env: dict[str, str] = {k: v for k, v in os.environ.items() if k in GATEWAY_ENV_KEYS}
    if args.env_file:
        env.update(read_env_file(Path(args.env_file)))
    if args.url_only:
        print(resolve_gateway(env)["url"])
        return 0
    d = diagnose(env)
    if args.json:
        print(json.dumps(d, indent=2))
    else:
        print(f"gateway_url={d['configured_url']} source={d['source']} verdict={d['verdict']}")
        if d["listening_candidates"]:
            print("listening_candidates=" + ",".join(str(p) for p in d["listening_candidates"]))
        for w in d["warnings"]:
            print(f"warning={w}")
        if d["hint"]:
            print(f"hint={d['hint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
