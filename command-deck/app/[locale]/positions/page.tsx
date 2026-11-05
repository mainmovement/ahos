import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { PositionsTable } from "@/features/positions/positions-table";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.positions.title, description: dict.positions.description };
}

export default async function PositionsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return (
    <>
      <PageHeader
        eyebrowLatin="Positions & Trades"
        title={dict.positions.title}
        description={dict.positions.description}
      />
      <PositionsTable />
    </>
  );
}
