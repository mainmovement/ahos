export type Locale = "fa" | "en";
export type QualityProfile = "high" | "balanced" | "low";
export type MotionPreference = "system" | "full" | "reduced";
export type ThemeId = "gold" | "contrast";
export type DigitMode = "latin" | "persian";

export interface Settings {
  locale: Locale;
  quality: QualityProfile;
  motion: MotionPreference;
  theme: ThemeId;
  digits: DigitMode;
  /** Master mute — audio is muted by default. */
  muted: boolean;
  volume: number;
  uiSounds: boolean;
  ambient: boolean;
  sidebarCollapsed: boolean;
  assistantCollapsed: boolean;
}

export const DEFAULT_SETTINGS: Settings = {
  locale: "fa",
  quality: "high",
  motion: "system",
  theme: "gold",
  digits: "latin",
  muted: true,
  volume: 0.5,
  uiSounds: true,
  ambient: false,
  sidebarCollapsed: false,
  assistantCollapsed: false,
};

export const STORAGE_KEY = "ahos.settings.v1";
export const COOKIE_KEY = "ahos_prefs";

/** Subset mirrored into a cookie so the server can render the right <html> attributes. */
export type CookieSettings = Pick<Settings, "locale" | "quality" | "motion" | "theme" | "digits" | "sidebarCollapsed" | "assistantCollapsed">;

const QUALITY: QualityProfile[] = ["high", "balanced", "low"];
const MOTION: MotionPreference[] = ["system", "full", "reduced"];

/** Defensive parse of untrusted persisted settings. */
export function sanitizeSettings(raw: unknown): Partial<Settings> {
  if (!raw || typeof raw !== "object") return {};
  const r = raw as Record<string, unknown>;
  const out: Partial<Settings> = {};
  if (r.locale === "fa" || r.locale === "en") out.locale = r.locale;
  if (typeof r.quality === "string" && (QUALITY as string[]).includes(r.quality)) out.quality = r.quality as QualityProfile;
  if (typeof r.motion === "string" && (MOTION as string[]).includes(r.motion)) out.motion = r.motion as MotionPreference;
  if (r.theme === "gold" || r.theme === "contrast") out.theme = r.theme;
  if (r.digits === "latin" || r.digits === "persian") out.digits = r.digits;
  if (typeof r.muted === "boolean") out.muted = r.muted;
  if (typeof r.volume === "number" && r.volume >= 0 && r.volume <= 1) out.volume = r.volume;
  if (typeof r.uiSounds === "boolean") out.uiSounds = r.uiSounds;
  if (typeof r.ambient === "boolean") out.ambient = r.ambient;
  if (typeof r.sidebarCollapsed === "boolean") out.sidebarCollapsed = r.sidebarCollapsed;
  if (typeof r.assistantCollapsed === "boolean") out.assistantCollapsed = r.assistantCollapsed;
  return out;
}

export function parseCookieSettings(value: string | undefined): Partial<Settings> {
  if (!value) return {};
  try {
    return sanitizeSettings(JSON.parse(decodeURIComponent(value)));
  } catch {
    return {};
  }
}

export function serializeCookieSettings(s: Settings): string {
  const subset: CookieSettings = {
    locale: s.locale,
    quality: s.quality,
    motion: s.motion,
    theme: s.theme,
    digits: s.digits,
    sidebarCollapsed: s.sidebarCollapsed,
    assistantCollapsed: s.assistantCollapsed,
  };
  return encodeURIComponent(JSON.stringify(subset));
}

/** What each quality profile controls (read by globe, particles, charts). */
export interface QualityBudget {
  pixelRatioCap: number;
  renderScale: number;
  bloom: boolean;
  stars: number;
  particles: number;
  textureSize: number;
  geoDetail: "50m" | "110m";
  cityLights: number;
  antialias: boolean;
  fpsCap: number;
}

export const QUALITY_BUDGETS: Record<QualityProfile, QualityBudget> = {
  high: { pixelRatioCap: 2, renderScale: 1, bloom: true, stars: 3200, particles: 70, textureSize: 4096, geoDetail: "50m", cityLights: 1, antialias: true, fpsCap: 60 },
  balanced: { pixelRatioCap: 1.5, renderScale: 0.85, bloom: false, stars: 1500, particles: 30, textureSize: 2048, geoDetail: "110m", cityLights: 0.7, antialias: true, fpsCap: 60 },
  low: { pixelRatioCap: 1, renderScale: 0.7, bloom: false, stars: 500, particles: 0, textureSize: 1024, geoDetail: "110m", cityLights: 0.45, antialias: false, fpsCap: 30 },
};
