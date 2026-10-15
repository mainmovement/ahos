'use client';

import { useEffect, useRef, useState } from 'react';
import { webApiFetch } from '@/web_api_client';
import type { Snap } from '@/dashboard_snapshot';

/**
 * The one read model the whole overview reads.
 *
 * Presentation only (AGENTS.md): this hook fetches `/api/command` — the app's own
 * snapshot of the Python canonical authority, the engine, the ledger and the
 * soak — and hands the payload to components. Nothing here is scored, derived or
 * decided client-side, and a failed fetch leaves the last good payload in place
 * with `stale` set rather than blanking the page: an old reading with its age on
 * it is more honest than an empty box.
 *
 * The poll is deliberately slower than the engine cycles (30 s against a 70 s
 * default interval).
 */

const REFRESH_MS = 30_000;

export interface SnapshotState {
  data: Snap | null;
  /** Wall-clock of the fetch that produced `data`. */
  fetchedAt: Date | null;
  /** The last fetch failed; `data` is whatever the previous one left behind. */
  stale: boolean;
  /** Still loading the first payload. */
  loading: boolean;
}

const INITIAL: SnapshotState = { data: null, fetchedAt: null, stale: false, loading: true };

export function useSnap(): SnapshotState {
  const [state, setState] = useState<SnapshotState>(INITIAL);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    const load = async () => {
      try {
        const res = await webApiFetch('/api/command');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = (await res.json()) as Snap;
        if (mounted.current) {
          setState({ data: payload, fetchedAt: new Date(), stale: false, loading: false });
        }
      } catch {
        if (mounted.current) {
          setState((prev) => ({ ...prev, stale: true, fetchedAt: new Date(), loading: false }));
        }
      }
    };
    void load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, []);

  return state;
}
