/**
 * Decorative trading-hall backdrop — T2/T3 only.
 *
 * Hard rules baked in here:
 *  · `aria-hidden` and no data attributes: it can never be read as content;
 *  · it carries no numbers, no status and no state;
 *  · it is not rendered at all for T0/T1 (see `TradeVenuePage`), and its motion
 *    is switched off entirely under `prefers-reduced-motion` (venue.css).
 */
export function DecorativeHall() {
  return (
    <div className="ah-hall" aria-hidden="true" data-decorative="hall">
      <div className="ah-hall__ring" />
      <div className="ah-hall__floor" />
      <div className="ah-hall__pillar" style={{ insetInlineStart: "12%" }} />
      <div className="ah-hall__pillar" style={{ insetInlineStart: "38%" }} />
      <div className="ah-hall__pillar" style={{ insetInlineStart: "64%" }} />
      <div className="ah-hall__pillar" style={{ insetInlineStart: "88%" }} />
    </div>
  );
}
