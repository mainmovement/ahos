"use client";
import { tr } from "@/src/lib/i18n";

import { useEffect, useRef, useState } from "react";
import { copyText } from "../lib/copy";
import { CheckIcon, CopyIcon } from "./icons";

/**
 * Copy-ID action (allowed verb: copy). Transient «کپی شد» state.
 * Never anything more than a clipboard write.
 */
export function CopyIdButton({
  value,
  label,
  className = "",
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  return (
    <button
      type="button"
      className={`wh-focus inline-flex items-center gap-1 rounded-sm border border-line px-1.5 py-[1px] text-[12px] text-mute transition-colors hover:border-linestrong hover:text-gold ${className}`}
      aria-label={label ?? `کپی شناسه ${value}`}
      title={`کپی: ${value}`}
      onClick={(event) => {
        event.stopPropagation();
        void copyText(value).then((ok) => {
          if (!ok) return;
          setCopied(true);
          if (timer.current) clearTimeout(timer.current);
          timer.current = setTimeout(() => setCopied(false), 1_500);
        });
      }}
      data-copied={copied}
    >
      {copied ? <CheckIcon /> : <CopyIcon />}
      <span className="sr-only">{copied ? tr("fa", "whiteHats.ui.CopyIdButton_1") : tr("fa", "whiteHats.ui.CopyIdButton_2")}</span>
      {copied && <span className="text-gold">{tr("fa", "whiteHats.ui.CopyIdButton_1")}</span>}
    </button>
  );
}
