# CLAUDE_MISSION_M61_TELEGRAM_BRIDGE_v2.md

**Mission:** Fix Telegram EMERGENCY_FALLBACK_ONLY when gateway URL is available
**Mission ID:** M61
**Status:** COMPLETE
**Queue Position:** 1 (first in binding order)

## Task Description
The Telegram bridge currently returns `EMERGENCY_FALLBACK_ONLY` instead of forwarding messages to the decision core, even when `AHOS_GATEWAY_URL` is properly configured. The bridge should normalize empty URLs and forward messages to the conversation gateway.

## Current Issue
- `telegram_ai/service.py` returns fallback response when `_call_conversation_gateway()` fails
- `_call_conversation_gateway()` returns None on any exception
- Empty `AHOS_GATEWAY_URL` should be normalized to default gateway
- Need to verify the fix works with G11 live E2E test

## Success Criteria
1. Telegram bridge forwards messages to decision core when gateway is available
2. Bridge normalizes empty `AHOS_GATEWAY_URL` to `http://127.0.0.1:3000/api/chat`
3. G11 live E2E test passes: owner sends message via Telegram, message reaches core
4. No more `EMERGENCY_FALLBACK_ONLY` when gateway is working

## Implementation Plan
1. Fix `telegram_ai/service.py` to normalize empty `AHOS_GATEWAY_URL` (same logic as `operator_validation_gate.py`)
2. Add fallback to default gateway if resolution fails
3. Test with G11 E2E workflow
4. Create test transcript at `reports/telegram_e2e_<UTC>.md`

## Files to Modify
- `telegram_ai/service.py` - normalize empty AHOS_GATEWAY_URL

## Testing
- Use `scripts/windows_g11_telegram_e2e_helper.ps1` for live testing
- Owner sends one message via Telegram to bridge
- Verify message reaches decision core
- Create test report with status and details

## Notes
- Mission M35.3 (token rotation) remains blocked - M61 works on current token
- This only fixes the bridge forwarding, does not enable token rotation
- PAPER_ONLY system, no real trading involved