import { db } from "@/db";
import { tokens } from "@/db/schema";
import { seedAhos } from "@/lib/seed";

let inflight: Promise<void> | null = null;

export async function ensureSeeded() {
  if (inflight) return inflight;
  inflight = (async () => {
    const existing = await db.select({ id: tokens.id }).from(tokens).limit(1);
    if (existing.length === 0) {
      await seedAhos();
    }
  })();
  try {
    await inflight;
  } finally {
    inflight = null;
  }
}
