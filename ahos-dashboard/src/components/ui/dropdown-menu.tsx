"use client";

import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";
import { DropdownMenu as D } from "radix-ui";
import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

export const DropdownMenu = D.Root;
export const DropdownMenuTrigger = D.Trigger;
export const DropdownMenuGroup = D.Group;
export const DropdownMenuRadioGroup = D.RadioGroup;

export const DropdownMenuContent = forwardRef<ElementRef<typeof D.Content>, ComponentPropsWithoutRef<typeof D.Content>>(function DropdownMenuContent(
  { className, sideOffset = 8, ...props },
  ref,
) {
  return (
    <D.Portal>
      <D.Content
        ref={ref}
        sideOffset={sideOffset}
        collisionPadding={10}
        className={cn("glass-strong gold-border z-50 min-w-[200px] overflow-hidden rounded-[var(--radius-lg)] p-1.5 text-sm text-fg-2 shadow-[var(--shadow-pop)] animate-fade-in", className)}
        {...props}
      />
    </D.Portal>
  );
});

export const DropdownMenuItem = forwardRef<ElementRef<typeof D.Item>, ComponentPropsWithoutRef<typeof D.Item>>(function DropdownMenuItem({ className, ...props }, ref) {
  return (
    <D.Item
      ref={ref}
      className={cn(
        "relative flex cursor-pointer select-none items-center gap-2 rounded-[var(--radius-sm)] px-2 py-1.5 outline-none transition-colors data-[disabled]:pointer-events-none data-[disabled]:opacity-45 data-[highlighted]:bg-[var(--surface-active)] data-[highlighted]:text-fg-1 [&_svg]:size-4 [&_svg]:text-fg-3",
        className,
      )}
      {...props}
    />
  );
});

export const DropdownMenuRadioItem = forwardRef<ElementRef<typeof D.RadioItem>, ComponentPropsWithoutRef<typeof D.RadioItem>>(function DropdownMenuRadioItem(
  { className, children, ...props },
  ref,
) {
  return (
    <D.RadioItem
      ref={ref}
      className={cn(
        "relative flex cursor-pointer select-none items-center gap-2 rounded-[var(--radius-sm)] py-1.5 pe-2 ps-7 outline-none transition-colors data-[highlighted]:bg-[var(--surface-active)] data-[highlighted]:text-fg-1",
        className,
      )}
      {...props}
    >
      <span className="absolute start-2 flex size-3.5 items-center justify-center">
        <D.ItemIndicator>
          <Circle className="size-2 fill-gold-400 text-gold-400" />
        </D.ItemIndicator>
      </span>
      {children}
    </D.RadioItem>
  );
});

export const DropdownMenuCheckboxItem = forwardRef<ElementRef<typeof D.CheckboxItem>, ComponentPropsWithoutRef<typeof D.CheckboxItem>>(function DropdownMenuCheckboxItem(
  { className, children, ...props },
  ref,
) {
  return (
    <D.CheckboxItem
      ref={ref}
      className={cn(
        "relative flex cursor-pointer select-none items-center gap-2 rounded-[var(--radius-sm)] py-1.5 pe-2 ps-7 outline-none transition-colors data-[highlighted]:bg-[var(--surface-active)] data-[highlighted]:text-fg-1",
        className,
      )}
      {...props}
    >
      <span className="absolute start-2 flex size-3.5 items-center justify-center">
        <D.ItemIndicator>
          <Check className="size-3.5 text-gold-300" />
        </D.ItemIndicator>
      </span>
      {children}
    </D.CheckboxItem>
  );
});

export function DropdownMenuLabel({ className, ...props }: ComponentPropsWithoutRef<typeof D.Label>) {
  return <D.Label className={cn("px-2 pb-1 pt-1.5 text-2xs font-medium text-fg-4", className)} {...props} />;
}

export function DropdownMenuSeparator({ className, ...props }: ComponentPropsWithoutRef<typeof D.Separator>) {
  return <D.Separator className={cn("hairline-x my-1.5", className)} {...props} />;
}
