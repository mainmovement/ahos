// Arena read boundary for the AHOS content pack (src/mock/content). Everything here is DEMO data;
// freshness stays on every field (Observed<T>), nothing is promoted to LIVE.
import type { Department, KillSwitchState, MockFile, MockRecord, Signal, SystemHealth } from "../../types/contract";
import departmentsFile from "../../mock/content/departments.json";
import signalsFile from "../../mock/content/signals.json";
import healthFile from "../../mock/content/system-health.json";
import killSwitchFile from "../../mock/content/kill-switch.json";
import indexFile from "../../mock/content/index.json";

export function getContentDepartments(): Department[] {
  return (departmentsFile as unknown as MockFile<Department>).items;
}
export function getContentSignals(): Signal[] {
  return (signalsFile as unknown as MockFile<Signal>).items;
}
export function getContentHealth(): SystemHealth {
  return (healthFile as unknown as MockRecord<SystemHealth>).record;
}
export function getContentGate(): KillSwitchState {
  return (killSwitchFile as unknown as MockRecord<KillSwitchState>).record;
}
export function getContentDemoNotice(): { fa: string; en: string } {
  return (indexFile as unknown as { demoNotice: { fa: string; en: string } }).demoNotice;
}