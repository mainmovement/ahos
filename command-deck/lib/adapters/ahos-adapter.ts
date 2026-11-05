/**
 * Future-compatible adapter boundary for the real AHOS backend
 * (`http://127.0.0.1:8787`).
 *
 * HARD RULES of this build:
 *  - The adapter is DISABLED. It is never called. Nothing in the UI can
 *    activate it. There is no settings toggle, no token, no .env wiring.
 *  - No real AHOS code, port, database, or credential is touched.
 *
 * When a future, separately-authorized build wants live data, it implements
 * `AhosBackendAdapter` against a running backend and registers an active
 * adapter in `adapterRegistry`. The UI reads statuses through
 * `BACKEND_CONNECTION` and stays unchanged.
 */

export class AdapterDisabledError extends Error {
  constructor() {
    super(
      "AHOS adapter is disabled in this build (PAPER-ONLY display deck). No backend calls are permitted.",
    );
    this.name = "AdapterDisabledError";
  }
}

export interface AhosSnapshotRequest {
  readonly desks?: readonly string[];
}

export interface AhosBackendAdapter {
  readonly id: string;
  readonly baseUrl: string;
  readonly enabled: boolean;
  /** Returns the real system snapshot. Throws while disabled. */
  fetchSystemSnapshot(req: AhosSnapshotRequest): Promise<unknown>;
  /** Returns desk-level intelligence. Throws while disabled. */
  fetchDesk(deskId: string): Promise<unknown>;
}

export const localAhosAdapter: AhosBackendAdapter = {
  id: "local-ahos-8787",
  baseUrl: "http://127.0.0.1:8787",
  enabled: false,
  async fetchSystemSnapshot(): Promise<never> {
    throw new AdapterDisabledError();
  },
  async fetchDesk(): Promise<never> {
    throw new AdapterDisabledError();
  },
};

/**
 * Registry. `active` MUST remain null in this build — enforced by a unit test
 * so an accidental activation fails CI instead of silently calling out.
 */
export const adapterRegistry = {
  available: [localAhosAdapter] as const,
  active: null as AhosBackendAdapter | null,
};

export const BACKEND_CONNECTION_STATUS = adapterRegistry.active
  ? ("MEASURED" as const)
  : ("NOT_CONNECTED" as const);

/** The dashboard sibling project — observed, never probed. */
export const SIBLING_DASHBOARD_URL = "http://127.0.0.1:3200";
