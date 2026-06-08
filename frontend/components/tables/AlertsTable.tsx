"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { AlertRow } from "@/lib/types";

interface AlertsTableProps {
  rows: AlertRow[];
}

export function AlertsTable({ rows }: AlertsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Email</TableHead>
            <TableHead>Alert name</TableHead>
            <TableHead>Question</TableHead>
            <TableHead>Day</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, i) => (
            <TableRow key={i}>
              <TableCell className="font-mono text-xs">{row.email}</TableCell>
              <TableCell>{row.name}</TableCell>
              <TableCell className="max-w-xs text-sm text-muted-foreground">
                {row.question}
              </TableCell>
              <TableCell className="capitalize">{row.day ?? "—"}</TableCell>
              <TableCell>{row.time ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={row.is_active ? "default" : "secondary"}>
                  {row.is_active ? "Active" : "Inactive"}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
