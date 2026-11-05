import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  body,
  action,
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  body?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 px-6 py-12 text-center", className)}>
      <span className="inline-flex size-12 items-center justify-center rounded-2xl border border-border bg-muted/40 text-muted-foreground">
        <Icon className="size-5" aria-hidden />
      </span>
      <div>
        <p className="text-sm font-bold">{title}</p>
        {body ? <p className="mt-1 max-w-sm text-xs leading-relaxed text-muted-foreground">{body}</p> : null}
      </div>
      {action}
    </div>
  );
}
