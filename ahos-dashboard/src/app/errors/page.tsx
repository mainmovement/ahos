import type { Metadata } from "next";
import { getErrors } from "@/lib/api/system";
import { ErrorsView } from "@/components/views/errors-view";

export const metadata: Metadata = { title: "خطاها و بازیابی · Errors & Recovery" };

export default async function ErrorsPage() {
  return <ErrorsView errors={await getErrors()} />;
}
