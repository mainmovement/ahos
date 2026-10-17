// FILE: 13_missions_batch3/src/app/arena/skill-market/page.tsx
import type { Metadata } from "next";
import { SkillMarketView } from "@/features/skill-market/SkillMarketView";

export const metadata: Metadata = { title: "بازار مهارت و افزونه" };

export default function Page() {
  return <SkillMarketView />;
}
