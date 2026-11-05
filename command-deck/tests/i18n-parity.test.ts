import { describe, expect, it } from "vitest";
import { fa } from "@/lib/i18n/dictionaries/fa";
import { en } from "@/lib/i18n/dictionaries/en";

function keyPaths(obj: unknown, prefix = ""): string[] {
  if (obj === null || typeof obj !== "object") return [prefix];
  return Object.entries(obj as Record<string, unknown>).flatMap(([k, v]) =>
    keyPaths(v, prefix ? `${prefix}.${k}` : k),
  );
}

describe("dictionary parity", () => {
  it("English has exactly the same key tree as Persian", () => {
    const faKeys = keyPaths(fa).sort();
    const enKeys = keyPaths(en).sort();
    expect(enKeys).toEqual(faKeys);
  });

  it("every leaf is a non-empty string", () => {
    const walk = (obj: unknown, path: string): void => {
      if (obj === null || typeof obj !== "object") {
        expect(typeof obj, `leaf ${path} must be a string`).toBe("string");
        expect((obj as string).length, `leaf ${path} must be non-empty`).toBeGreaterThan(0);
        return;
      }
      for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
        walk(v, path ? `${path}.${k}` : k);
      }
    };
    walk(fa, "fa");
    walk(en, "en");
  });
});
