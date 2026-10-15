import type { Metadata } from "next";
import { getOil } from "@/lib/api/commodities";
import { OilView } from "@/components/views/commodities-view";

export const metadata: Metadata = { title: "نفت · Oil" };

export default async function OilPage() {
  return <OilView oil={await getOil()} />;
}
