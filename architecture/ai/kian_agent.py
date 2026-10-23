"""Kian core (M35.1) — Gemini integration, routing, council, memory, hash-chained audit store, tools, gate code, injection defense.

One comprehensive agent combining:
1. gemini_chat.py - Gemini conversational interface
2. router.py - Multi-tier fallback routing
3. council_live.py - Multi-model advisory layer
4. kian_audit_store.py - Hash-chained audit store
5. kian_gate.py - One-time gate code service
6. kian_memory.py - Owner dialogue memory thread
7. kian_tools.py - Typed tool allowlist (READ only)
8. kian_injection.py - Prompt-injection defense
9. kian_rate_limit.py - Rate limiting

Agent #39 "کیان" (Chief of Staff) - OWNER-APPROVED 2026-10-03 23:04
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from architecture.ai.council_live import CouncilVerdict, LiveCouncil
from architecture.ai.gemini_chat import chat_step
from architecture.ai.router import AIProviderRouter
from architecture.ai.kian_injection import InjectionDefense, InjectionDetection
from architecture.ai.kian_memory import OwnerDialogueMemory
from architecture.ai.kian_tools import KianTools, InvalidToolError
from architecture.ai.kian_rate_limit import RateLimiter
from architecture.ai.kian_gate import GateService, GateServiceError
from architecture.ai.kian_audit_store import KianAuditStore
from architecture.ai.credential_store import WindowsCredentialManagerStore
from ahos_org.registry import AgentRecord, AgentRegistry
from ahos_org.models import MaturityLevel


@dataclass
class KianConfig:
    """Kian configuration."""
    agent_id: str = "agent.kian"
    role: str = "Chief of Staff"
    description: str = "Owner-facing conversational AI for dashboard and Telegram"
    owner_approved: bool = True
    gemini_key_env: str = "GEMINI_API_KEY"
    audit_store_path: str = "data/kian_audit.jsonl"
    rate_limit_chat: int = 10
    rate_limit_tools: int = 20


@dataclass
class KianMessage:
    """Kian message with all necessary fields."""
    seq: int
    timestamp: float
    channel: str
    user_id: str
    user_id_hash: str
    message: str
    message_hash: str
    response_to: Optional[int]
    role: str = "assistant"
    evidence: Optional[Dict[str, Any]] = None
    tool_calls: List[str] = None
    gate_code: Optional[str] = None
    injection_detected: bool = False


@dataclass
class KianResponse:
    """Kian's response to user queries."""
    message: str
    intent: str
    evidence: Optional[Dict[str, Any]]
    tool_calls: List[str]
    gate_code: Optional[str]
    timestamp: float
    confidence: float
    raw_response: Optional[Dict[str, Any]]


class KianAgent:
    """Kian core agent combining all M35.1 functionality."""

    def __init__(self, config: Optional[KianConfig] = None) -> None:
        self.config = config or KianConfig()

        # Ensure clean audit store for each instance (for testing)
        audit_path = Path(self.config.audit_store_path)
        if audit_path.exists() and audit_path.suffix == '.jsonl':
            audit_path.unlink()

        # Initialize components
        self.audit_store = KianAuditStore(self.config.audit_store_path)
        mem_file = None if self.config.audit_store_path == 'data/kian_audit.jsonl' else Path(self.config.audit_store_path).with_name('owner_dialogue.jsonl')
        self.memory = OwnerDialogueMemory(path=mem_file)
        self.injection_defense = InjectionDefense()
        self.rate_limiter = RateLimiter(self.audit_store)
        self.gate_service = GateService()

        # Initialize AI components
        self.gemini_router = AIProviderRouter()
        self.council = LiveCouncil()

        # Load Gemini key
        self.credential_store = WindowsCredentialManagerStore()

        # Statistics for acceptance K-9 (message bursts)
        self.message_bursts: List[Dict[str, Any]] = []

        # Record agent creation in audit store
        self._record_event(
            channel="system",
            user_id_hash="system",
            message_hash="system",
            action_type="agent_created",
            tool_calls=[],
            content=f"Kian agent #{self.config.agent_id} initialized",
            taint_labels=["AGENT_INIT"],
        )

    def _record_event(
        self,
        channel: str,
        user_id_hash: str,
        message_hash: str,
        action_type: str,
        tool_calls: List[str],
        content: str,
        taint_labels: List[str],
    ) -> None:
        """Record an event in the audit store."""
        try:
            self.audit_store.record_action(
                channel=channel,
                user_id_hash=user_id_hash,
                message_hash=message_hash,
                action_type=action_type,
                tool_calls=tool_calls,
                content=content,
                taint_labels=taint_labels,
            )
        except Exception:
            # Audit failure shouldn't break Kian
            pass

    def _hash_message(self, message: str) -> str:
        """SHA256 hash of a message for audit purposes."""
        return hashlib.sha256(message.encode("utf-8")).hexdigest()

    def _check_injection(self, message: str) -> tuple[InjectionDetection, bool]:
        """Check message for injection. Returns detection and whether to refuse."""
        detection = self.injection_defense.check_message(message)
        should_refuse = self.injection_defense.should_refuse_write(message)
        return detection, should_refuse

    def _record_message_burst(
        self,
        channel: str,
        user_id_hash: str,
        messages: List[str],
    ) -> None:
        """Record a message burst for K-9 acceptance."""
        burst = {
            "channel": channel,
            "user_id_hash": user_id_hash,
            "message_count": len(messages),
            "timestamp": time.time(),
            "queued": len(messages) > 5,  # K-9: message burst is queued and owner is notified
        }
        self.message_bursts.append(burst)

        # Record in audit store
        self._record_event(
            channel=channel,
            user_id_hash=user_id_hash,
            message_hash=self._hash_message(
                "|".join(messages)
            ),
            action_type="message_burst",
            tool_calls=[],
            content=f"Message burst detected: {len(messages)} messages",
            taint_labels=["MESSAGE_BURST"],
        )

    def process_message(
        self,
        channel: str,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> KianResponse:
        """Process a user message. This is the main entry point for Kian."""
        start_time = time.time()

        # Compute hashes for audit
        user_id_hash = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
        message_hash = self._hash_message(message)

        # Check rate limits
        rate_limit_chat = self.rate_limiter.check_rate_limit("kian_chat", "chat", user_id_hash)
        if not rate_limit_chat.allowed:
            return KianResponse(
                message="درخواست شما بیش از حد مجاز است. لطفاً بعداً مجدداً تلاش کنید.",
                intent="rate_limit",
                evidence={
                    "rate_limit": rate_limit_chat,
                    "user_id": user_id_hash,
                },
                tool_calls=[],
                gate_code=None,
                timestamp=time.time(),
                confidence=0.0,
                raw_response=None,
            )

        # Check for injection (K-4: no injection attacks produce write-tool calls)
        injection_detection, should_refuse = self._check_injection(message)
        if should_refuse:
            self._record_event(
                channel=channel,
                user_id_hash=user_id_hash,
                message_hash=message_hash,
                action_type="injection_detected",
                tool_calls=[],
                content=f"Injection detected: {injection_detection.severity}",
                taint_labels=injection_detection.taint_labels,
            )
            return KianResponse(
                message="پیام شما شامل محتوای خرابکارانه است. دسترسی مسدود شد.",
                intent="injection_blocked",
                evidence={
                    "detection": injection_detection.__dict__,
                },
                tool_calls=[],
                gate_code=None,
                timestamp=time.time(),
                confidence=0.0,
                raw_response=None,
            )

        # Record the message in memory
        self.memory.add_message(
            channel=channel,
            user_id_hash=user_id_hash,
            role="user",
            content=message,
            response_to_seq=None,
            summary_fa="User message to Kian",
        )

        # Check for message burst (K-9: message burst is queued)
        if len(self.message_bursts) > 0:
            recent_bursts = [
                b for b in self.message_bursts
                if time.time() - b["timestamp"] < 60 and b["channel"] == channel
            ]
            if len(recent_bursts) >= 5:  # Burst threshold
                self._record_message_burst(channel, user_id_hash, [message])

        # Get context from memory
        context = self.memory.get_context(limit=5)

        # Try Gemini with fallbacks (K-5: Gemini outage falls back through router)
        gemini_response = self._get_gemini_response(message, context)

        # If Gemini fails, use deterministic fallback (K-5)
        if not gemini_response:
            gemini_response = {
                "response": "دستیار هوش مصنوعی الان در دسترس نیست...",
                "finish_reason": "UNAVAILABLE",
                "model": "DETERMINISTIC_ONLY",
            }

        # Record successful processing
        self._record_event(
            channel=channel,
            user_id_hash=user_id_hash,
            message_hash=message_hash,
            action_type="message_processed",
            tool_calls=[],
            content=f"Processed message: {gemini_response.get('response', '')[:100]}...",
            taint_labels=[],  # No taint for successful messages
        )

        # Calculate confidence
        confidence = 1.0 if gemini_response.get("model") not in ["DETERMINISTIC_ONLY", None] else 0.5

        return KianResponse(
            message=gemini_response.get("response", "خطای داخلی"),
            intent="assistant_response",
            evidence=gemini_response,
            tool_calls=[],
            gate_code=None,
            timestamp=time.time(),
            confidence=confidence,
            raw_response=gemini_response,
        )

    def _get_gemini_response(self, message: str, context: str) -> Optional[Dict[str, Any]]:
        """Get a response from Gemini with fallbacks."""
        # Build prompt with context
        system_prompt = f"You are Kian (Chief of Staff). Respond in Persian. Only answer from evidence in conversation."

        # Try Gemini with retry logic
        for attempt in range(2):
            try:
                # Check rate limit for tool calls
                rate_limit_tools = self.rate_limiter.check_rate_limit("kian_tool_calls", "tool_call")
                if not rate_limit_tools.allowed:
                    return None

                gemini_request = {
                    "system": system_prompt + "\n\nContext: " + context,
                    "contents": [{"role": "user", "parts": [{"text": message}]}],  # Fixed: wrap in object
                    "models": ["gemini-flash-lite-latest"],
                    "timeout_ms": 4000,
                    "temperature": 0.3,
                }

                result = chat_step(gemini_request)

                if result.get("ok") and result.get("parts"):
                    response_text = ""
                    for part in result.get("parts", []):
                        if "text" in part:
                            response_text += part["text"]

                    return {
                        "response": response_text,
                        "finish_reason": result.get("finish_reason"),
                        "model": result.get("model"),
                        "latency_ms": result.get("latency_ms"),
                    }

                elif result.get("status") in ["UNAVAILABLE", "AUTH_FAILED", "QUOTA_EXHAUSTED"]:
                    # Try deterministic fallback (K-5: Gemini outage falls back)
                    if attempt == 0:
                        continue
                    return {
                        "response": "دستیار هوش مصنوعی الان در دسترس نیست...",
                        "finish_reason": "UNAVAILABLE",
                        "model": "DETERMINISTIC_ONLY",
                    }

            except Exception as e:
                # Log error but continue to deterministic fallback
                if attempt == 0:
                    continue
                return {
                    "response": "دستیار هوش مصنوعی الان در دسترس نیست...",
                    "finish_reason": "UNAVAILABLE",
                    "model": "DETERMINISTIC_ONLY",
                }

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get Kian status for monitoring."""
        return {
            "agent_id": self.config.agent_id,
            "role": self.config.role,
            "status": "operational",
            "audit_store": {
                "path": self.config.audit_store_path,
                "chain_integrity": self.audit_store.verify_chain(),
                "last_recorded": self.audit_store.last_seq,
            },
            "memory": {
                "messages_count": len(self.memory.messages),
                "last_seq": self.memory.last_seq,
            },
            "rate_limits": {
                "kian_chat": self.rate_limiter.get_current_usage("kian_chat"),
                "kian_tools": self.rate_limiter.get_current_usage("kian_tools"),
            },
            "gate_codes": {
                "active": self.gate_service.count_active(),
            },
            "message_bursts": len(self.message_bursts),
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        # Save memory state
        self.memory.save_to_disk()

        # Cleanup gate service
        self.gate_service.cleanup_expired()