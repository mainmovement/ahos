import localFont from "next/font/local";

/**
 * Fonts are bundled locally (public/fonts, OFL-1.1) — no runtime network.
 * Inter is restricted to the Latin unicode-range so Persian glyphs always
 * resolve to Vazirmatn while Latin text / numbers render in Inter.
 */
export const inter = localFont({
  src: "../../public/fonts/Inter-Variable-latin.woff2",
  variable: "--font-inter",
  weight: "100 900",
  style: "normal",
  display: "swap",
  preload: true,
  fallback: ["ui-sans-serif", "system-ui", "Segoe UI", "Arial"],
  declarations: [
    {
      prop: "unicode-range",
      value:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-205F, U+2070-209F, U+20AC, U+2122, U+2190-2199, U+2212, U+2215, U+FEFF, U+FFFD",
    },
  ],
});

export const vazirmatn = localFont({
  src: "../../public/fonts/Vazirmatn-Variable.woff2",
  variable: "--font-vazirmatn",
  weight: "100 900",
  style: "normal",
  display: "swap",
  preload: true,
  fallback: ["Tahoma", "ui-sans-serif", "system-ui", "Arial"],
});
