"use client";

/* Read-only export helpers (allowed verb: export read-only).
   Everything here just serialises data the user is already viewing. */

function download(name: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2_000);
}

export function exportJson(name: string, data: unknown) {
  download(name, "application/json;charset=utf-8", JSON.stringify(data, null, 2));
}

function csvCell(value: unknown): string {
  const s = value === null || value === undefined ? "" : String(value);
  return /[",\n;]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

export function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0] as Record<string, unknown>);
  const lines = [headers.join(",")];
  for (const row of rows) {
    lines.push(headers.map((h) => csvCell(row[h])).join(","));
  }
  // BOM so Excel opens Persian text correctly.
  return "\uFEFF" + lines.join("\r\n");
}

export function exportCsv(name: string, rows: Record<string, unknown>[]) {
  download(name, "text/csv;charset=utf-8", toCsv(rows));
}
