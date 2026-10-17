"""M61 proof: TelegramDomainService POSTs to AHOS_GATEWAY_URL and returns gateway text."""
from __future__ import annotations

import importlib
import json
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _GatewayHandler(BaseHTTPRequestHandler):
    last_request: dict | None = None

    def log_message(self, *_args) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        type(self).last_request = {
            "path": self.path,
            "headers": {k: v for k, v in self.headers.items()},
            "body": payload,
        }
        reply = {
            "text": "سلام مهرداد — پاسخ آزمایشی از دروازه.",
            "intent": "m61_selftest",
            "focus_token": None,
            "evidence": {"proof": "mock_gateway"},
        }
        body = json.dumps(reply, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture()
def mock_gateway():
    server = HTTPServer(("127.0.0.1", 0), _GatewayHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/api/chat"
    yield url
    server.shutdown()


def test_m61_round_trip_transcript(mock_gateway, monkeypatch, tmp_path):
    monkeypatch.setenv("AHOS_GATEWAY_URL", mock_gateway)
    monkeypatch.delenv("AHOS_WEB_API_TOKEN", raising=False)
    monkeypatch.delenv("AHOS_TELEGRAM_GATEWAY_SECRET", raising=False)

    import telegram_ai.service as svc

    importlib.reload(svc)
    service = svc.TelegramDomainService()
    inbound = "M61 round-trip probe from pytest"
    out = service.handle_message(inbound, {"user_id": "owner-test"})

    assert out["status"] == "OK"
    assert out["source"] == "conversation_gateway"
    assert "پاسخ آزمایشی" in out["text"]
    assert _GatewayHandler.last_request is not None
    assert _GatewayHandler.last_request["body"]["message"] == inbound
    assert _GatewayHandler.last_request["body"]["channel"] == "telegram"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = ROOT / "reports" / f"telegram_e2e_{stamp}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# M61 Telegram gateway round-trip (automated proof)",
                "",
                f"- UTC: {stamp}",
                f"- Gateway URL: `{mock_gateway}`",
                f"- Inbound: `{inbound}`",
                f"- Outbound status: `{out['status']}`",
                f"- Outbound source: `{out['source']}`",
                f"- Outbound intent: `{out['intent']}`",
                f"- Outbound text (first line): `{out['text'].splitlines()[0]}`",
                "",
                "## Captured POST body",
                "```json",
                json.dumps(_GatewayHandler.last_request["body"], ensure_ascii=False, indent=2),
                "```",
            ]
        ),
        encoding="utf-8",
    )
    assert report.stat().st_size > 200


def test_m61_missing_gateway_is_fail_closed(monkeypatch):
    monkeypatch.delenv("AHOS_GATEWAY_URL", raising=False)
    import telegram_ai.service as svc

    importlib.reload(svc)
    out = svc.TelegramDomainService().handle_message("ping")
    assert out["status"] == "EMERGENCY_FALLBACK_ONLY"
    assert out["source"] == "EMERGENCY_FALLBACK_ONLY"
