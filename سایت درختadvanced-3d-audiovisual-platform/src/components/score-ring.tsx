export function ScoreRing({
  value,
  label,
  size = 88,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const r = 28;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.max(0, Math.min(100, value)) / 100) * c;
  const tone = value >= 80 ? "#4ade80" : value >= 55 ? "#f3d5a0" : "#fb7185";
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox="0 0 72 72" className="overflow-visible">
        <circle cx="36" cy="36" r={r} fill="none" stroke="rgba(255,244,214,0.08)" strokeWidth="4" />
        <circle
          cx="36"
          cy="36"
          r={r}
          fill="none"
          stroke={tone}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 36 36)"
        />
        <text x="36" y="40" textAnchor="middle" fill="#fff6e4" fontSize="13" fontFamily="IBM Plex Mono, monospace">
          {value}
        </text>
      </svg>
      <span className="kicker">{label}</span>
    </div>
  );
}

export function ScoreBar({ value, label }: { value: number; label: string }) {
  const tone = value >= 80 ? "good" : value >= 55 ? "mid" : "bad";
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs text-[#efe6d6]/70">
        <span>{label}</span>
        <span className="font-mono">{value}</span>
      </div>
      <div className={`score-bar ${tone}`}>
        <span style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
