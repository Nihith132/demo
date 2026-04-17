"use client";

import Link from "next/link";

export default function TopNav() {
  return (
    <header className="border-b border-white/10 bg-black/20 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-semibold tracking-tight">
          AI4 Triage
        </Link>

        <nav className="flex items-center gap-3 text-sm">
          <Link className="text-white/70 hover:text-white" href="/patient">
            Patient
          </Link>
          <Link className="text-white/70 hover:text-white" href="/doctor/login">
            Are you a doctor?
          </Link>
        </nav>
      </div>
    </header>
  );
}
