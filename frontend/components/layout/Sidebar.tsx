"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { BackendStatus } from "./BackendStatus";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/overview", label: "Overview" },
  { href: "/alerts", label: "Alerts" },
  { href: "/usage", label: "User Usage" },
  { href: "/widgets", label: "Widgets" },
  { href: "/equipments", label: "Equipments" },
  { href: "/profils", label: "Profils" },
  { href: "/users", label: "Users" },
  { href: "/release-notes", label: "Release Notes" },
];

export function Sidebar() {
  const pathname = usePathname();
  // Mobile only: the sidebar becomes a drawer opened from the top bar.
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const currentLabel = NAV.find(
    ({ href }) => pathname === href || pathname.startsWith(href + "/")
  )?.label;

  return (
    <>
      <header className="md:hidden sticky top-0 z-30 flex items-center gap-3 border-b bg-card px-4 py-3">
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="-ml-1 rounded-md p-1 hover:bg-accent"
        >
          <Menu className="size-5" />
        </button>
        <span className="font-semibold text-sm tracking-wide">TGS Metrics</span>
        {currentLabel && (
          <span className="truncate text-sm text-muted-foreground">· {currentLabel}</span>
        )}
      </header>

      {open && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 border-r bg-card flex flex-col transition-transform md:static md:z-auto md:w-56 md:shrink-0 md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="px-6 py-5 border-b flex items-center justify-between">
          <span className="font-semibold text-sm tracking-wide">TGS Metrics</span>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="md:hidden -mr-2 rounded-md p-1 hover:bg-accent"
          >
            <X className="size-4" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
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
        <BackendStatus />
      </aside>
    </>
  );
}
