import type {
  DataEnvelope,
  DigitalWorldOverview,
  EarthOverview,
  GovernanceOverview,
  MemoryOverview,
  ReportItem,
  WorkshopOverview,
} from "./types";
import { fromMock, label } from "./_envelope";
import { mockDigitalWorld, mockEarth, mockGovernance, mockMemory, mockReports, mockWorkshop } from "@/mock/org";

/** Governance. Real source: governance ledger + approvals (ACCEPTANCE states) + audit log. */
export async function getGovernance(): Promise<DataEnvelope<GovernanceOverview>> {
  return fromMock(mockGovernance(), "governance", label("حاکمیت نمایشی", "Demo governance"), 300, 3600);
}

/** Memory & learning. Real source: memory store (PROMOTED ≠ truth) + calibration metrics. */
export async function getMemory(): Promise<DataEnvelope<MemoryOverview>> {
  return fromMock(mockMemory(), "memory", label("حافظه نمایشی", "Demo memory"), 300, 3600);
}

/** Reports. Real source: report generator jobs. */
export async function getReports(): Promise<DataEnvelope<ReportItem[]>> {
  return fromMock(mockReports(), "reports", label("گزارش‌های نمایشی", "Demo reports"), 300, 3600);
}

/** Tech workshop. Real source: CI runs, pytest JSON reports, package manifests. */
export async function getWorkshop(): Promise<DataEnvelope<WorkshopOverview>> {
  return fromMock(mockWorkshop(), "workshop", label("کارگاه نمایشی", "Demo workshop"), 120, 900);
}

/** Digital world. Real source: DefiLlama chains/stablecoins/DEX volumes. */
export async function getDigitalWorld(): Promise<DataEnvelope<DigitalWorldOverview>> {
  return fromMock(mockDigitalWorld(), "digital-world", label("جهان دیجیتال نمایشی", "Demo digital world"), 90, 900);
}

/** Earth overlays. Real source: static reference data + market feeds for index change. */
export async function getEarth(): Promise<DataEnvelope<EarthOverview>> {
  return fromMock(mockEarth(), "earth", label("لایه‌های نمایشی زمین", "Demo earth layers"), 40, 300);
}
