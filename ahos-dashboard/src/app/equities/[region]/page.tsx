import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { EQUITY_REGIONS, getEquities, isEquityRegion } from "@/lib/api/equities";
import { EquitiesView } from "@/components/views/equities-view";

const TITLES = { us: "سهام آمریکا · US Equities", eu: "سهام اروپا · EU Equities", asia: "سهام آسیا · Asia Equities" } as const;

export const dynamicParams = false;

export function generateStaticParams() {
  return EQUITY_REGIONS.map((region) => ({ region }));
}

export async function generateMetadata({ params }: { params: Promise<{ region: string }> }): Promise<Metadata> {
  const { region } = await params;
  return { title: isEquityRegion(region) ? TITLES[region] : "Equities" };
}

export default async function EquitiesPage({ params }: { params: Promise<{ region: string }> }) {
  const { region } = await params;
  if (!isEquityRegion(region)) notFound();
  return <EquitiesView board={await getEquities(region)} />;
}
