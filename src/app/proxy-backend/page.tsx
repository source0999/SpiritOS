import Link from "next/link";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

const statusItems = [
  {
    label: "Backend API",
    status: "Planned, not wired",
    note: "Live health needs a later read-only decision.",
  },
  {
    label: "Source Proxy",
    status: "Planned, not wired",
    note: "Proxy reachability is not connected yet.",
  },
  {
    label: "Ollama/local model",
    status: "Planned, not wired",
    note: "Model availability is not connected yet.",
  },
  {
    label: "Scout",
    status: "Planned, not wired",
    note: "Scout status is not connected yet.",
  },
];

const plannedChecks = [
  "Backend health check",
  "Proxy reachability check",
  "Local model availability check",
  "Scout/intelligence status check",
];

const blockedItems = [
  "Live backend health: planned, not wired",
  "Backend runtime changes: out of scope",
  "Read-only data: requires later decision",
  "Autonomy controls: not enabled",
];

const rawDiagnosticItems = [
  {
    label: "Raw diagnostics",
    note: "Copied /coding diagnostic packets, failed preview payloads, and manual proof notes belong here.",
  },
  {
    label: "Backend state",
    note: "Health, reachability, model availability, worker state, and queue details stay off the main /coding cockpit.",
  },
  {
    label: "Route details",
    note: "Preview, verification, and apply route names can be inspected here when a failure needs handoff context.",
  },
  {
    label: "Evidence archive",
    note: "Trial reports, copied receipts, and artifact links remain available as debug material, not as default cockpit panels.",
  },
  {
    label: "Environment setup",
    note: "Paths, variables, local model setup, and runtime probes should be recorded here or in logs/artifacts.",
  },
];

export default function ProxyBackendPage() {
  return (
    <div className="dashboard-demo-v4-route-shell">
      <main className="dashboard-demo-v4-route-main min-h-dvh bg-slate-950 text-slate-100">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 pb-[var(--shell-mobile-bottom-reserved-height)] pt-6 sm:px-6 lg:px-8 lg:pb-8">
          <section className="flex flex-col gap-5 border-b border-slate-800 pb-6">
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium text-cyan-300">/proxy-backend</p>
              <h1 className="text-3xl font-semibold tracking-normal text-white sm:text-4xl">
                Backend Console
              </h1>
              <p className="max-w-2xl text-base leading-7 text-slate-300">
                Check backend health, proxy status, and safe next actions.
              </p>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-900/70 p-4">
              <div className="text-sm font-medium text-slate-300">
                Backend status
              </div>
              <div className="mt-2 text-sm font-semibold text-amber-200">
                Planned, not wired
              </div>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
                Live checks for Backend API, Source Proxy, Ollama/local model, and
                Scout need a later read-only wiring decision.
              </p>
              <p className="mt-2 max-w-3xl text-sm font-medium leading-6 text-slate-200">
                No explicit go means no wiring.
              </p>
            </div>

            <p className="text-sm text-slate-300">
              Next step: use this page as a static backend overview until
              read-only wiring is approved later.
            </p>
          </section>

          <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
            <div className="flex flex-col gap-6">
              <section className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-white">
                  System Status
                </h2>
                <div className="overflow-hidden rounded-md border border-slate-800">
                  {statusItems.map((item) => (
                    <div
                      className="grid gap-2 border-b border-slate-800 bg-slate-900/50 p-4 last:border-b-0 sm:grid-cols-[170px_150px_1fr]"
                      key={item.label}
                    >
                      <div className="font-medium text-white">{item.label}</div>
                      <div className="text-sm font-semibold text-amber-200">
                        {item.status}
                      </div>
                      <div className="text-sm leading-6 text-slate-300">
                        {item.note}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-white">
                  Raw Diagnostics Home
                </h2>
                <div className="overflow-hidden rounded-md border border-slate-800 bg-slate-900/50">
                  {rawDiagnosticItems.map((item) => (
                    <div
                      className="grid gap-2 border-b border-slate-800 p-4 last:border-b-0 sm:grid-cols-[180px_1fr]"
                      key={item.label}
                    >
                      <div className="font-medium text-white">{item.label}</div>
                      <div className="text-sm leading-6 text-slate-300">{item.note}</div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-white">Safe Checks</h2>
                <div className="rounded-md border border-slate-800 bg-slate-900/50">
                  {plannedChecks.map((check) => (
                    <div
                      className="flex flex-col gap-1 border-b border-slate-800 p-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
                      key={check}
                    >
                      <span className="font-medium text-white">{check}</span>
                      <span className="text-sm font-semibold text-amber-200">
                        Planned, not wired
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <aside className="flex flex-col gap-6">
              <section className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-white">
                  Current Workflows
                </h2>
                <div className="flex flex-col gap-3">
                  <Link
                    className="rounded-md border border-slate-800 bg-slate-900/70 p-4 transition-colors hover:border-cyan-500 hover:bg-slate-900"
                    href="/coding"
                  >
                    <span className="block font-medium text-white">
                      Open coding
                    </span>
                    <span className="mt-1 block text-sm leading-6 text-slate-300">
                      Coding command center for coding agent workflow.
                    </span>
                  </Link>
                  <Link
                    className="rounded-md border border-slate-800 bg-slate-900/70 p-4 transition-colors hover:border-cyan-500 hover:bg-slate-900"
                    href="/map"
                  >
                    <span className="block font-medium text-white">Open map</span>
                    <span className="mt-1 block text-sm leading-6 text-slate-300">
                      Cartographer manual control center.
                    </span>
                  </Link>
                  <Link
                    className="rounded-md border border-slate-800 bg-slate-900/70 p-4 transition-colors hover:border-cyan-500 hover:bg-slate-900"
                    href="/"
                  >
                    <span className="block font-medium text-white">
                      Open dashboard
                    </span>
                    <span className="mt-1 block text-sm leading-6 text-slate-300">
                      Overview-only dashboard.
                    </span>
                  </Link>
                </div>
              </section>

              <section className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-white">
                  Blocked Or Not Wired
                </h2>
                <ul className="rounded-md border border-slate-800 bg-slate-900/50">
                  {blockedItems.map((item) => (
                    <li
                      className="border-b border-slate-800 p-4 text-sm leading-6 text-slate-300 last:border-b-0"
                      key={item}
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </section>

          <section className="border-t border-slate-800 pt-5 text-sm leading-6 text-slate-400">
            <h2 className="mb-2 text-base font-semibold text-slate-200">
              Debug Notes
            </h2>
            <p>
              This page is static. Live backend values need a later read-only
              wiring decision. No explicit go means no wiring.
            </p>
          </section>
        </div>
      </main>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
