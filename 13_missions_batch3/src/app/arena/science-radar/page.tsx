// FILE: 13_missions_batch3/src/app/arena/science-radar/page.tsx
import type { Metadata } from "next";
import { ScienceRadarView } from "@/features/science-radar/ScienceRadarView";

export const metadata: Metadata = { title: "رادار علم" };

export default function Page() {
  return <ScienceRadarView />;
}
