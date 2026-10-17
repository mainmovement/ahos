// FILE: 13_missions_batch3/src/app/arena/self-debug/page.tsx
import type { Metadata } from "next";
import { SelfDebugView } from "@/features/self-debug/SelfDebugView";

export const metadata: Metadata = { title: "خطایابی خودکار" };

export default function Page() {
  return <SelfDebugView />;
}
