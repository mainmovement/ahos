import type { Metadata } from "next";
import { getPaperAccount } from "@/lib/api/paper";
import { PaperView } from "@/components/views/paper-view";

export const metadata: Metadata = { title: "معاملات کاغذی · Paper Trading" };

export default async function PaperTradingPage() {
  return <PaperView account={await getPaperAccount()} />;
}
