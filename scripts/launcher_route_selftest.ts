/**
 * M11.1: self-test for the dashboard launcher route's skip-argument emission.
 * No network, no DB, no file writes. Run: npm run test:launcher-route
 *
 * ``spawnLauncher`` hands its exclusions to a reparented PowerShell child
 * through ``Start-Process -ArgumentList``, which re-parses the array back into
 * ONE command line. A repeated ``-Skip`` therefore reaches the child as
 * ``-Skip a -Skip b`` on a single command line and PowerShell's binder rejects
 * it with "parameter 'Skip' is specified more than once" — the child exits 1
 * before running a statement, which is exactly what broke Restart from the
 * dashboard. The fix is one ``-Skip`` whose value is comma-joined; this test is
 * the regression guard for that shape. (self-test, not independent verification)
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { launcherSkipArgs } from "../app/api/launcher/route.ts";

describe("launcherSkipArgs", () => {
  it("emits no arguments when nothing is skipped", () => {
    assert.deepEqual(launcherSkipArgs([]), []);
  });

  it("emits a single -Skip for one exclusion", () => {
    assert.deepEqual(launcherSkipArgs(["engine"]), ["-Skip", "engine"]);
  });

  it("emits exactly ONE -Skip for several exclusions", () => {
    const args = launcherSkipArgs(["telegram", "engine"]);
    assert.deepEqual(args, ["-Skip", "telegram,engine"]);
    assert.equal(
      args.filter((a) => a === "-Skip").length,
      1,
      "a repeated -Skip is rejected by the child's parameter binder",
    );
  });

  it("keeps every exclusion in order in the joined value", () => {
    assert.equal(launcherSkipArgs(["stores", "db_backend", "gateway", "telegram", "engine"])[1],
      "stores,db_backend,gateway,telegram,engine");
  });
});
