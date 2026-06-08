"use client";

import { Button } from "@/components/ui/button";

export const SEGMENTS = [
  "release",
  "beta",
  "testing",
  "friends",
  "work",
  "all",
] as const;

export type Segment = (typeof SEGMENTS)[number];

interface Props {
  value: Segment;
  onChange: (s: Segment) => void;
}

export function SegmentSelector({ value, onChange }: Props) {
  return (
    <div className="flex gap-2 flex-wrap">
      {SEGMENTS.map((s) => (
        <Button
          key={s}
          variant={value === s ? "default" : "outline"}
          size="sm"
          onClick={() => onChange(s)}
        >
          {s.charAt(0).toUpperCase() + s.slice(1)}
        </Button>
      ))}
    </div>
  );
}
