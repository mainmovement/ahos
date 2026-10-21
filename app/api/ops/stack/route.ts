import { NextResponse } from "next/server";
import { readFileSync, existsSync } from "node:fs";
import { connect } from "node:net";
import { join } from "node:path";

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

function parseVerifyReceipt(lines: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of lines) {
    const normalized = line.replace(/^\uFEFF/, "");
    const i = normalized.indexOf("=");
    if (i < 0) {
      out[normalized] = "true";
      continue;
    }
    out[normalized.slice(0, i)] = normalized.slice(i + 1);
  }
  return out;
}

/** Read-only ops snapshot (ports + launcher verify file if present). */
export async function GET() {
  const launcherDir = process.env.AHOS_LAUNCHER_DIR ?? join(process.cwd(), "..", "AHOS_Launcher");
  const verifyPath = join(launcherDir, "logs", "verify_stack_latest.txt");
  let verifyLines: string[] = [];
  let verify: Record<string, string> | null = null;
  if (existsSync(verifyPath)) {
    try {
      verifyLines = readFileSync(verifyPath, "utf8").split(/\r?\n/).filter(Boolean);
      verify = parseVerifyReceipt(verifyLines);
    } catch {
      verifyLines = [];
    }
  }
  const [arena, bridge] = await Promise.all([probe(3200), probe(8787)]);
  let served: string | null = null;
  try {
    served = readFileSync(join(launcherDir, "served_commit.txt"), "utf8").trim() || null;
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
