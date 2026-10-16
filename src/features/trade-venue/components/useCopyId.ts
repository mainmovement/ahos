"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * «کپی شناسه» — copy an id to the clipboard, with a short confirmation state.
 * Copying an identifier is a read-only verb; it never mutates anything server
 * side. Falls back to a hidden textarea when the async clipboard API is not
 * available (non-secure contexts, older engines).
 */
export function useCopyId(resetMs = 1500) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [failedId, setFailedId] = useState<string | null>(null);

  useEffect(() => {
    if (!copiedId && !failedId) return;
    const timer = window.setTimeout(() => {
      setCopiedId(null);
      setFailedId(null);
    }, resetMs);
    return () => window.clearTimeout(timer);
  }, [copiedId, failedId, resetMs]);

  const copy = useCallback(async (value: string) => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
        setCopiedId(value);
        return true;
      }
      throw new Error("clipboard-unavailable");
    } catch {
      try {
        const area = document.createElement("textarea");
        area.value = value;
        area.setAttribute("readonly", "true");
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(area);
        if (ok) {
          setCopiedId(value);
          return true;
        }
      } catch {
        /* fall through to the failure state */
      }
      setFailedId(value);
      return false;
    }
  }, []);

  return { copy, copiedId, failedId };
}
