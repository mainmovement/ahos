import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { DesksGrid } from "@/features/desks/desks-grid";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.desks.title, description: dict.desks.description };
}

export default async function DesksPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return (
    <>
      <PageHeader eyebrowLatin="Intelligence Desks" title={dict.desks.title} description={dict.desks.description} />
      <DesksGrid />
    </>
  );
}
