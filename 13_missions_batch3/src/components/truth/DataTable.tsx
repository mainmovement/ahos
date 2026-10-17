// FILE: 13_missions_batch3/src/components/truth/DataTable.tsx
import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
}

/** Minimal 2D table — T0-safe (no WebGL, no canvas). */
export function DataTable<T>({ columns, rows, rowKey }: DataTableProps<T>) {
  return (
    <div className="ah-table-wrap">
      <table className="ah-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((c) => (
                <td key={c.key}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
