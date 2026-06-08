"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { SegmentSelector, type Segment } from "@/components/ui/SegmentSelector";

const SEGMENT_ORDER = ["release", "beta", "testing", "friends", "work"] as const;

const SEGMENT_LABELS: Record<string, string> = {
  release: "Release",
  beta: "Beta",
  testing: "Testing",
  friends: "Friends",
  work: "Work",
};

export default function UsersPage() {
  const [segment, setSegment] = useState<Segment>("all");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["users-list"],
    queryFn: api.users.getList,
  });

  const visibleSegments =
    segment === "all"
      ? SEGMENT_ORDER.filter((seg) => (data?.segments[seg]?.length ?? 0) > 0)
      : SEGMENT_ORDER.filter((seg) => seg === segment && (data?.segments[seg]?.length ?? 0) > 0);

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Users</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Email addresses grouped by segment
          </p>
        </div>
        <SegmentSelector value={segment} onChange={setSegment} />
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}
      {isError && (
        <p className="text-sm text-destructive">Failed to load users.</p>
      )}

      {data &&
        visibleSegments.map(
          (seg) => {
            const emails = data.segments[seg];
            return (
              <Card key={seg}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    {SEGMENT_LABELS[seg]}
                    <Badge variant="secondary">{emails.length}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="pl-6">#</TableHead>
                        <TableHead>Email</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {emails.map((email, i) => (
                        <TableRow key={email}>
                          <TableCell className="pl-6 text-muted-foreground text-xs w-10">
                            {i + 1}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {email}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            );
          }
        )}
    </div>
  );
}
