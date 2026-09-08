"use client";

import { useRouter } from "next/navigation";
import { SoundButton } from "@/components/sound-button";

export function PaperActions() {
  const router = useRouter();
  return (
    <div className="flex flex-wrap gap-3">
      <SoundButton
        tone="ghost"
        onClick={async () => {
          await fetch("/api/paper", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "mark" }) });
          router.refresh();
        }}
      >
        Mark to market
      </SoundButton>
    </div>
  );
}
