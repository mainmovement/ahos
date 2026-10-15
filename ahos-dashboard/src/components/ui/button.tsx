import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "relative inline-flex select-none items-center justify-center gap-1.5 whitespace-nowrap font-medium transition-[background-color,border-color,color,box-shadow,opacity] duration-[var(--dur-fast)] ease-out disabled:pointer-events-none disabled:opacity-45 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        gold: "bg-[image:var(--gradient-gold)] text-ink-950 shadow-[var(--shadow-glow-sm)] hover:shadow-[var(--shadow-glow-md)] hover:brightness-105",
        outline: "border border-[var(--line-hairline)] bg-ink-900/40 text-fg-2 hover:border-gold-500/50 hover:text-fg-1 hover:bg-[var(--surface-hover)]",
        ghost: "text-fg-3 hover:text-fg-1 hover:bg-[var(--surface-hover)]",
        subtle: "bg-white/[0.04] text-fg-2 hover:bg-white/[0.07] hover:text-fg-1",
        active: "bg-[var(--surface-active)] text-gold-200 shadow-[inset_0_0_0_1px_rgb(230_191_95/0.28)]",
        danger: "border border-down/40 bg-down/10 text-down hover:bg-down/15",
      },
      size: {
        xs: "h-6 rounded-[var(--radius-sm)] px-2 text-2xs [&_svg]:size-3",
        sm: "h-7 rounded-[var(--radius-sm)] px-2.5 text-xs [&_svg]:size-3.5",
        md: "h-8 rounded-[var(--radius-md)] px-3 text-sm [&_svg]:size-4",
        lg: "h-10 rounded-[var(--radius-md)] px-4 text-base [&_svg]:size-4",
        icon: "size-8 rounded-[var(--radius-md)] [&_svg]:size-4",
        "icon-sm": "size-7 rounded-[var(--radius-sm)] [&_svg]:size-3.5",
        "icon-xs": "size-6 rounded-[var(--radius-xs)] [&_svg]:size-3",
      },
    },
    defaultVariants: { variant: "outline", size: "md" },
  },
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button({ className, variant, size, asChild, type, ...props }, ref) {
  const Comp = asChild ? Slot.Root : "button";
  return <Comp ref={ref} type={asChild ? undefined : (type ?? "button")} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
});
