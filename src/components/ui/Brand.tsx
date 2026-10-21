export const LION_SUN_TRANSPARENT_SRC =
  "/brand/logo/ahos-lion-sun-transparent.png";

export type BrandMarkVariant = "sidebar" | "orbit" | "splash";

const variantClass: Record<BrandMarkVariant, string> = {
  sidebar: "ah-brand-mark ah-brand-mark--sidebar",
  orbit: "ah-brand-mark ah-brand-mark--orbit",
  splash: "ah-brand-mark ah-brand-mark--splash",
};

type LionSunMarkProps = {
  className?: string;
  variant?: BrandMarkVariant;
  /** When true, hide from assistive tech (use beside visible AHOS wordmark). */
  decorative?: boolean;
};

export function LionSunMark({
  className = "",
  variant = "sidebar",
  decorative = true,
}: LionSunMarkProps) {
  const size = variant === "orbit" ? 87 : variant === "splash" ? 120 : 42;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={`${variantClass[variant]} ${className}`.trim()}
      src={LION_SUN_TRANSPARENT_SRC}
      width={size}
      height={size}
      alt={decorative ? "" : "AHOS Lion and Sun logo"}
      aria-hidden={decorative ? true : undefined}
      decoding="async"
      draggable={false}
    />
  );
}

/** Primary AHOS brand mark (Lion & Sun). Replaces the legacy gold star in shell UI. */
export function StarMark({
  className = "",
  variant = "sidebar",
}: {
  className?: string;
  variant?: BrandMarkVariant;
}) {
  return <LionSunMark className={className} variant={variant} decorative />;
}
