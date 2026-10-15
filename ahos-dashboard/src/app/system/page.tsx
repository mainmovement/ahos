import type { Metadata } from "next";
import { getSystem } from "@/lib/api/system";
import { SystemView } from "@/components/views/system-view";

export const metadata: Metadata = { title: "سامانه و اجرا · System & Runtime" };

export default async function SystemPage() {
  return <SystemView system={await getSystem()} />;
}
