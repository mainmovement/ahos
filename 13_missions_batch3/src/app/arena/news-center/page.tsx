// FILE: 13_missions_batch3/src/app/arena/news-center/page.tsx
import type { Metadata } from "next";
import { NewsCenterView } from "@/features/news-center/NewsCenterView";

export const metadata: Metadata = { title: "مرکز اخبار آرام" };

export default function Page() {
  return <NewsCenterView />;
}
