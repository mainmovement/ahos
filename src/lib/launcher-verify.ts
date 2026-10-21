import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export function parseVerifyReceipt(lines: string[]): Record<string, string> {
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

export function launcherDir(): string {
  return process.env.AHOS_LAUNCHER_DIR ?? join(process.cwd(), "..", "AHOS_Launcher");
}

export function readLauncherVerifyReceipt(): { lines: string[]; map: Record<string, string> } | null {
  const verifyPath = join(launcherDir(), "logs", "verify_stack_latest.txt");
  if (!existsSync(verifyPath)) return null;
  try {
    const lines = readFileSync(verifyPath, "utf8").split(/\r?\n/).filter(Boolean);
    return { lines, map: parseVerifyReceipt(lines) };
  } catch {
    return null;
  }
}

export function telegramHealthStatus(state: string | undefined): "LIVE" | "STALE" | "ERROR" | "UNKNOWN" {
  if (!state) return "UNKNOWN";
  if (state === "RUNNING") return "LIVE";
  if (state === "PREFLIGHT_FAIL") return "ERROR";
  if (state === "STOPPED" || state === "STOPPED_AFTER_PREFLIGHT_OK") return "STALE";
  return "UNKNOWN";
}
