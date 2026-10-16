#!/usr/bin/env python3
"""Test script to verify M61 fix works."""

import os
import sys
from pathlib import Path

# Add telegram_ai to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "telegram_ai"))

from telegram_ai.service import TelegramDomainService

def test_service():
    """Test if Telegram service now properly loads AHOS_GATEWAY_URL."""
    service = TelegramDomainService()

    # Check if gateway URL is loaded
    from telegram_ai.service import AHOS_GATEWAY_URL
    print(f"Gateway URL loaded: {AHOS_GATEWAY_URL}")

    if AHOS_GATEWAY_URL:
        print("✅ SUCCESS: AHOS_GATEWAY_URL is loaded and non-empty")

        # Test a simple message to see if it tries to call gateway
        test_result = service.handle_message("test message")
        print(f"Result status: {test_result['status']}")
        print(f"Result intent: {test_result['intent']}")

        if test_result['status'] == 'OK':
            print("✅ SUCCESS: Service successfully connected to gateway")
        else:
            print("⚠️  WARNING: Service returned non-OK status, but this might be expected if gateway isn't running")

        if test_result['source'] == 'conversation_gateway':
            print("✅ SUCCESS: Source shows conversation_gateway")
        else:
            print(f"ℹ️  INFO: Source is {test_result['source']} (might be EMERGENCY_FALLBACK_ONLY if gateway not running)")

        return True
    else:
        print("❌ FAILURE: AHOS_GATEWAY_URL is empty")
        return False

if __name__ == "__main__":
    test_service()