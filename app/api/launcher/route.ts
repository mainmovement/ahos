import { authorizeDashboardEndpoint } from "@/web_api_auth";
import { isLoopbackRequest } from "@/chat_auth";
import { recordControlAudit } from "@/chat_control_gate";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

export const dynamic = "force-dynamic";

const STATUS_FILE = path.join(process.cwd(), "reports", "launcher", "status.json");
const LOCK_TTL_MS = 60_000;

// Components the orchestrator may be asked to leave out of a start.
const COMPONENTS = ["stores", "db_backend", "gateway", "telegram", "engine"] as const;

/**
 * The components the *previous* run explicitly excluded. A Restart must restore
 * the stack that was actually running, not silently widen it: the dashboard
 * button has no way to know the owner started with `--skip engine` (the one-click
 * smoke does, and so does any host where the engine is intentionally held back),
 * and re-booting an excluded component turns a ~15s restart into a 40+ minute
 * cold engine boot the owner never asked for. ``SKIPPED`` is the marker the
 * orchestrator writes for "skipped by request"; an absent or unhealthy component
 * is *not* carried over — Restart may legitimately retry one of those.
 */
async function priorSkips(): Promise<readonly string[]> {
  const raw = await readFile(STATUS_FILE, "utf8").catch(() => "");
  if (!raw) return [];
  let status: unknown;
  try {
    status = JSON.parse(raw);
  } catch {
    return [];
  }
  const components = (status as { components?: Record<string, unknown> } | null)
    ?.components;
  if (!components || typeof components !== "object") return [];
  return COMPONENTS.filter(
    (name) =>
      (components as Record<string, { status?: unknown }>)[name]?.status === "SKIPPED",
  );
}

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

// POST — stop | restart. The child is reparented outside this gateway's process
// tree: a stop/restart kills *this* process with `taskkill /T`, which fells every
// descendant, and the launcher child is the one pulling the trigger.
async function spawnLauncher(action: string, ps1: string, skipArgs: string[]): Promise<number | null> {
  // Node's own `detached: true` is not an escape on this host. Windows PowerShell
  // 5.1 started with DETACHED_PROCESS has no console host, so it exits 0 without
  // executing the script at all — verified by a four-variant matrix: the same
  // command with `detached: false` ran and exited 7, and with `detached: true`
  // exited 0 instantly and printed nothing. Worse, `detached` does not even break
  // process-tree parentage, so a detached child would still die under taskkill /T.
  // `Start-Process` (ShellExecute) reparents the worker onto a shell host instead —
  // verified with a heartbeat child that survived its own taskkill /T /F on its
  // launcher (its ppid became a shell host, not the spawning process).
  const inner = [
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
    "-File", ps1, "-Action", action, ...skipArgs,
  ];
  const argList = inner.map((a) => `'${a.replace(/'/g, "''")}'`).join(",");
  const command =
    `Start-Process -FilePath powershell.exe -ArgumentList @(${argList}) ` +
    `-WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id`;
  const chunks: Buffer[] = [];
  const child = spawn("powershell.exe", ["-NoProfile", "-Command", command], {
    cwd: process.cwd(),
    windowsHide: true,
    detached: false,
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stdout.on("data", (c: Buffer) => chunks.push(c));
  return new Promise<number | null>((resolve) => {
    let done = false;
    const finish = (pid: number | null) => {
      if (done) return;
      done = true;
      resolve(pid);
    };
    child.on("error", () => finish(null));
    child.on("exit", (code) => {
      if (code !== 0) return finish(null);
      const text = Buffer.concat(chunks).toString("utf8").trim();
      const first = text.split(/\s+/)[0];
      finish(/^\d+$/.test(first) ? Number(first) : null);
    });
    // The starter shell is a hidden wrapper that should return in well under a
    // second; never hold the response open on a wedged one.
    setTimeout(() => finish(null), 10_000);
  });
}

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
  const skipped = action === "restart" ? await priorSkips() : [];
  const skipArgs: string[] = [];
  for (const name of skipped) skipArgs.push("-Skip", name);
  const ps1 = path.join(process.cwd(), "launcher", "ahos.ps1");

  const pid = await spawnLauncher(action, ps1, skipArgs);
  if (pid === null) {
    recordControlAudit({
      surface: "engine_api",
      intent: action,
      capability: "ENGINE_CONTROL",
      decision: "FAILED",
      reason: "LAUNCHER_SPAWN_ERROR",
      channelClaimed: "dashboard_launcher_api",
    });
    if (lockToken === lockedAt) lockedAt = 0;
    return Response.json(
      { ok: false, error: "LAUNCHER_SPAWN_ERROR", hint: "rep parented launcher did not report a pid" },
      { status: 500 },
    );
  }

  // Fire and forget: the launcher may restart this very gateway, so the worker
  // was reparented outside our tree and its exit cannot be observed from here.
  // The lock therefore releases on the TTL below; the orchestrator is idempotent
  // per component, so a late second click reports ALREADY_RUNNING rather than
  // starting a second stack.
  recordControlAudit({
    surface: "engine_api",
    intent: action,
    capability: "ENGINE_CONTROL",
    decision: "CONFIRMED",
    reason: "EXECUTED_DASHBOARD_LAUNCHER_API",
    channelClaimed: "dashboard_launcher_api",
  });
  return Response.json({ ok: true, action, pid, skipped }, { status: 202 });
}
