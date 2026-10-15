import type { Metadata } from "next";
import { getDigitalWorld } from "@/lib/api/org";
import { DigitalWorldView } from "@/components/views/digital-world-view";

export const metadata: Metadata = { title: "جهان دیجیتال · Digital World" };

export default async function DigitalWorldPage() {
  return <DigitalWorldView dw={await getDigitalWorld()} />;
}
