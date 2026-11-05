/**
 * Minimal, correct CSV serialization for local sample-data exports.
 * RFC-4180 quoting; UTF-8 BOM so Excel opens Persian text correctly.
 */

export function csvEscape(value: string): string {
  if (/[",\n\r]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function toCsv(rows: ReadonlyArray<ReadonlyArray<string | number | null>>): string {
  return rows.map((row) => row.map((cell) => csvEscape(cell === null ? "" : String(cell))).join(",")).join("\r\n");
}

export function csvWithBom(csv: string): string {
  return `\uFEFF${csv}`;
}
