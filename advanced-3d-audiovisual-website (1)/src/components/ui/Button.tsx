"use client";

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useAudio } from "@/components/system/AudioProvider";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  href?: string;
  icon?: ReactNode;
  iconRight?: ReactNode;
  soundOnHover?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-cyan-300 via-teal-300 to-violet-400 text-slate-950 shadow-[0_0_30px_-6px_rgba(53,240,208,0.65)] hover:shadow-[0_0_44px_-4px_rgba(139,123,255,0.75)]",
  secondary: "glass text-slate-100 hover:border-cyan-300/50",
  outline: "border border-white/15 text-slate-100 hover:border-cyan-300/60 hover:bg-white/5",
  ghost: "text-slate-300 hover:text-cyan-200 hover:bg-white/5",
  danger: "bg-gradient-to-r from-rose-500 to-pink-500 text-white shadow-[0_0_28px_-6px_rgba(255,77,109,0.6)]",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-3.5 py-1.5 text-xs gap-1.5",
  md: "px-5 py-2.5 text-sm gap-2",
  lg: "px-7 py-3.5 text-base gap-2.5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", href, icon, iconRight, soundOnHover = true, onClick, onMouseEnter, children, ...props },
  ref
) {
  const { play } = useAudio();

  const classes = cn(
    "relative inline-flex items-center justify-center rounded-full font-medium tracking-tight transition-all duration-200 will-change-transform",
    "active:scale-[0.96] disabled:opacity-40 disabled:pointer-events-none",
    variantClasses[variant],
    sizeClasses[size],
    className
  );

  const handleEnter: React.MouseEventHandler<HTMLButtonElement> = (e) => {
    if (soundOnHover) play.hover();
    onMouseEnter?.(e);
  };

  const handleClick: React.MouseEventHandler<HTMLButtonElement> = (e) => {
    play.click();
    onClick?.(e);
  };

  const content = (
    <>
      {icon}
      <span>{children}</span>
      {iconRight}
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        data-cursor-interactive
        className={classes}
        onMouseEnter={() => soundOnHover && play.hover()}
        onClick={() => play.click()}
      >
        {content}
      </Link>
    );
  }

  return (
    <button ref={ref} data-cursor-interactive className={classes} onMouseEnter={handleEnter} onClick={handleClick} {...props}>
      {content}
    </button>
  );
});
