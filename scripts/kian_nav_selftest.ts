import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

test("navigation declares arena routes for Kian and Newsroom", () => {
  const nav = readFileSync(join(import.meta.dirname, "..", "src", "lib", "navigation.ts"), "utf8");
  assert.match(nav, /id:\s*"kian"[\s\S]*?href:\s*"\/arena\/kian"/);
  assert.match(nav, /id:\s*"news"[\s\S]*?href:\s*"\/arena\/newsroom"/);
});
