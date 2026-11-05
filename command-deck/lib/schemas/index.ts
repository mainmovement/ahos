/**
 * Runtime validation of the data contracts (Zod).
 * The whole frozen dataset is parsed once per process at import time; a
 * failure means the dataset is structurally dishonest and is surfaced loudly
 * instead of rendering quietly.
 */
import { z } from "zod";

export const i18nTextSchema = z.object({
  fa: z.string().min(1),
  en: z.string().min(1),
});

export const dataStatusSchema = z.enum([
  "MEASURED",
  "SAMPLE",
  "NOT_MEASURED",
  "NOT_CONNECTED",
  "STALE",
  "QUARANTINED",
  "UNVERIFIED",
  "UNAVAILABLE",
  "EXCLUDED",
  "UNKNOWN",
]);

export const reasonCodeSchema = z.enum([
  "sampling_only",
  "no_measurement",
  "adapter_disabled",
  "backend_not_connected",
  "quarantined_by_operator",
  "insufficient_evidence",
  "not_available_in_demo",
  "stale_beyond_window",
]);

export const provenanceSchema = z.object({
  status: dataStatusSchema,
  source: z.string().min(1),
  observedAt: z.string().nullable(),
  reason: reasonCodeSchema.nullable(),
  confidence: z.number().min(0).max(1).nullable(),
  note: i18nTextSchema.optional(),
});

/** Honest invariants are additionally enforced by unit tests (tests/*.test.ts). */
export function envelopeSchema<T extends z.ZodTypeAny>(value: T) {
  return z.object({
    value: value.nullable(),
    provenance: provenanceSchema,
  });
}

export const modelScoreSchema = z.object({
  value: z.number().min(0).max(1),
  calibrated: z.literal(false),
});

export const deskIdSchema = z.enum([
  "gold",
  "oil",
  "crypto",
  "onchain",
  "exchanges",
  "tokens",
  "stocks",
]);

export const signalStateSchema = z.enum(["LONG", "SHORT", "HOLD", "UNKNOWN"]);

export const deskSchema = z.object({
  id: deskIdSchema,
  name: i18nTextSchema,
  instruments: z.array(z.string()).min(1),
  priority: z.enum(["PRIORITY", "STANDARD"]),
  signal: envelopeSchema(signalStateSchema),
  score: envelopeSchema(modelScoreSchema),
  sparkline: envelopeSchema(z.array(z.number())),
  lastObservation: envelopeSchema(z.string()),
  alertCount: envelopeSchema(z.number().int().min(0)),
});

export const pnlBreakdownSchema = z.object({
  gross: z.number(),
  fees: z.number().nullable(),
  funding: z.number().nullable(),
  net: z.number().nullable(),
});

export const positionSchema = z
  .object({
    id: z.string(),
    symbol: z.string().min(1),
    deskId: deskIdSchema,
    side: z.enum(["LONG", "SHORT"]),
    leverage: z.number().positive().nullable(),
    entry: z.number().positive(),
    mark: z.number().positive(),
    qty: z.number().positive(),
    pnl: pnlBreakdownSchema,
    state: z.enum(["OPEN", "CLOSED"]),
    openedAt: z.string().nullable(),
    closedAt: z.string().nullable(),
    provenance: provenanceSchema,
  })
  .superRefine((p, ctx) => {
    const { gross, fees, funding, net } = p.pnl;
    if (fees !== null && funding !== null) {
      const expected = gross - fees + funding;
      if (Math.abs(expected - (net ?? Number.NaN)) > 1e-6) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `NET identity violated for ${p.id}: NET must equal GROSS − FEES + FUNDING`,
        });
      }
    } else if (net !== null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `NET must be null when fees or funding are missing (${p.id})`,
      });
    }
  });

export const newsEventSchema = z.object({
  id: z.string(),
  category: z.enum([
    "geopolitics",
    "central_banks",
    "macroeconomics",
    "whale_activity",
    "onchain",
    "exchanges",
    "regulatory",
    "commodity_supply",
  ]),
  title: i18nTextSchema,
  summary: i18nTextSchema,
  at: z.string().nullable(),
  desks: z.array(deskIdSchema).min(1),
  impact: z.enum(["HIGH", "MEDIUM", "LOW"]),
  sourceLabel: z.string().min(1),
  provenance: provenanceSchema,
});

export const marketDriverSchema = z.object({
  id: z.string(),
  deskId: deskIdSchema,
  name: i18nTextSchema,
  direction: z.enum(["UP", "DOWN", "FLAT", "UNKNOWN"]),
  weight: envelopeSchema(z.number().min(-1).max(1)),
  reading: envelopeSchema(z.number().nullable()),
  unit: z.string().nullable(),
  explanation: i18nTextSchema,
});

export const serviceRecordSchema = z.object({
  id: z.string(),
  name: i18nTextSchema,
  role: i18nTextSchema,
  endpoint: z.string().nullable(),
  status: dataStatusSchema,
  pid: envelopeSchema(z.number().int().positive()),
  provenance: provenanceSchema,
});

export const healthCheckSchema = z.object({
  id: z.string(),
  serviceId: z.string(),
  name: i18nTextSchema,
  status: dataStatusSchema,
  latencyMs: envelopeSchema(z.number().positive()),
  lastRunAt: z.string().nullable(),
  detail: i18nTextSchema,
  provenance: provenanceSchema,
});

export const soakStatusSchema = z.object({
  windowId: z.string(),
  scope: z.union([deskIdSchema, z.literal("system")]),
  start: z.string(),
  end: z.string().nullable(),
  coverage: envelopeSchema(z.number().min(0).max(100)),
  segments: z.array(
    z.object({
      id: z.string(),
      start: z.string(),
      end: z.string(),
      kind: z.enum(["MEASURED", "GAP", "EXCLUDED", "QUARANTINED"]),
      note: i18nTextSchema.optional(),
    }),
  ),
  provenance: provenanceSchema,
});

export const readinessItemSchema = z.object({
  id: z.string(),
  title: i18nTextSchema,
  requirement: i18nTextSchema,
  state: z.enum(["PASS", "FAIL", "NOT_MEASURED", "NOT_VERIFIED"]),
  demonstrationState: z.enum(["PASS", "FAIL", "NOT_MEASURED", "NOT_VERIFIED"]),
  evidence: i18nTextSchema.nullable(),
  hardBlocked: z.boolean(),
});

export const alertItemSchema = z.object({
  id: z.string(),
  severity: z.enum(["INFO", "WARN", "CRITICAL"]),
  title: i18nTextSchema,
  body: i18nTextSchema,
  at: z.string().nullable(),
  provenance: provenanceSchema,
});
