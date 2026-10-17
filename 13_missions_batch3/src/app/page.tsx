// FILE: 13_missions_batch3/src/app/page.tsx
import { redirect } from "next/navigation";

/** All routes live under /arena/* — the index just enters the first page. */
export default function IndexPage() {
  redirect("/arena/science-radar");
}
