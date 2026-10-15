import type { Metadata } from "next";
import { getMemory } from "@/lib/api/org";
import { MemoryView } from "@/components/views/memory-view";

export const metadata: Metadata = { title: "حافظه و یادگیری · Memory & Learning" };

export default async function MemoryPage() {
  return <MemoryView memory={await getMemory()} />;
}
