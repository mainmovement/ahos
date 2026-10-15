import type { Metadata } from "next";
import { getUniversity } from "@/lib/api/university";
import { UniversityView } from "@/components/views/university-view";

export const metadata: Metadata = { title: "دانشگاه · University" };

export default async function UniversityPage() {
  return <UniversityView uni={await getUniversity()} />;
}
