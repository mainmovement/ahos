import type { Metadata } from "next";
import { getWorkshop } from "@/lib/api/org";
import { WorkshopView } from "@/components/views/workshop-view";

export const metadata: Metadata = { title: "کارگاه فناوری · Tech Workshop" };

export default async function WorkshopPage() {
  return <WorkshopView workshop={await getWorkshop()} />;
}
