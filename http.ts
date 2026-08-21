import { createHash } from "crypto";
import type { Envelope, ProviderStatus } from "./types";

const UA =
  "AHOS-CommandCenter/1.0 (local-laptop; evidence-first; https://github.com/mainmovement/ahos)";

export function sha1(input: string): string {
  return createHash("sha1").update(input).digest("hex");
}

/**
 * Adaptive timeout: discovery/news can fail fast; market core gets a bit more room.
 * Never fabricates data on timeout — returns DOWN with honest latency.
 */
function defaultTimeout(category: string): number {
  if (category === "discovery") return 7000;
  if (category === "news") return 8000;
  if (category === "security") return 9000;
  return 8500;
}

export async function fetchJson<T>(
  provider: string,
  category: string,
  url: string,
  options?: {
    timeoutMs?: number;
    headers?: Record<string, string>;
    statusOverride?: ProviderStatus;
  },
): Promise<Envelope<T>> {
  if (options?.statusOverride) {
    return makeEnvelope<T>(provider, category, options.statusOverride, 0, url, 0, null);
  }

  const started = Date.now();
  const timeoutMs = options?.timeoutMs ?? defaultTimeout(category);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        Accept: "application/json, text/xml, application/rss+xml, text/plain, */*",
        "User-Agent": UA,
        ...(options?.headers ?? {}),
      },
      cache: "no-store",
    });
    const latencyMs = Date.now() - started;
    if (res.status === 401 || res.status === 403) {
      return makeEnvelope<T>(provider, category, "AUTH_REQUIRED", latencyMs, url, 0, null);
    }
    if (res.status === 429) {
      return makeEnvelope<T>(provider, category, "RATE_LIMIT", latencyMs, url, 0, null);
    }
    if (res.status === 404) {
      return makeEnvelope<T>(provider, category, "NO_DATA", latencyMs, url, 0, null);
    }
    if (!res.ok) {
      return makeEnvelope<T>(provider, category, "DOWN", latencyMs, url, 0, null);
    }
    const ctype = res.headers.get("content-type") || "";
    const text = await res.text();
    if (!text.trim()) {
      return makeEnvelope<T>(provider, category, "NO_DATA", latencyMs, url, 0, null);
    }
    if (ctype.includes("json") || text.trim().startsWith("{") || text.trim().startsWith("[")) {
      try {
        const data = JSON.parse(text) as T;
        const itemCount = countItems(data);
        if (itemCount === 0) {
          return makeEnvelope<T>(provider, category, "NO_DATA", latencyMs, url, 0, data);
        }
        return makeEnvelope<T>(provider, category, "SUCCESS", latencyMs, url, itemCount, data);
      } catch {
        return makeEnvelope<T>(provider, category, "DOWN", latencyMs, url, 0, null, "پاسخ JSON نامعتبر بود");
      }
    }
    return makeEnvelope<T>(provider, category, "SUCCESS", latencyMs, url, 1, text as T);
  } catch (error) {
    const latencyMs = Date.now() - started;
    const name = error instanceof Error ? error.name : "";
    if (name === "AbortError") {
      return makeEnvelope<T>(provider, category, "DOWN", latencyMs, url, 0, null, "زمان درخواست تمام شد");
    }
    return makeEnvelope<T>(provider, category, "DOWN", latencyMs, url, 0, null);
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchText(
  provider: string,
  category: string,
  url: string,
  timeoutMs = 8000,
): Promise<Envelope<string>> {
  return fetchJson<string>(provider, category, url, { timeoutMs });
}

function makeEnvelope<T>(
  provider: string,
  category: string,
  status: ProviderStatus,
  latencyMs: number,
  url: string,
  itemCount: number,
  data: T | null,
  extraFa?: string,
): Envelope<T> {
  return {
    provider,
    category,
    status,
    latencyMs,
    fetchedAt: new Date().toISOString(),
    url,
    itemCount,
    messageFa: extraFa || statusFa(status),
    messageEn: status,
    data,
  };
}

export function statusFa(status: ProviderStatus): string {
  switch (status) {
    case "SUCCESS":
      return "داده واقعی دریافت شد";
    case "NO_DATA":
      return "پاسخ خالی — NO_DATA";
    case "AUTH_REQUIRED":
      return "نیاز به احراز هویت — AUTH_REQUIRED";
    case "COST_BLOCKED":
      return "مسیر پولی / بدون کلید — COST_BLOCKED";
    case "RATE_LIMIT":
      return "محدودیت نرخ — RATE_LIMIT";
    case "DOWN":
      return "در دسترس نیست — DOWN";
    case "OUT_OF_POLICY":
      return "خارج از سیاست مجاز — OUT_OF_POLICY";
    case "UNSUPPORTED":
      return "پشتیبانی نمی‌شود — UNSUPPORTED";
    case "NO_KEY":
      return "کلید پیکربندی نشده — NO_KEY";
    default:
      return "نامشخص — UNKNOWN";
  }
}

function countItems(data: unknown): number {
  if (Array.isArray(data)) return data.length;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    for (const key of ["pairs", "data", "coins", "articles", "items", "result", "assets", "posts"]) {
      if (Array.isArray(obj[key])) return (obj[key] as unknown[]).length;
    }
    return Object.keys(obj).length > 0 ? 1 : 0;
  }
  return data ? 1 : 0;
}

export function envKey(name: string): string | null {
  const v = process.env[name];
  if (!v || !v.trim()) return null;
  return v.trim();
}
