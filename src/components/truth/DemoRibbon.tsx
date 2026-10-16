/**
 * Diagonal DEMO tape for mock-backed surfaces (truth rule 3).
 *
 * It runs down the panel's inline-start edge, inside the padding gutter, so it
 * can never cover a value, a chip or a heading — a mock surface must *look*
 * marked, not become unreadable.
 * Purely decorative markup — every panel that shows it *also* carries a DEMO
 * `TruthChip`, so the label survives even in the T0 tier where the ribbon is
 * hidden and under `prefers-reduced-motion`.
 */
export function DemoRibbon({ variant = "DEMO" }: { variant?: "DEMO" | "SIMULATED" }) {
  return (
    <span
      className={variant === "SIMULATED" ? "tv-ribbon tv-ribbon--sim" : "tv-ribbon"}
      data-demo-ribbon={variant}
      aria-hidden="true"
    >
      <span className="tv-ribbon__text">{variant === "SIMULATED" ? "SIMULATED" : "DEMO"}</span>
    </span>
  );
}
