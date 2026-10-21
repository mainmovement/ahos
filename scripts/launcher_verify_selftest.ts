import assert from "node:assert/strict";
import test from "node:test";
import { parseVerifyReceipt, telegramHealthStatus } from "../src/lib/launcher-verify.ts";

test("launcher verify: BOM strip and telegram states", () => {
  const map = parseVerifyReceipt(["\uFEFFts=2026-10-21", "telegram_state=RUNNING", "free_ram_mb=3000"]);
  assert.equal(map.ts, "2026-10-21");
  assert.equal(telegramHealthStatus(map.telegram_state), "LIVE");
  assert.equal(telegramHealthStatus("PREFLIGHT_FAIL"), "ERROR");
});
