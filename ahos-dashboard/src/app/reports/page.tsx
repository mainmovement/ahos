import type { Metadata } from "next";
import { getReports } from "@/lib/api/org";
import { ReportsView } from "@/components/views/reports-view";

export const metadata: Metadata = { title: "گزارش‌ها · Reports" };

export default async function ReportsPage() {
  return <ReportsView reports={await getReports()} />;
}
