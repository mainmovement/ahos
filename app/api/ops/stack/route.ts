import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "node:fs";
import { connect } from "node:net";
import { join } from "node:path";
import { launcherDir, readLauncherVerifyReceipt } from "@/src/lib/launcher-verify";

export const dynamic = "force-dynamic";

function probe(port: number, ms = 600): Promise<boolean> {
  return new Promise((resolve) => {
    const s = connect({ host: "127.0.0.1", port });
    const done = (ok: boolean) => {
      s.destroy();
      resolve(ok);
    };
    s.setTimeout(ms, () => done(false));
    s.once("connect", () => done(true));
    s.once("error", () => done(false));
  });
}

/** Read-only ops snapshot (ports + launcher verify file if present). */
export async function GET() {
  const root = launcherDir();
  const receipt = readLauncherVerifyReceipt();
  const verify = receipt?.map ?? null;
  const verifyLines = receipt?.lines ?? [];
  const [arena, bridge] = await Promise.all([probe(3200), probe(8787)]);
  let served: string | null = null;
  try {
    served = readFileSync(join(root, "served_commit.txt"), "utf8").trim() || null;
  } catch {
    served = null;
  }
  const stackOk = arena && bridge;
  const soakPids = verify?.soak_venv_pids?.trim() ?? "";
  const telegramState = verify?.telegram_state?.trim() ?? "UNKNOWN";
  return NextResponse.json({
    ok: stackOk,
    executionMode: "PAPER_ONLY",
    arenaPort: arena ? "OK" : "DOWN",
    bridgePort: bridge ? "OK" : "DOWN",
    servedCommit: served,
    soakVenvPids: soakPids.length ? soakPids.split(",").filter(Boolean) : [],
    telegramState,
    freeRamMb: verify?.free_ram_mb ? Number(verify.free_ram_mb) : null,
    verifyFile: verifyLines.length ? verifyLines.slice(-10) : null,
    verify,
    demo: false,
  });
}
