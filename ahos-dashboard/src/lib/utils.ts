import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** shadcn-style class combiner (clsx + tailwind-merge). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Narrow unknown to a finite number. */
export function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** Last element of an array (typed for noUncheckedIndexedAccess). */
export function last<T>(items: readonly T[]): T | undefined {
  return items.length ? items[items.length - 1] : undefined;
}

/** Percentage change between two numbers, or null when undefined. */
export function pctChange(from: number | undefined, to: number | undefined): number | null {
  if (!isFiniteNumber(from) || !isFiniteNumber(to) || from === 0) return null;
  return ((to - from) / Math.abs(from)) * 100;
}

export function sum(values: readonly number[]): number {
  let total = 0;
  for (const v of values) total += v;
  return total;
}

export function shortenAddress(address: string, head = 6, tail = 4): string {
  if (address.length <= head + tail + 1) return address;
  return `${address.slice(0, head)}…${address.slice(-tail)}`;
}
