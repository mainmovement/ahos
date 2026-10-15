"use client";

import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";
import { Dialog as D } from "radix-ui";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = D.Root;
export const DialogTrigger = D.Trigger;
export const DialogClose = D.Close;
export const DialogTitle = D.Title;
export const DialogDescription = D.Description;

export const DialogContent = forwardRef<ElementRef<typeof D.Content>, ComponentPropsWithoutRef<typeof D.Content> & { hideClose?: boolean }>(function DialogContent(
  { className, children, hideClose, ...props },
  ref,
) {
  return (
    <D.Portal>
      <D.Overlay className="fixed inset-0 z-50 bg-ink-1000/70 backdrop-blur-[2px] animate-fade-in" />
      <D.Content
        ref={ref}
        className={cn(
          "glass-strong gold-border fixed inset-x-0 top-[14vh] z-50 mx-auto w-[min(640px,92vw)] rounded-[var(--radius-xl)] shadow-[var(--shadow-pop)] outline-none animate-rise-in",
          className,
        )}
        {...props}
      >
        {children}
        {!hideClose && (
          <D.Close className="absolute end-3 top-3 rounded-[var(--radius-sm)] p-1 text-fg-3 transition-colors hover:bg-[var(--surface-hover)] hover:text-fg-1" aria-label="Close">
            <X className="size-4" />
          </D.Close>
        )}
      </D.Content>
    </D.Portal>
  );
});

/** Side drawer that opens from the inline-end edge (left in RTL, right in LTR). */
export const SheetContent = forwardRef<ElementRef<typeof D.Content>, ComponentPropsWithoutRef<typeof D.Content> & { closeLabel?: string }>(function SheetContent(
  { className, children, closeLabel = "Close", ...props },
  ref,
) {
  return (
    <D.Portal>
      <D.Overlay className="fixed inset-0 z-50 bg-ink-1000/60 animate-fade-in" />
      <D.Content
        ref={ref}
        className={cn(
          "glass-strong gold-border fixed inset-y-2 end-2 z-50 flex w-[min(460px,94vw)] flex-col overflow-hidden rounded-[var(--radius-xl)] shadow-[var(--shadow-pop)] outline-none animate-rise-in",
          className,
        )}
        {...props}
      >
        {children}
        <D.Close className="absolute end-3 top-3 rounded-[var(--radius-sm)] p-1.5 text-fg-3 transition-colors hover:bg-[var(--surface-hover)] hover:text-fg-1" aria-label={closeLabel}>
          <X className="size-4" />
        </D.Close>
      </D.Content>
    </D.Portal>
  );
});
