import { tr } from "@/src/lib/i18n";
import { NOT_AUTHORIZED_FA, PERMITTED_FA } from "@/src/features/trade-venue/logic/truth";

/**
 * Permission chip — deliberately **not** a `TruthChip`.
 *
 * `paperAllowed` is a permission flag, not a truth status: an allowed row is
 * neither "live" nor fresh, and a not-allowed row is not a rejected trade. Giving
 * permission the LIVE tone would put a green chip on a screen that has no live
 * data at all (it did, once — the UNKNOWN-state test caught it), so permission
 * gets its own neutral/danger vocabulary and its own `data-permission` hook.
 */
export interface PermissionChipProps {
  allowed: boolean;
  size?: "sm" | "md";
  title?: string;
}

export function PermissionChip({ allowed, size = "sm", title }: PermissionChipProps) {
  return (
    <span
      className={size === "sm" ? "tv-chip tv-chip--sm tv-chip--perm" : "tv-chip tv-chip--perm"}
      data-chip=""
      data-permission={allowed ? "ALLOWED" : "NOT_ALLOWED"}
      data-tone={allowed ? "neutral" : "danger"}
      data-live="false"
      title={
        title ??
        (allowed
          ? tr("fa", "tradeVenue.ui.PermissionChip_1")
          : tr("fa", "tradeVenue.ui.PermissionChip_2"))
      }
    >
      <i className="tv-chip__dot" aria-hidden="true" />
      <span className="tv-chip__fa">{allowed ? PERMITTED_FA : NOT_AUTHORIZED_FA}</span>
    </span>
  );
}
