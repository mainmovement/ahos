import type { Metadata } from "next";
import { getPortfolio } from "@/lib/api/paper";
import { PortfolioView } from "@/components/views/portfolio-view";

export const metadata: Metadata = { title: "سبد دارایی · Portfolio" };

export default async function PortfolioPage() {
  return <PortfolioView portfolio={await getPortfolio()} />;
}
