import type { Metadata } from "next";
import { getGold } from "@/lib/api/commodities";
import { GoldView } from "@/components/views/commodities-view";

export const metadata: Metadata = { title: "طلا · Gold" };

export default async function GoldPage() {
  return <GoldView gold={await getGold()} />;
}
