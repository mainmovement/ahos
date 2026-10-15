import type { Metadata } from "next";
import { getEarth } from "@/lib/api/org";
import { EarthView } from "@/components/views/earth-view";

export const metadata: Metadata = { title: "زمین و جهان · Earth & Global" };

export default async function EarthPage({ searchParams }: { searchParams: Promise<{ focus?: string }> }) {
  const [{ focus }, earth] = await Promise.all([searchParams, getEarth()]);
  return <EarthView earth={earth} initialFocus={focus === "iran" ? "iran" : "global"} />;
}
