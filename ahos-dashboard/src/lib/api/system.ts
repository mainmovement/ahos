import type { AlertItem, AppNotification, DataEnvelope, ErrorsOverview, SystemOverview } from "./types";
import { fromMock, label } from "./_envelope";
import { mockAlerts, mockErrors, mockNotifications, mockSystem } from "@/mock/system";

/** System & runtime. Real source: /api/runtime + process heartbeats + Lane A integrity check. */
export async function getSystem(): Promise<DataEnvelope<SystemOverview>> {
  return fromMock(mockSystem(), "system", label("سامانه نمایشی", "Demo system"), 12, 60);
}

/** Errors & recovery. Real source: recovery orchestrator event log. */
export async function getErrors(): Promise<DataEnvelope<ErrorsOverview>> {
  return fromMock(mockErrors(), "errors", label("خطاهای نمایشی", "Demo errors"), 30, 120);
}

/** Notifications. Real source: alert service (AlertEvent in repo types.ts). */
export async function getNotifications(): Promise<DataEnvelope<AppNotification[]>> {
  return fromMock(mockNotifications(), "notifications", label("اعلان‌های نمایشی", "Demo notifications"), 20, 120);
}

/** Alert rail. Real source: AlertEvent stream with tiers INFO/WATCH/HIGH_ATTENTION. */
export async function getAlerts(): Promise<DataEnvelope<AlertItem[]>> {
  return fromMock(mockAlerts(), "alerts", label("هشدارهای نمایشی", "Demo alerts"), 20, 120);
}
