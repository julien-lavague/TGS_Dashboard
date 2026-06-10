"use client";

import { Button } from "@/components/ui/button";

export type TimeRange = "1d" | "7d" | "30d" | "all";

const TIME_RANGES: { label: string; value: TimeRange }[] = [
  { label: "Last Day", value: "1d" },
  { label: "Last Week", value: "7d" },
  { label: "Last Month", value: "30d" },
  { label: "All", value: "all" },
];

export const DAYS_FOR_RANGE: Record<TimeRange, number | undefined> = {
  "1d": 1,
  "7d": 7,
  "30d": 30,
  "all": undefined,
};

interface Props {
  value: TimeRange;
  onChange: (r: TimeRange) => void;
}

export function TimeRangeSelector({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {TIME_RANGES.map((r) => (
        <Button
          key={r.value}
          variant={value === r.value ? "default" : "outline"}
          size="sm"
          onClick={() => onChange(r.value)}
        >
          {r.label}
        </Button>
      ))}
    </div>
  );
}
