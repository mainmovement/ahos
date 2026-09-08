"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, MouseEvent, ReactNode } from "react";
import { useAudio } from "@/components/providers";

type Props = {
  href?: string;
  children: ReactNode;
  className?: string;
  tone?: "gold" | "ghost" | "plain";
  sound?: "click" | "enter" | "warn" | "success";
} & ButtonHTMLAttributes<HTMLButtonElement>;

export function SoundButton({ href, children, className = "", tone = "plain", sound = "click", onClick, type, ...rest }: Props) {
  const audio = useAudio();
  const toneClass = tone === "gold" ? "gold-btn" : tone === "ghost" ? "ghost-btn" : "";
  const cls = `sound-btn inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm ${toneClass} ${className}`;

  const onMove = (e: MouseEvent<HTMLElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty("--x", `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty("--y", `${e.clientY - r.top}px`);
  };

  if (href) {
    return (
      <Link
        href={href}
        className={cls}
        data-hot
        onMouseEnter={() => audio.play("hover")}
        onClick={() => audio.play(sound)}
        onMouseMove={onMove}
      >
        {children}
      </Link>
    );
  }

  return (
    <button
      type={type ?? "button"}
      className={cls}
      data-hot
      onMouseEnter={() => audio.play("hover")}
      onClick={(e) => {
        audio.play(sound);
        onClick?.(e);
      }}
      onMouseMove={onMove}
      {...rest}
    >
      {children}
    </button>
  );
}
