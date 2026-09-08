export const TEAMS = [
  {
    no: 1,
    name: "Mathematical Intelligence",
    code: "MATH",
    focus: "Probability, Bayesian reasoning, anomaly detection, time series.",
  },
  {
    no: 2,
    name: "Crypto Market Intelligence",
    code: "MARKET",
    focus: "Tokenomics, liquidity, DEX microstructure, cycles.",
  },
  {
    no: 3,
    name: "Blockchain & On-Chain",
    code: "CHAIN",
    focus: "Wallets, whales, holders, transaction graphs.",
  },
  {
    no: 4,
    name: "Cybersecurity & Hacker Intel",
    code: "SEC",
    focus: "Honeypots, exploits, hidden admin, attack surface.",
  },
  {
    no: 5,
    name: "Investigative Intelligence",
    code: "OSINT",
    focus: "Entity investigation, contradictions, developer history.",
  },
  {
    no: 6,
    name: "News & Journalism",
    code: "NEWS",
    focus: "Source evaluation, narrative detection, verification.",
  },
  {
    no: 7,
    name: "Social & Narrative",
    code: "SOCIAL",
    focus: "Momentum, sentiment, authenticity vs. manufactured hype.",
  },
  {
    no: 8,
    name: "Technology & Engineering",
    code: "ENG",
    focus: "Architecture, GitHub, APIs, testing, automation.",
  },
  {
    no: 9,
    name: "AI Research & Self-Evolution",
    code: "AI",
    focus: "Reasoning methods, evaluation, model comparison.",
  },
  {
    no: 10,
    name: "Strategic Decision & Red Team",
    code: "RED",
    focus: "Contrarian analysis, bias detection, worst case.",
  },
] as const;

export type NavItem = { href: string; label: string; hint: string };

export const NAV: { label: string; items: NavItem[] }[] = [
  {
    label: "Orbit",
    items: [
      { href: "/dashboard", label: "Command", hint: "Overview" },
      { href: "/tokens", label: "Discovery", hint: "Tokens" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/intelligence", label: "Market", hint: "Structure" },
      { href: "/onchain", label: "On-Chain", hint: "Wallets" },
      { href: "/social", label: "Social", hint: "Narratives" },
      { href: "/news", label: "News", hint: "Verification" },
      { href: "/security", label: "Security", hint: "Risk gate" },
    ],
  },
  {
    label: "Council",
    items: [
      { href: "/council", label: "Chamber", hint: "10 teams" },
      { href: "/chat", label: "AI Chat", hint: "Ask AHOS" },
    ],
  },
  {
    label: "Operations",
    items: [
      { href: "/paper", label: "Paper Desk", hint: "Virtual book" },
      { href: "/alerts", label: "Alerts", hint: "Signals" },
      { href: "/telegram", label: "Telegram", hint: "Relay" },
    ],
  },
  {
    label: "Evolution",
    items: [
      { href: "/learning", label: "Learning", hint: "Post-mortem" },
      { href: "/github", label: "GitHub", hint: "Source of truth" },
      { href: "/reports", label: "Reports", hint: "Daily intel" },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/system", label: "Status", hint: "Health" },
      { href: "/settings", label: "Settings", hint: "Control" },
    ],
  },
] as const;

export const MEDIA = {
  gold: "https://images.pexels.com/photos/26628059/pexels-photo-26628059.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  waves: "https://images.pexels.com/photos/26628060/pexels-photo-26628060.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  metal: "https://images.pexels.com/photos/6141905/pexels-photo-6141905.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  palace: "https://images.pexels.com/photos/752329/pexels-photo-752329.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  facade: "https://images.pexels.com/photos/19577796/pexels-photo-19577796.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  roots: "https://images.pexels.com/photos/12763908/pexels-photo-12763908.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  tangle: "https://images.pexels.com/photos/8552609/pexels-photo-8552609.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  forest: "https://images.pexels.com/photos/35726769/pexels-photo-35726769.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  alley: "https://images.pexels.com/photos/19943722/pexels-photo-19943722.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
  hotel: "https://images.pexels.com/photos/36913959/pexels-photo-36913959.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=900&w=1600",
};

export const PROVIDERS = [
  { layer: "MarketData", primary: "DEX Screener", fallback: ["GeckoTerminal", "CoinGecko"] },
  { layer: "Blockchain", primary: "Public RPC", fallback: ["Explorer APIs", "Local indexer"] },
  { layer: "News", primary: "Open RSS", fallback: ["Project blogs", "Manual ingest"] },
  { layer: "Social", primary: "Public timelines", fallback: ["Telegram export", "Reddit"] },
  { layer: "AI", primary: "Local council engine", fallback: ["Optional cloud models"] },
  { layer: "Security", primary: "Static heuristics", fallback: ["GoPlus-style public", "Manual review"] },
];
