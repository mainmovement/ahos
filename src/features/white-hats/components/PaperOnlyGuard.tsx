"use client";

import { isViolation } from "../predicates";
import type { WhiteHatsSnapshot } from "../types";
import { ViolationBar } from "./ViolationBar";

/**
 * Paper-only guard: the read-only audit surface stays paper-only even when a
 * (mock) source claims otherwise. If the snapshot violates the policy, the
 * red VIOLATION bar renders — and nothing else changes: still zero controls.
 *
 * The permanent «فقط کاغذی · PAPER_ONLY» pill lives in the Topbar and is not
 * dismissible; this component owns the violation surface.
 */
export function PaperOnlyGuard({ snapshot }: { snapshot: WhiteHatsSnapshot }) {
  if (!isViolation(snapshot)) return null;
  return <ViolationBar snapshot={snapshot} />;
}
