export function Sparkline({
  values,
  tone = "gold",
  label,
}: {
  values: number[];
  tone?: "gold" | "green" | "cyan" | "danger";
  label?: string;
}) {
  const min = Math.min(...values);
  const span = Math.max(...values) - min || 1;
  const points = values
    .map(
      (value, i) =>
        `${(i / Math.max(1, values.length - 1)) * 120},${35 - ((value - min) / span) * 29}`,
    )
    .join(" ");
  return (
    <svg
      className={`dc-sparkline dc-tone-${tone}`}
      viewBox="0 0 120 40"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={!label}
      preserveAspectRatio="none"
    >
      <polygon
        points={`0,40 ${points} 120,40`}
        fill="currentColor"
        opacity=".07"
      />
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
