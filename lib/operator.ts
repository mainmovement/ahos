/**
 * AHOS operator identity (local, single-operator desktop app).
 *
 * The template this shell was ported from used Clerk for user/org identity.
 * AHOS has no user directory: it is a paper-only desktop command center owned
 * and operated by one person. The launcher bootstrap token authenticates the
 * *session*, not a user, so the shell's identity surface is a constant here.
 *
 * MASTER_SPEC asks for the owner avatar "Mehrdad" in the top bar.
 */
export interface AhosOperator {
  fullName: string;
  /** Shown under the name in the user menu and sidebar footer. */
  role: string;
  /** Initials for the avatar (no remote image: offline-first, no tracking). */
  initials: string;
  /** Locale the shell greets in (MASTER_SPEC: Persian + English). */
  locale: "fa" | "en";
}

export const AHOS_OPERATOR: AhosOperator = {
  fullName: "Mehrdad",
  role: "Owner · Operator",
  initials: "M",
  locale: "fa",
};

/** MASTER_SPEC hero greeting, in the operator's locale. */
export function greeting(operator: AhosOperator = AHOS_OPERATOR): string {
  const hour = new Date().getHours();
  if (operator.locale === "fa") {
    if (hour < 12) return `صبح بخیر، ${operator.fullName}`;
    if (hour < 18) return `بعد از ظهر بخیر، ${operator.fullName}`;
    return `شب بخیر، ${operator.fullName}`;
  }
  if (hour < 12) return `Good morning, ${operator.fullName}`;
  if (hour < 18) return `Good afternoon, ${operator.fullName}`;
  return `Good evening, ${operator.fullName}`;
}
