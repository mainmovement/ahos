import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { ReadinessGate } from "@/features/readiness/readiness-gate";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.readiness.title, description: dict.readiness.description };
}

export default async function ReadinessPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return (
    <>
      <PageHeader
        eyebrowLatin="Gold Readiness Gate"
        title={dict.readiness.title}
        description={dict.readiness.description}
      />
      <ReadinessGate />
    </>
  );
}
