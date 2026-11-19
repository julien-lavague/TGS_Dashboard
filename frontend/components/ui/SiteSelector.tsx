"use client";

import { Button } from "@/components/ui/button";

export type Site = "prod" | "dev";

const SITES: { label: string; value: Site; title: string }[] = [
  { label: "Prod", value: "prod", title: "www.thegoodspots.fr" },
  { label: "Dev", value: "dev", title: "dev.thegoodspots.fr" },
];

interface Props {
  value: Site;
  onChange: (s: Site) => void;
}

export function SiteSelector({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {SITES.map((s) => (
        <Button
          key={s.value}
          variant={value === s.value ? "default" : "outline"}
          size="sm"
          title={s.title}
          onClick={() => onChange(s.value)}
        >
          {s.label}
        </Button>
      ))}
    </div>
  );
}
