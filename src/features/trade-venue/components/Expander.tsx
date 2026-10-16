import type { ReactNode } from "react";

/** Native <details> expander: keyboard/AT accessible, no client state needed. */
export function Expander({
  id,
  title,
  meta,
  defaultOpen = false,
  children,
}: {
  id: string;
  title: string;
  meta?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  return (
    <details className="tv-expander" data-expander={id} open={defaultOpen}>
      <summary className="tv-expander__summary">
        <span className="tv-expander__title">{title}</span>
        {meta ? <span className="tv-expander__meta">{meta}</span> : null}
      </summary>
      <div className="tv-expander__body">{children}</div>
    </details>
  );
}
