import type { DataEnvelope, Newsroom } from "./types";
import { fromMock, label } from "./_envelope";
import { mockNews } from "@/mock/news";

/** Newsroom. Real source: AHOS `news.ts` pipeline (RSS + MyMemory translation + provenance). */
export async function getNewsroom(): Promise<DataEnvelope<Newsroom>> {
  return fromMock(mockNews(), "news", label("اتاق خبر نمایشی", "Demo newsroom"), 90, 600);
}
