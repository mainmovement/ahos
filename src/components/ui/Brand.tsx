export function StarMark({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      width="42"
      height="42"
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="m24 4 5.8 12.9 14 1.5-10.4 9.5 2.8 14L24 35l-12.2 6.9 2.8-14L4.2 18.4l14-1.5L24 4Z"
        stroke="currentColor"
        strokeWidth="1.2"
      />
      <path
        d="m24 11 4.2 10 10.8 1-8.1 7 2.3 10L24 33l-9.2 6 2.3-10-8.1-7 10.8-1L24 11Z"
        fill="currentColor"
        opacity=".14"
      />
      <circle cx="24" cy="22" r="3" fill="currentColor" />
      <path
        d="M20.7 29a3.3 3.3 0 0 1 6.6 0L24 39l-3.3-10Z"
        stroke="currentColor"
      />
      <path d="M24 1v2M45 24h2M1 24h2" stroke="currentColor" opacity=".4" />
    </svg>
  );
}
