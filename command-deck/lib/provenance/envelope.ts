/**
 * Data provenance helpers — the ONLY way presentation code obtains values.
 * Every constructor is explicit about the honesty status of its value.
 */
import type {
  DataEnvelope,
  DataProvenance,
  DataStatus,
  I18NText,
  ModelScore,
  ReasonCode,
} from "@/lib/types";
import { DATASET } from "@/lib/data/config";

function provenance(
  status: DataStatus,
  source: string,
  reason: ReasonCode | null,
  observedAt: string | null = null,
  confidence: number | null = null,
  note?: I18NText,
): DataProvenance {
  return { status, source, reason, observedAt, confidence, ...(note ? { note } : {}) };
}

/** Deterministic, clearly-labeled demo value. */
export function sample<T>(value: T, source: string, observedAt: string | null = DATASET.asOf): DataEnvelope<T> {
  return {
    value,
    provenance: provenance("SAMPLE", source, "sampling_only", observedAt, null, {
      fa: "مقدار نمونه — فقط برای نمایش رابط کاربری",
      en: "Sample value — UI demonstration only",
    }),
  };
}

/** A plausible value that has NOT been independently verified. */
export function unverified<T>(value: T, source: string, observedAt: string | null): DataEnvelope<T> {
  return {
    value,
    provenance: provenance("UNVERIFIED", source, "insufficient_evidence", observedAt, 0.4),
  };
}

/** A measurement that exists but is outside its freshness window. */
export function stale<T>(value: T, source: string, observedAt: string): DataEnvelope<T> {
  return {
    value,
    provenance: provenance("STALE", source, "stale_beyond_window", observedAt, null),
  };
}

/** No measurement exists. Never substitute zero or a guess. */
export function notMeasured<T = never>(source: string, reason: ReasonCode = "no_measurement"): DataEnvelope<T> {
  return { value: null, provenance: provenance("NOT_MEASURED", source, reason, null, null) };
}

/** A real, known endpoint that is intentionally disconnected in this build. */
export function notConnected<T = never>(source: string): DataEnvelope<T> {
  return { value: null, provenance: provenance("NOT_CONNECTED", source, "adapter_disabled", null, null) };
}

/** Removed from evidence by operator decision. */
export function quarantined<T = never>(source: string, note?: I18NText): DataEnvelope<T> {
  return {
    value: null,
    provenance: provenance("QUARANTINED", source, "quarantined_by_operator", null, null, note),
  };
}

/** Genuinely measured by this running application itself (e.g. config facts). */
export function measured<T>(value: T, source: string, observedAt: string | null): DataEnvelope<T> {
  return {
    value,
    provenance: provenance("MEASURED", source, null, observedAt, 1),
  };
}

/** The state cannot be determined. Must never be rendered as PASS/HEALTHY. */
export function unknownState<T = never>(source: string, reason: ReasonCode = "no_measurement"): DataEnvelope<T> {
  return { value: null, provenance: provenance("UNKNOWN", source, reason, null, null) };
}

/** Raw, explicitly uncalibrated model score. */
export function sampleScore(value: number, source: string): DataEnvelope<ModelScore> {
  return sample<ModelScore>({ value, calibrated: false }, source);
}

export function isKnown<T>(envelope: DataEnvelope<T>): envelope is DataEnvelope<T> & { value: T } {
  return envelope.value !== null;
}
