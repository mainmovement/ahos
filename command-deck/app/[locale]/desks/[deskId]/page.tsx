import type { Metadata } from "next";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n";
import { DeskDetail } from "@/features/desks/desk-detail";
import { DESKS } from "@/lib/data/desks";

export function generateStaticParams() {
  return DESKS.map((desk) => ({ deskId: desk.id }));
}

export const dynamicParams = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; deskId: string }>;
}): Promise<Metadata> {
  const { locale, deskId } = await params;
  const dict = getDictionary(isLocale(locale) ? locale : "fa");
  const desk = DESKS.find((d) => d.id === deskId);
  return { title: desk ? desk.name[locale === "en" ? "en" : "fa"] : dict.desks.title };
}

export default async function DeskDetailPage({
  params,
}: {
  params: Promise<{ locale: string; deskId: string }>;
}) {
  const { deskId } = await params;
  return <DeskDetail deskId={deskId} />;
}
