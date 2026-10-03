import { authorizeDashboardEndpoint, sanitizePublicError } from "@/web_api_auth";
import { isLoopbackRequest } from "@/chat_auth";
import { recordControlAudit } from "@/chat_control_gate";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

export const dynamic = "force-dynamic";

const STATUS_FILE = path.join(process.cwd(), "reports", "launcher", "status.json");
const LOCK_TTL_MS = 60_000;

// In-process guard so a double-click cannot start two launcher operations.
// A lock older than LOCK_TTL_MS is stale (a stop/restart is fire-and-forget and
// outlives this request), so it is ignored rather than blocking forever.
let lockedAt = 0;

// GET — read-only launcher status for the dashboard poll.
export async function GET(req: Request) {
  if (!isLoopbackRequest(req)) {
    return Response.json({ ok: false, error: "LOOPBACK_REQUIRED" }, { status: 403 });
  }
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;
  const raw = await readFile(STATUS_FILE, "utf8").catch(() => "");
  let status: unknown = null;
  if (raw) {
    try {
      status = JSON.parse(raw);
    } catch {
      status = null;
    }
  }
  return Response.json({ ok: true, status, staleAfterSec: 30 });
}

// POST — stop | restart. The child is hidden and detached so that stopping the
// gateway does not kill the stop itself.
export async function POST(req: Request) {
  if (!isLoopbackRequest(req)) {
    return Response.json({ ok: false, error: "LOOPBACK_REQUIRED" }, { status: 403 });
  }
  const denied = authorizeDashboardEndpoint(req);
  if (denied) return denied;
  const body = (await req.json().catch(() => ({}))) as { action?: string };
  const action = body.action;
  if (action !== "stop" && action !== "restart") {
    return Response.json({ ok: false, error: "BAD_ACTION" }, { status: 400 });
  }
  if (process.platform !== "win32") {
    return Response.json({ ok: false, error: "WINDOWS_ONLY_SURFACE" }, { status: 400 });
  }
  if (lockedAt && Date.now() - lockedAt < LOCK_TTL_MS) {
    return Response.json({ ok: false, error: "ALREADY_RUNNING" }, { status: 409 });
  }

  // Audit write-ahead: the chain may never say EXECUTING for something that
  // did not happen, and an action may never happen un-audited.
  const ahead = recordControlAudit({
    surface: "engine_api",
    intent: action,
    capability: "ENGINE_CONTROL",
    decision: "EXECUTING",
    reason: "AUDIT_WRITE_AHEAD_DASHBOARD_LAUNCHER_API",
    channelClaimed: "dashboard_launcher_api",
  });
  if (!ahead) {
    return Response.json(
      { ok: false, error: "AUDIT_WRITE_FAILED", hint: "control audit unavailable; action refused" },
      { status: 503 },
    );
  }

  lockedAt = Date.now();
  const lockToken = lockedAt;
  let child;
  try {
    child = spawn(
      "powershell.exe",
      ["-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", path.join(process.cwd(), "launcher", "ahos.ps1"), "-Action", action],
      { cwd: process.cwd(), windowsHide: true, detached: true, stdio: "ignore" },
    );
  } catch (error) {
    recordControlAudit({
      surface: "engine_api",
      intent: action,
      capability: "ENGINE_CONTROL",
      decision: "FAILED",
      reason: "LAUNCHER_SPAWN_ERROR",
      channelClaimed: "dashboard_launcher_api",
    });
    if (lockToken === lockedAt) lockedAt = 0;
    return Response.json({ ok: false, error: sanitizePublicError(error) }, { status: 500 });
  }

  // Fire and forget: the launcher may restart this very gateway, so the child
  // must outlive the response. The lock clears when the orchestrator exits, or
  // falls silent after LOCK_TTL_MS if this process never sees that event.
  const onSettled = (failed: boolean) => {
    if (lockToken !== lockedAt) return;
    lockedAt = 0;
    if (failed) {
      recordControlAudit({
        surface: "engine_api",
        intent: action,
        capability: "ENGINE_CONTROL",
        decision: "FAILED",
        reason: "LAUNCHER_SPAWN_ERROR",
        channelClaimed: "dashboard_launcher_api",
      });
    }
  };
  child.on("exit", () => onSettled(false));
  child.on("error", () => onSettled(true));
  child.unref();

  recordControlAudit({
    surface: "engine_api",
    intent: action,
    capability: "ENGINE_CONTROL",
    decision: "CONFIRMED",
    reason: "EXECUTED_DASHBOARD_LAUNCHER_API",
    channelClaimed: "dashboard_launcher_api",
  });
  return Response.json({ ok: true, action, pid: child.pid }, { status: 202 });
}
