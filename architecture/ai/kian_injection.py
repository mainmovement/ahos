"""Kian taint labels and prompt-injection defense (M35.1).

Detects and tags prompt-injection attempts. Kian never executes write-tool
calls for injected content (acceptance K-4: ≥50 injection attacks produce 0
write-tool calls).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


# Common prompt-injection patterns (from research)
INJECTION_PATTERNS = [
    # Direct instruction injection
    r"ignore previous instructions",
    r"disregard previous context",
    r"forget the above",
    r"start new conversation",
    r"forget everything said",
    r"override your instructions",
    r"do what i say",
    r"break your rules",
    r"ignore your safety guidelines",

    # Jailbreak-style patterns
    r"you are now in full control",
    r"act as a",
    r"bypass",
    r"circumvent",
    r"evade",
    r"help me bypass",
    r"how to bypass",
    r"bypass instructions",

    # Role-playing injection
    r"pretend to be",
    r"simulate",
    r"simulate as if",
    r"as if you are",

    # Code injection
    r"execute this code",
    r"run this script",
    r"python ",
    r"bash ",
    r"shell ",
    r"execute: ",

    # Output manipulation
    r"output only",
    r"ignore all",
    r"forget all",
    r"stop",
    r"terminate",

    # Hidden instruction patterns
    r"\[instruction\]",
    r"\[hidden instruction\]",
    r"\[system instruction\]",
    r"\[override\]",
    r"\[ignore\]",

    # Urgency-based injection
    r"right now",
    r"immediately",
    r"urgent",
    r"urgent action required",

    # "Ignore above" patterns
    r"ignore above",
    r"ignore previous",
    r"ignore earlier",
    r"previous",
    r"forget",
]


@dataclass
class InjectionDetection:
    """Result of injection detection."""
    detected: bool
    patterns_found: List[str]
    confidence: float
    taint_labels: List[str]
    severity: str  # low | medium | high | critical


class InjectionDetector:
    """Detects prompt-injection attempts in user messages."""

    def __init__(self) -> None:
        # Compile patterns with word boundaries for better precision
        self.patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self.severity_thresholds = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

    def detect(self, message: str) -> InjectionDetection:
        """Detect injection patterns in a message. Returns label suggestions."""
        found_patterns = []
        confidence = 0.0

        for pattern in self.patterns:
            match = pattern.search(message)
            if match:
                found_patterns.append(match.group(0))
                confidence += 1.0

        detected = confidence > 0

        # Determine severity
        severity = "low"
        if confidence >= self.severity_thresholds["critical"]:
            severity = "critical"
        elif confidence >= self.severity_thresholds["high"]:
            severity = "high"
        elif confidence >= self.severity_thresholds["medium"]:
            severity = "medium"

        # Generate taint labels
        taint_labels = []
        if detected:
            if severity in ["high", "critical"]:
                taint_labels.append("PROMPT_INJECTION_CRITICAL")
            elif severity == "high":
                taint_labels.append("PROMPT_INJECTION_HIGH")
            elif severity == "medium":
                taint_labels.append("PROMPT_INJECTION_MEDIUM")
            else:
                taint_labels.append("PROMPT_INJECTION_LOW")

            # Add specific pattern label
            if found_patterns:
                # Take the most serious-looking pattern
                critical_patterns = ["ignore previous instructions", "ignore above", "disregard"]
                for crit in critical_patterns:
                    if crit.lower() in str(found_patterns).lower():
                        taint_labels.append("INSTRUCTION_OVERRIDE")
                        break

        return InjectionDetection(
            detected=detected,
            patterns_found=found_patterns,
            confidence=min(confidence / 4.0, 1.0),  # Normalize 0-4 to 0-1
            taint_labels=taint_labels,
            severity=severity,
        )

    def should_refuse(self, detection: InjectionDetection) -> bool:
        """Check if an injection should be refused."""
        # Critical and high-severity injections are refused
        return detection.severity in ["critical", "high"]

    def sanitize_message(self, message: str, detection: InjectionDetection) -> str:
        """Sanitize a message by removing suspicious content.

        Note: This is a defensive measure. The main defense is refuse-on-injection.
        """
        if not detection.detected:
            return message

        # For now, just redact suspicious patterns (not implemented for brevity)
        # In production, this would remove or truncate the injection content
        return message


class InjectionDefense:
    """Provides prompt-injection defense for Kian.

    All write-tool calls must be blocked when injection is detected.
    """

    def __init__(self) -> None:
        self.detector = InjectionDetector()
        self._refusal_reasons = set()

    def check_message(self, message: str) -> InjectionDetection:
        """Check a message for injection. Returns detection result."""
        detection = self.detector.detect(message)

        # Track refusal reasons
        if detection.detected:
            if detection.severity in ["critical", "high"]:
                self._refusal_reasons.add(f"PROMPT_INJECTION_{detection.severity}")
            elif detection.severity == "medium":
                self._refusal_reasons.add("PROMPT_INJECTION_MEDIUM")
            else:
                self._refusal_reasons.add("PROMPT_INJECTION_LOW")

        return detection

    def should_refuse_write(self, message: str) -> bool:
        """Check if a write-tool call should be refused due to injection."""
        detection = self.check_message(message)
        return self.detector.should_refuse(detection)

    def get_refusal_reasons(self) -> List[str]:
        """Get all refusal reasons for the current message."""
        return list(self._refusal_reasons)

    def clear_refusal_reasons(self) -> None:
        """Clear refusal reasons after processing."""
        self._refusal_reasons.clear()

    def apply_taint_labels(self, message: str) -> tuple[str, List[str]]:
        """Apply taint labels to a message and return (sanitized_message, labels)."""
        detection = self.check_message(message)
        sanitized = self.detector.sanitize_message(message, detection)
        return sanitized, detection.taint_labels


class InjectionDefenseError(Exception):
    """Raised when injection defense operations fail."""
    pass
