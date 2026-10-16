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
      className={size === "sm" ? "ah-chip ah-chip--sm ah-chip--perm" : "ah-chip ah-chip--perm"}
      data-chip=""
      data-permission={allowed ? "ALLOWED" : "NOT_ALLOWED"}
      data-tone={allowed ? "neutral" : "danger"}
      data-live="false"
      title={
        title ??
        (allowed
          ? "مجوز کاغذی دارد: موتور کاغذی اجازهٔ آینه‌کردن این نماد را دارد."
          : "مجوز کاغذی ندارد: ردیف «غیرمجاز» است و در هیچ جمعی نمی‌آید.")
      }
    >
      <i className="ah-chip__dot" aria-hidden="true" />
      <span className="ah-chip__fa">{allowed ? PERMITTED_FA : NOT_AUTHORIZED_FA}</span>
    </span>
  );
}
