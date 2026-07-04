"use client";

import Link from "next/link";
import { Fingerprint } from "lucide-react";

type NavKey = "home" | "new" | "workspace" | "analytics" | "reports";

export function AppNav({ active = "workspace" }: { active?: NavKey }) {
  const linkClass = (key: NavKey) =>
    key === active
      ? "text-white font-semibold text-xs bg-[#353434] px-3 py-1 rounded"
      : "text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded";

  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-14 bg-[#141313] border-b border-[#262626]">
      <Link href="/" className="flex items-center gap-3">
        <Fingerprint className="text-white w-5 h-5" />
        <span className="text-base font-semibold text-white tracking-tight">SignalHire</span>
      </Link>
      <div className="hidden md:flex items-center gap-6">
        <Link className={linkClass("new")} href="/new">New search</Link>
        <Link className={linkClass("workspace")} href="/workspace">Shortlist</Link>
        <Link className={linkClass("analytics")} href="/analytics">Analytics</Link>
        <Link className={linkClass("reports")} href="/reports">Reports</Link>
      </div>
    </nav>
  );
}
