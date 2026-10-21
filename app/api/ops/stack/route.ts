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

/** Read-only ops snapshot (ports + launcher verify file if present). */
export async function GET() {
  const launcherDir = process.env.AHOS_LAUNCHER_DIR ?? join(process.cwd(), "..");
  const verifyPath = join(launcherDir, "logs", "verify_stack_latest.txt");
  let verifyLines: string[] = [];
  if (existsSync(verifyPath)) {
    try {
      verifyLines = readFileSync(verifyPath, "utf8").split(/\r?\n/).filter(Boolean).slice(-8);
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
  return NextResponse.json({
    ok: arena && bridge,
    executionMode: "PAPER_ONLY",
    arenaPort: arena ? "OK" : "DOWN",
    bridgePort: bridge ? "OK" : "DOWN",
    servedCommit: served,
    verifyFile: existsSync(verifyPath) ? verifyLines : null,
    demo: false,
  });
}
