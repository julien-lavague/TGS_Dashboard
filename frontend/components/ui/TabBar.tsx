"use client";

interface TabBarProps<T extends string> {
  tabs: readonly { id: T; label: string }[];
  active: T;
  onChange: (id: T) => void;
}

export function TabBar<T extends string>({ tabs, active, onChange }: TabBarProps<T>) {
  // Scrolls sideways instead of wrapping when the tabs don't fit (phones).
  return (
    <div className="flex gap-1 border-b overflow-x-auto [scrollbar-width:none]">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={[
            "shrink-0 whitespace-nowrap px-3 md:px-4 py-2 text-sm font-medium transition-colors border-b-2",
            active === tab.id
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground",
          ].join(" ")}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
