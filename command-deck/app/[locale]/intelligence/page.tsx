import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { PageHeader } from "@/components/layout/page-header";
import { IntelligenceFeed } from "@/features/intelligence/intelligence-feed";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return { title: dict.intelligence.title, description: dict.intelligence.description };
}

export default async function IntelligencePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  return (
    <>
      <PageHeader
        eyebrowLatin="Drivers & News"
        title={dict.intelligence.title}
        description={dict.intelligence.description}
      />
      <IntelligenceFeed />
    </>
  );
}
