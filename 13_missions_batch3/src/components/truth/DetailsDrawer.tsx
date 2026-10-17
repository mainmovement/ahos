// FILE: 13_missions_batch3/src/components/truth/DetailsDrawer.tsx
"use client";
import type { ReactNode } from "react";

export interface DetailsDrawerProps {
  open: boolean;
  onToggle: () => void;
  title?: string;
  children: ReactNode;
}

/**
 * «جزئیات» drawer — the only interaction a read-only page offers besides
 * filters and copy-ID. A view control; it mutates nothing.
 */
export function DetailsDrawer({ open, onToggle, title = "جزئیات", children }: DetailsDrawerProps) {
  return (
    <div>
      <button type="button" className="ah-btn ah-btn-ghost" onClick={onToggle} aria-expanded={open}>
        {open ? `بستن ${title}` : title}
      </button>
      {open ? (
        <div className="ah-drawer" data-testid="details-drawer">
          <div className="ah-drawer-body">{children}</div>
        </div>
      ) : null}
    </div>
  );
}
