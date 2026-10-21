import { readFileSync } from "node:fs";
import { join } from "node:path";
import { SOAK_DIR } from "../../missions-b5/lib/data.server";
import type { NewsroomSnapshot } from "./types";
import { buildSoakNewsroomSnapshot } from "./soak-snapshot";

export function readSoakNewsroomSnapshot(): NewsroomSnapshot | null {
  const path = join(SOAK_DIR, "soak_status.json");
  try {
    const soak = JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
    return buildSoakNewsroomSnapshot(soak);
  } catch {
    return null;
  }
}
