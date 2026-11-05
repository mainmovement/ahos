import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * AHOS panel — the core surface of the design system. Padding follows the
 * density preference through --pad-card.
 */
const Panel = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("panel", className)} {...props} />
  ),
);
Panel.displayName = "Panel";

function PanelHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1.5 panel-pad pb-0", className)} {...props} />;
}

function PanelTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-base font-bold leading-tight", className)} {...props} />;
}

function PanelDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-xs text-muted-foreground leading-relaxed", className)} {...props} />;
}

function PanelContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("panel-pad", className)} {...props} />;
}

function PanelFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center gap-2 border-t border-border/70 panel-pad", className)}
      {...props}
    />
  );
}

export { Panel, PanelHeader, PanelTitle, PanelDescription, PanelContent, PanelFooter };
