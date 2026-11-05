import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { DatasetBanner } from "@/features/command-center/dataset-banner";
import { CommandStage } from "@/features/command-center/command-stage";
import { KpiGrid } from "@/features/command-center/kpi-grid";
import { ChartsSection } from "@/features/command-center/charts-section";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.command.title, description: dict.command.description };
}

export default async function CommandCenterPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");

  return (
    <>
      <PageHeader
        eyebrowLatin="Command Center"
        title={dict.command.title}
        description={dict.command.description}
      />
      <DatasetBanner />
      <CommandStage />
      <KpiGrid />
      <ChartsSection />
    </>
  );
}
