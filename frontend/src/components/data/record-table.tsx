"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef
} from "@tanstack/react-table";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { formatApiDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { RecordLike } from "@/types/api";

function titleize(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function getRecordValue(record: RecordLike, key: string) {
  return record[key];
}

function renderCellValue(value: unknown, key: string) {
  if (value === null || value === undefined || value === "") {
    return <span className="text-muted-foreground">—</span>;
  }

  if (typeof value === "boolean") {
    return (
      <Badge variant={value ? "success" : "secondary"}>
        {value ? "Yes" : "No"}
      </Badge>
    );
  }

  if (typeof value === "string" && /\d{4}-\d{2}-\d{2}/.test(value)) {
    return formatApiDate(value);
  }

  if (Array.isArray(value)) {
    return value.length ? `${value.length} items` : "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  if (key.includes("status") || key.includes("state")) {
    return <Badge variant="outline">{String(value)}</Badge>;
  }

  return String(value);
}

export function RecordTable({
  data,
  preferredColumns = []
}: {
  data: RecordLike[];
  preferredColumns?: string[];
}) {
  const columns = useMemo<ColumnDef<RecordLike>[]>(() => {
    const discoveredKeys = Array.from(
      new Set(data.flatMap((record) => Object.keys(record)))
    );
    const orderedKeys = [
      ...preferredColumns.filter((key) => discoveredKeys.includes(key)),
      ...discoveredKeys.filter((key) => !preferredColumns.includes(key))
    ].slice(0, 8);

    return orderedKeys.map((key) => ({
      id: key,
      accessorFn: (row) => getRecordValue(row, key),
      header: titleize(key),
      cell: ({ getValue }) => renderCellValue(getValue(), key)
    }));
  }, [data, preferredColumns]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel()
  });

  if (data.length === 0) {
    return (
      <Card className="flex min-h-48 items-center justify-center p-8 text-center">
        <div>
          <p className="text-lg font-bold">No records returned yet</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Once the API has data for this section, it will appear here.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-secondary/70 text-xs uppercase tracking-[0.14em] text-muted-foreground">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-5 py-4 font-extrabold">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className={cn(
                  "border-t transition-colors hover:bg-accent/45",
                  row.index % 2 === 0 && "bg-card/35"
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-5 py-4 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
