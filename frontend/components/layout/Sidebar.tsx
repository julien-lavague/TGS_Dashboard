"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/overview", label: "Overview" },
  { href: "/alerts", label: "Alerts" },
  { href: "/usage", label: "User Usage" },
  { href: "/equipments", label: "Equipments" },
  { href: "/profils", label: "Profils" },
  { href: "/users", label: "Users" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r bg-card flex flex-col">
      <div className="px-6 py-5 border-b">
        <span className="font-semibold text-sm tracking-wide">TGS Metrics</span>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV.map(({ href, label }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
