export function StarMark({ className = "" }: { className?: string }) {
  // Gold star from the AHOS brand pack (public/brand/logo/ahos-star-gold.svg).
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      className={className}
      src="/brand/logo/ahos-star-gold.svg"
      width={42}
      height={42}
      alt=""
      aria-hidden="true"
    />
  );
}
