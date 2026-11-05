import { describe, expect, it } from "vitest";
import {
  AdapterDisabledError,
  BACKEND_CONNECTION_STATUS,
  adapterRegistry,
  localAhosAdapter,
} from "@/lib/adapters/ahos-adapter";
import { deskSchema, positionSchema, provenanceSchema } from "@/lib/schemas";
import { notMeasured, sample } from "@/lib/provenance/envelope";

describe("backend adapter boundary", () => {
  it("is disabled and inactive", () => {
    expect(localAhosAdapter.enabled).toBe(false);
    expect(adapterRegistry.active).toBeNull();
    expect(BACKEND_CONNECTION_STATUS).toBe("NOT_CONNECTED");
  });

  it("throws if anyone ever calls it", async () => {
    await expect(localAhosAdapter.fetchSystemSnapshot({})).rejects.toBeInstanceOf(AdapterDisabledError);
    await expect(localAhosAdapter.fetchDesk("gold")).rejects.toBeInstanceOf(AdapterDisabledError);
  });
});

describe("provenance schemas", () => {
  it("accepts a well-formed sample envelope", () => {
    const env = sample(42, "sample://ahos-demo/test");
    const parsed = provenanceSchema.safeParse(env.provenance);
    expect(parsed.success).toBe(true);
  });

  it("accepts NOT_MEASURED envelopes with null value", () => {
    const env = notMeasured("sample://ahos-demo/none");
    expect(env.value).toBeNull();
    expect(env.provenance.status).toBe("NOT_MEASURED");
  });
});

describe("position accounting identity", () => {
  const base = {
    id: "p1",
    symbol: "XAUUSD",
    deskId: "gold",
    side: "LONG",
    leverage: 2,
    entry: 4000,
    mark: 4050,
    qty: 1,
    state: "OPEN",
    openedAt: "2026-10-01T10:00:00Z",
    closedAt: null,
  };

  it("accepts NET = GROSS − FEES + FUNDING", () => {
    const parsed = positionSchema.safeParse({
      ...base,
      pnl: { gross: 50, fees: 4, funding: 1.5, net: 47.5 },
      provenance: sample(null, "sample://t").provenance,
    });
    expect(parsed.success).toBe(true);
  });

  it("rejects a broken NET identity", () => {
    const parsed = positionSchema.safeParse({
      ...base,
      pnl: { gross: 50, fees: 4, funding: 1.5, net: 55 },
      provenance: sample(null, "sample://t").provenance,
    });
    expect(parsed.success).toBe(false);
  });

  it("rejects a computed NET when fees/funding are missing", () => {
    const parsed = positionSchema.safeParse({
      ...base,
      pnl: { gross: 50, fees: null, funding: null, net: 50 },
      provenance: sample(null, "sample://t").provenance,
    });
    expect(parsed.success).toBe(false);
  });

  it("accepts null NET when inputs are missing", () => {
    const parsed = positionSchema.safeParse({
      ...base,
      pnl: { gross: 50, fees: null, funding: null, net: null },
      provenance: sample(null, "sample://t").provenance,
    });
    expect(parsed.success).toBe(true);
  });

  it("desk schema validates a real desk entry", () => {
    const desk = {
      id: "gold",
      name: { fa: "طلا", en: "Gold" },
      instruments: ["XAUUSD"],
      priority: "PRIORITY",
      signal: { value: "HOLD", provenance: sample(null, "s").provenance },
      score: {
        value: { value: 0.61, calibrated: false },
        provenance: sample(null, "s").provenance,
      },
      sparkline: { value: [1, 2, 3], provenance: sample(null, "s").provenance },
      lastObservation: { value: "2026-10-31T12:00:00Z", provenance: sample(null, "s").provenance },
      alertCount: { value: 2, provenance: sample(null, "s").provenance },
    };
    expect(deskSchema.safeParse(desk).success).toBe(true);
  });
});
