"use client";

import "@/styles/dashboard-demo-v4.css";

import CodingCockpitShell from "@/components/coding/CodingCockpitShell";
import { activeCodingShell } from "@/lib/coding/shell-registry";

export default function CodingPage() {
  return (
    <>
      <div
        className="fixed right-3 top-3 z-50 flex gap-2"
        data-coding-shell-id={activeCodingShell.id}
      >
        <a
          className="rounded border border-white/15 bg-black/75 px-3 py-2 text-xs font-semibold text-white shadow-lg backdrop-blur transition hover:border-white/35 hover:bg-black/90"
          href="/v1/decisions/fip0-receipts/latest"
          target="_blank"
          rel="noreferrer"
        >
          Receipt
        </a>
        <a
          className="rounded border border-emerald-300/35 bg-emerald-950/80 px-3 py-2 text-xs font-semibold text-emerald-50 shadow-lg backdrop-blur transition hover:border-emerald-200/70 hover:bg-emerald-900/90"
          href="/v1/decisions/fip0-receipts/latest/trace"
          target="_blank"
          rel="noreferrer"
        >
          Trace
        </a>
      </div>
      <CodingCockpitShell />
    </>
  );
}
