import type { Metadata } from "next";
import { getSecurity } from "@/lib/api/security";
import { SecurityView } from "@/components/views/security-view";

export const metadata: Metadata = { title: "مرکز امنیت · Security Center" };

export default async function SecurityPage() {
  return <SecurityView security={await getSecurity()} />;
}
