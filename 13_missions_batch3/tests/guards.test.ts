// FILE: 13_missions_batch3/tests/guards.test.ts
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

const SRC = path.join(process.cwd(), "src");

describe("source guards (grep tests)", () => {
  it("components/features/app never import @/mock/* or the contract JSON", () => {
    const dirs = ["components", "features", "app"].map((d) => path.join(SRC, d));
    const files = dirs.flatMap((d) => walk(d));
    const offenders: string[] = [];
    for (const file of files) {
      const text = fs.readFileSync(file, "utf8");
      if (text.includes("@/mock") || text.includes("ahos-arena-contract.example.json")) {
        offenders.push(file);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("adapters read data only through the shared _contract loader", () => {
    const adapterDir = path.join(SRC, "adapters");
    for (const file of walk(adapterDir)) {
      if (file.endsWith("_contract.ts")) continue;
      const text = fs.readFileSync(file, "utf8");
      if (!file.endsWith(".ts")) continue;
      // page adapters must not fetch the JSON themselves
      expect(text.includes("ahos-arena-contract.example.json"), file).toBe(false);
    }
  });

  it("no font size below 12px anywhere in CSS or inline styles", () => {
    const files = walk(SRC);
    const offenders: string[] = [];
    for (const file of files) {
      const text = fs.readFileSync(file, "utf8");
      if (file.endsWith(".css")) {
        for (const m of text.matchAll(/font-size:\s*([0-9.]+)px/g)) {
          if (parseFloat(m[1]) < 12) offenders.push(`${file}: ${m[0]}`);
        }
        for (const m of text.matchAll(/font-size:\s*([0-9.]+)rem/g)) {
          if (parseFloat(m[1]) * 16 < 12) offenders.push(`${file}: ${m[0]}`);
        }
      }
      if (file.endsWith(".tsx") || file.endsWith(".ts")) {
        for (const m of text.matchAll(/fontSize:\s*"?([0-9.]+)px?"?/g)) {
          if (parseFloat(m[1]) < 12) offenders.push(`${file}: ${m[0]}`);
        }
        for (const m of text.matchAll(/text-\[([0-9.]+)px\]/g)) {
          if (parseFloat(m[1]) < 12) offenders.push(`${file}: ${m[0]}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it("exports the required shared component names", () => {
    const shell = fs.readFileSync(path.join(SRC, "components", "shell", "Shell.tsx"), "utf8");
    const truth = fs.readFileSync(path.join(SRC, "components", "truth", "TruthChip.tsx"), "utf8");
    const tier = fs.readFileSync(path.join(SRC, "components", "truth", "TierChip.tsx"), "utf8");
    const clock = fs.readFileSync(path.join(SRC, "components", "shell", "TehranClock.tsx"), "utf8");
    const violation = fs.readFileSync(path.join(SRC, "components", "shell", "ViolationBar.tsx"), "utf8");
    const telemetry = fs.readFileSync(path.join(SRC, "components", "shell", "TelemetryStrip.tsx"), "utf8");
    expect(shell).toContain("export function Shell(");
    expect(shell).toContain("export interface ShellProps");
    expect(truth).toContain("export function TruthChip(");
    expect(tier).toContain("export function TierChip(");
    expect(clock).toContain("export function TehranClock(");
    expect(violation).toContain("export function ViolationBar(");
    expect(telemetry).toContain("export function TelemetryStrip(");
  });

  it("Persian text is real UTF-8 Persian, not transliterated", () => {
    const shell = fs.readFileSync(path.join(SRC, "components", "shell", "Shell.tsx"), "utf8");
    expect(shell).toContain("فقط کاغذی");
    expect(shell).toContain("رادار علم");
    expect(/[\u0600-\u06FF]/.test(shell)).toBe(true);
  });
});
