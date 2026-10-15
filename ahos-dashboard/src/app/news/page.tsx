import type { Metadata } from "next";
import { getNewsroom } from "@/lib/api/news";
import { NewsView } from "@/components/views/news-view";

export const metadata: Metadata = { title: "اتاق خبر · Newsroom" };

export default async function NewsPage() {
  return <NewsView news={await getNewsroom()} />;
}
