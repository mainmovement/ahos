// FILE: 13_missions_batch3/src/app/arena/weekly-exam/page.tsx
import type { Metadata } from "next";
import { WeeklyExamView } from "@/features/weekly-exam/WeeklyExamView";

export const metadata: Metadata = { title: "آزمون هفتگی هوش" };

export default function Page() {
  return <WeeklyExamView />;
}
