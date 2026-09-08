export function usd(n: number, digits = 2) {
  if (!Number.isFinite(n)) return "—";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(digits)}`;
}

export function compact(n: number) {
  if (!Number.isFinite(n)) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

export function pct(n: number) {
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

export function timeAgo(input: Date | string | null | undefined) {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const days = Math.floor(h / 24);
  return `${days}d`;
}

export function scoreTone(n: number) {
  if (n >= 80) return "good";
  if (n >= 55) return "mid";
  return "bad";
}

export function decisionLabel(d: string) {
  const map: Record<string, string> = {
    investigate: "INVESTIGATE",
    paper: "PAPER",
    reject: "REJECT",
    skip: "SKIP",
    watch: "WATCH",
  };
  return map[d] ?? d.toUpperCase();
}

export function groupLabel(g: string) {
  const map: Record<string, string> = {
    pre_launch: "Group A · Pre-Launch",
    newly_launched: "Group B · Newly Launched",
    hidden: "Group C · Hidden",
  };
  return map[g] ?? g;
}

export function truncateAddr(addr: string) {
  if (addr.length < 12) return addr;
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}
