import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { HealthBoard } from "@/features/health/health-board";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.health.title, description: dict.health.description };
}

export default async function HealthPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return (
    <>
      <PageHeader eyebrowLatin="System Health" title={dict.health.title} description={dict.health.description} />
      <HealthBoard />
    </>
  );
}
