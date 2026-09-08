"use client";

import { useRouter } from "next/navigation";
import { SoundButton } from "@/components/sound-button";

export function MarkRead({ id }: { id: number }) {
  const router = useRouter();
  return (
    <SoundButton
      tone="ghost"
      className="mt-3 !px-3 !py-1 text-xs"
      onClick={async () => {
        await fetch("/api/alerts", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id }),
        });
        router.refresh();
      }}
    >
      Mark read
    </SoundButton>
  );
}
