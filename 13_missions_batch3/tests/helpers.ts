// FILE: 13_missions_batch3/tests/helpers.ts
import fs from "node:fs";
import path from "node:path";
import { vi } from "vitest";

const CONTRACT_PATH = path.join(process.cwd(), "public", "contract", "ahos-arena-contract.example.json");

/** The shipped example contract (tests may read files; components may not). */
export function loadExample(): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8")) as Record<string, unknown>;
}

/** Deep clone of the example for mutation-based fixtures. */
export function cloneExample(): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8")) as Record<string, unknown>;
}

/** Point global fetch at a fixed JSON payload. */
export function mockFetch(payload: unknown, ok = true): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok,
      json: async () => payload,
    })),
  );
}

/** Point global fetch at a network failure. */
export function mockFetchFails(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("network down");
    }),
  );
}

/** All button + anchor texts currently rendered — used by the forbidden-control scan. */
export function controlTexts(container: HTMLElement): string[] {
  const nodes = container.querySelectorAll("button, a");
  return Array.from(nodes).map((n) => (n.textContent ?? "").trim());
}

/** Full visible body text. */
export function bodyText(container: HTMLElement): string {
  return container.textContent ?? "";
}
