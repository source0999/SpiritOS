import Link from "next/link";
import { Activity, ArrowRight, FileText, ShieldCheck } from "lucide-react";

const statusItems = [
  { label: "Proxy", value: "Ready for safe preview", tone: "text-emerald-200" },
  { label: "Route", value: "Select during preview", tone: "text-sky-200" },
  { label: "Workspace", value: "SpiritOS", tone: "text-slate-100" },
];

const timelineItems = ["Draft", "Plan", "Diff", "Approval", "Apply", "Verification", "Done"];

export default function CodingCockpitShell() {
  return (
    <main className="min-h-dvh bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-dvh w-full max-w-6xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">
              Source Proxy cockpit
            </p>
            <h1 className="text-3xl font-semibold tracking-normal text-white">Coding</h1>
            <p className="max-w-2xl text-sm leading-6 text-slate-300">
              Draft a scoped task, preview the diff safely, then approve and apply only when
              Source Proxy gates allow it.
            </p>
          </div>
          <Link
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-white/15 bg-white/5 px-4 text-sm font-medium text-slate-100 transition hover:border-emerald-300/50 hover:bg-emerald-300/10 focus:outline-none focus:ring-2 focus:ring-emerald-300"
            href="/proxy-backend"
          >
            Advanced diagnostics
            <ArrowRight aria-hidden="true" size={16} />
          </Link>
        </header>

        <section
          aria-label="Coding status"
          className="grid gap-3 border-b border-white/10 py-4 sm:grid-cols-3"
        >
          {statusItems.map((item) => (
            <div className="rounded-md border border-white/10 bg-white/[0.03] p-4" key={item.label}>
              <div className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                {item.label}
              </div>
              <div className={`mt-2 text-sm font-semibold ${item.tone}`}>{item.value}</div>
            </div>
          ))}
        </section>

        <div className="grid flex-1 gap-5 py-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
          <section className="space-y-5" aria-labelledby="task-composer-heading">
            <div className="rounded-md border border-white/10 bg-slate-900/70 p-4 sm:p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-300/10 text-emerald-200">
                  <FileText aria-hidden="true" size={20} />
                </div>
                <div>
                  <h2 id="task-composer-heading" className="text-lg font-semibold text-white">
                    Task Composer
                  </h2>
                  <p className="text-sm text-slate-400">Preview safely before anything writes.</p>
                </div>
              </div>

              <div className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-200">Task</span>
                  <textarea
                    className="min-h-32 w-full resize-y rounded-md border border-white/10 bg-slate-950/80 px-3 py-3 text-sm text-slate-200 placeholder:text-slate-600"
                    disabled
                    placeholder="Describe the coding task here."
                  />
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-slate-200">
                      Target file
                    </span>
                    <input
                      className="min-h-11 w-full rounded-md border border-white/10 bg-slate-950/80 px-3 text-sm text-slate-200 placeholder:text-slate-600"
                      disabled
                      placeholder="docs/example.md"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-slate-200">
                      Allowed files
                    </span>
                    <input
                      className="min-h-11 w-full rounded-md border border-white/10 bg-slate-950/80 px-3 text-sm text-slate-200 placeholder:text-slate-600"
                      disabled
                      placeholder="Same as target"
                    />
                  </label>
                </div>

                <button
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-emerald-300 px-4 text-sm font-semibold text-slate-950 opacity-60 sm:w-auto"
                  disabled
                  type="button"
                >
                  <ShieldCheck aria-hidden="true" size={18} />
                  Preview safely
                </button>
              </div>
            </div>

            <div className="rounded-md border border-dashed border-white/15 bg-white/[0.02] p-5">
              <div className="flex items-start gap-3">
                <Activity className="mt-0.5 text-slate-400" aria-hidden="true" size={20} />
                <div>
                  <h2 className="text-base font-semibold text-white">No active task</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-400">
                    Approval and apply controls will appear only after a safe preview exists and
                    Source Proxy reports that the next action is legal.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <aside className="space-y-5" aria-label="Task timeline and actions">
            <section className="rounded-md border border-white/10 bg-slate-900/70 p-4">
              <h2 className="text-base font-semibold text-white">Current Task Timeline</h2>
              <ol className="mt-4 space-y-3">
                {timelineItems.map((item, index) => (
                  <li className="flex items-center gap-3" key={item}>
                    <span
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                        index === 0
                          ? "border-emerald-300 bg-emerald-300 text-slate-950"
                          : "border-white/15 text-slate-500"
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className={index === 0 ? "text-sm text-slate-100" : "text-sm text-slate-500"}>
                      {item}
                    </span>
                  </li>
                ))}
              </ol>
            </section>

            <section className="rounded-md border border-white/10 bg-slate-900/70 p-4">
              <h2 className="text-base font-semibold text-white">Next Safe Action</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Draft a task and run a preview. No files have been changed.
              </p>
            </section>
          </aside>
        </div>
      </div>
    </main>
  );
}
