"use client";

import { useEffect, useMemo, useState } from "react";
import type { ComponentType } from "react";
import {
  ClipboardCopy,
  FileAudio,
  FolderInput,
  Pause,
  Play,
  ShieldCheck,
  Square,
  Trash2,
} from "lucide-react";

import { CONVERTER_ROOTS, type ConverterJob, type ConverterQueueSnapshot } from "@/lib/converter/converterTypes";
import { cn } from "@/lib/cn";

const emptySnapshot: ConverterQueueSnapshot = {
  state: "idle",
  jobs: [],
};

type FormState = {
  pastedItems: string;
  folderPath: string;
  manualTranscript: string;
  affirmed: boolean;
  note: string;
  proofPath: string;
  title: string;
  creator: string;
  project: string;
  tags: string;
  licenseNote: string;
};

const initialForm: FormState = {
  pastedItems: "",
  folderPath: "",
  manualTranscript: "",
  affirmed: false,
  note: "",
  proofPath: "",
  title: "",
  creator: "",
  project: "",
  tags: "",
  licenseNote: "",
};

export function AuthorizedMediaImporter() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [snapshot, setSnapshot] = useState<ConverterQueueSnapshot>(emptySnapshot);
  const [selectedJobId, setSelectedJobId] = useState<string>();
  const [message, setMessage] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const activeJob = useMemo(() => {
    const selected = snapshot.jobs.find((job) => job.id === selectedJobId);
    return selected ?? snapshot.jobs.find((job) => job.id === snapshot.activeJobId) ?? snapshot.jobs[0];
  }, [selectedJobId, snapshot]);

  const completedJobs = snapshot.jobs.filter((job) => job.state === "completed");

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const response = await fetch("/api/converter/jobs", { cache: "no-store" });
        if (!response.ok) {
          return;
        }
        const next = (await response.json()) as ConverterQueueSnapshot;
        if (!cancelled) {
          setSnapshot(next);
        }
      } catch {
        if (!cancelled) {
          setMessage("Converter queue status is temporarily unavailable.");
        }
      }
    }

    void poll();
    const interval = window.setInterval(poll, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  async function startQueue() {
    setSubmitting(true);
    setMessage("");
    try {
      const response = await fetch("/api/converter/jobs", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          pastedItems: form.pastedItems,
          folderPath: form.folderPath,
          manualTranscript: form.manualTranscript,
          authorization: {
            affirmed: form.affirmed,
            note: form.note,
            proofPath: form.proofPath,
          },
          metadata: {
            title: form.title,
            creator: form.creator,
            project: form.project,
            tags: form.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
            licenseNote: form.licenseNote,
          },
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        setMessage(body.error ?? "Could not start converter queue.");
        return;
      }
      setSnapshot(body.snapshot);
      setSelectedJobId(body.snapshot.jobs[0]?.id);
      setMessage(`Queued ${body.accepted} item${body.accepted === 1 ? "" : "s"}.`);
    } finally {
      setSubmitting(false);
    }
  }

  async function controlQueue(action: "pause" | "resume" | "cancel" | "clear") {
    const response = await fetch("/api/converter/control", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action }),
    });
    if (response.ok) {
      setSnapshot((await response.json()) as ConverterQueueSnapshot);
    }
  }

  async function copyDiagnostics(job: ConverterJob | undefined) {
    if (!job) {
      return;
    }

    const response = await fetch(`/api/converter/diagnostics/${job.id}`, { cache: "no-store" });
    const text = await response.text();
    await navigator.clipboard.writeText(text);
    setMessage("Diagnostics copied with secrets redacted.");
  }

  return (
    <main className="min-h-dvh bg-slate-950 text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 pb-[var(--shell-mobile-bottom-reserved-height)] pt-6 sm:px-6 lg:px-8 lg:pb-8">
        <section className="border-b border-slate-800 pb-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-cyan-300">
                /converter
              </p>
              <h1 className="mt-2 text-3xl font-semibold tracking-normal text-white sm:text-4xl">
                Authorized Media Importer
              </h1>
              <p className="mt-3 text-base leading-7 text-slate-300">
                Import Britton-owned or written-permission media into Dell-stored
                audio, transcript, and knowledge assets. This is authorization gated
                and is not a public YouTube downloader.
              </p>
            </div>
            <div className="rounded-md border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-sm leading-6 text-amber-100">
              YouTube URLs are rejected unless ownership or written permission is affirmed.
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="flex flex-col gap-5">
            <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <FolderInput className="h-4 w-4 text-cyan-300" aria-hidden />
                Inputs
              </div>
              <div className="mt-4 grid gap-4">
                <label className="grid gap-2">
                  <span className="text-sm font-medium text-slate-200">Pasted links or local file paths</span>
                  <textarea
                    className="min-h-36 rounded-md border border-slate-700 bg-slate-950 p-3 font-mono text-sm text-slate-100 outline-none transition focus:border-cyan-400"
                    placeholder={"https://www.youtube.com/watch?v=...\n/mnt/spirit-8tb/source/file.mp4"}
                    value={form.pastedItems}
                    onChange={(event) => setForm({ ...form, pastedItems: event.target.value })}
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-medium text-slate-200">Folder path for local media files</span>
                  <input
                    className="rounded-md border border-slate-700 bg-slate-950 p-3 font-mono text-sm text-slate-100 outline-none transition focus:border-cyan-400"
                    value={form.folderPath}
                    onChange={(event) => setForm({ ...form, folderPath: event.target.value })}
                    placeholder="/mnt/spirit-8tb/incoming-media"
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-sm font-medium text-slate-200">Manual transcript paste</span>
                  <textarea
                    className="min-h-28 rounded-md border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 outline-none transition focus:border-cyan-400"
                    value={form.manualTranscript}
                    onChange={(event) => setForm({ ...form, manualTranscript: event.target.value })}
                    placeholder="Paste transcript text to store it immediately as a knowledge record."
                  />
                </label>
              </div>
            </section>

            <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <ShieldCheck className="h-4 w-4 text-emerald-300" aria-hidden />
                Authorization
              </div>
              <label className="mt-4 flex gap-3 rounded-md border border-slate-700 bg-slate-950 p-3">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4"
                  checked={form.affirmed}
                  onChange={(event) => setForm({ ...form, affirmed: event.target.checked })}
                />
                <span className="text-sm leading-6 text-slate-200">
                  I own this content or have written permission/license to download/process it.
                </span>
              </label>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <TextInput label="License/approval note" value={form.note} onChange={(note) => setForm({ ...form, note })} />
                <TextInput label="License proof path" value={form.proofPath} onChange={(proofPath) => setForm({ ...form, proofPath })} />
              </div>
            </section>

            <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-sm font-semibold text-white">Optional metadata</div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <TextInput label="Title" value={form.title} onChange={(title) => setForm({ ...form, title })} />
                <TextInput label="Creator/channel" value={form.creator} onChange={(creator) => setForm({ ...form, creator })} />
                <TextInput label="Project" value={form.project} onChange={(project) => setForm({ ...form, project })} />
                <TextInput label="Tags" value={form.tags} onChange={(tags) => setForm({ ...form, tags })} placeholder="comma, separated" />
                <div className="sm:col-span-2">
                  <TextInput label="License note" value={form.licenseNote} onChange={(licenseNote) => setForm({ ...form, licenseNote })} />
                </div>
              </div>
            </section>
          </div>

          <aside className="flex flex-col gap-5">
            <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-sm font-semibold text-white">Output roots</div>
              <dl className="mt-3 grid gap-2 text-xs">
                {Object.entries(CONVERTER_ROOTS).map(([key, value]) => (
                  <div className="grid gap-1" key={key}>
                    <dt className="font-semibold uppercase tracking-wide text-slate-500">{key}</dt>
                    <dd className="break-all font-mono text-slate-300">{value}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="inline-flex min-h-11 items-center gap-2 rounded-md bg-cyan-400 px-4 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={startQueue}
                  disabled={submitting}
                >
                  <Play className="h-4 w-4" aria-hidden />
                  Start Queue
                </button>
                <IconButton label="Pause" onClick={() => controlQueue("pause")} icon={Pause} />
                <IconButton label="Resume" onClick={() => controlQueue("resume")} icon={Play} />
                <IconButton label="Cancel" onClick={() => controlQueue("cancel")} icon={Square} />
                <IconButton label="Clear" onClick={() => controlQueue("clear")} icon={Trash2} />
              </div>
              <p className="mt-3 text-sm text-slate-300">
                Queue: <span className="font-semibold text-white">{snapshot.state}</span>
              </p>
              {message ? <p className="mt-2 text-sm text-cyan-200">{message}</p> : null}
            </section>
          </aside>
        </section>

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_420px]">
          <section className="rounded-md border border-slate-800 bg-slate-900/60">
            <div className="border-b border-slate-800 p-4 text-sm font-semibold text-white">
              Batch progress
            </div>
            <div className="divide-y divide-slate-800">
              {snapshot.jobs.length ? (
                snapshot.jobs.map((job) => (
                  <button
                    type="button"
                    className={cn(
                      "grid w-full gap-2 p-4 text-left transition hover:bg-slate-800/60 sm:grid-cols-[150px_1fr_150px]",
                      activeJob?.id === job.id && "bg-slate-800/80",
                    )}
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                  >
                    <span className="font-mono text-xs uppercase tracking-wide text-cyan-300">{job.kind}</span>
                    <span className="min-w-0 truncate text-sm font-medium text-white">{job.source}</span>
                    <span className={cn("text-sm font-semibold", stateClass(job.state))}>{job.state}</span>
                  </button>
                ))
              ) : (
                <p className="p-4 text-sm text-slate-400">No converter jobs queued yet.</p>
              )}
            </div>
          </section>

          <section className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-white">Active job detail</div>
              <button
                type="button"
                className="inline-flex min-h-10 items-center gap-2 rounded-md border border-slate-700 px-3 text-sm font-semibold text-slate-100 transition hover:border-cyan-400"
                onClick={() => copyDiagnostics(activeJob)}
                disabled={!activeJob}
              >
                <ClipboardCopy className="h-4 w-4" aria-hidden />
                Copy diagnostics
              </button>
            </div>
            {activeJob ? (
              <div className="mt-4 grid gap-4 text-sm">
                <Detail label="Status" value={activeJob.state} />
                <Detail label="Authorization" value={activeJob.authorization?.affirmed ? "Owned/licensed authorization recorded" : "Not recorded"} />
                <Detail label="License note" value={activeJob.authorization?.note || activeJob.metadata.licenseNote || "None"} />
                <Detail label="Proof path" value={activeJob.authorization?.proofPath || "None"} />
                <Detail label="Audio" value={activeJob.output.audioPath || "Pending"} />
                <Detail label="Transcript" value={activeJob.output.transcriptPath || "Pending"} />
                <Detail label="Knowledge" value={activeJob.output.knowledgeRecordPath || "Pending"} />
                {activeJob.error ? <Detail label="Error" value={activeJob.error} tone="error" /> : null}
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Logs</div>
                  <div className="mt-2 max-h-52 overflow-auto rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs leading-5 text-slate-300">
                    {activeJob.logs.map((entry, index) => (
                      <div key={`${entry.at}-${index}`}>{entry.state}: {entry.message}</div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-400">Select a job to inspect authorization and outputs.</p>
            )}
          </section>
        </section>

        <section className="rounded-md border border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2 border-b border-slate-800 p-4 text-sm font-semibold text-white">
            <FileAudio className="h-4 w-4 text-cyan-300" aria-hidden />
            Completed outputs
          </div>
          <div className="divide-y divide-slate-800">
            {completedJobs.length ? (
              completedJobs.map((job) => (
                <div className="grid gap-2 p-4 text-sm sm:grid-cols-[180px_1fr]" key={job.id}>
                  <div className="font-semibold text-white">{job.metadata.title || job.sourceMetadata?.title || job.kind}</div>
                  <div className="grid gap-1 font-mono text-xs text-slate-300">
                    {Object.entries(job.output)
                      .filter(([, value]) => typeof value === "string")
                      .map(([key, value]) => <span className="break-all" key={key}>{key}: {String(value)}</span>)}
                  </div>
                </div>
              ))
            ) : (
              <p className="p-4 text-sm text-slate-400">Completed converter artifacts will appear here.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function TextInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <input
        className="rounded-md border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 outline-none transition focus:border-cyan-400"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string;
  icon: ComponentType<{ className?: string }>;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="inline-flex min-h-11 items-center gap-2 rounded-md border border-slate-700 px-3 text-sm font-semibold text-slate-100 transition hover:border-cyan-400"
      onClick={onClick}
      title={label}
    >
      <Icon className="h-4 w-4" aria-hidden />
      <span>{label}</span>
    </button>
  );
}

function Detail({ label, value, tone }: { label: string; value: string; tone?: "error" }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={cn("mt-1 break-all text-slate-200", tone === "error" && "text-rose-200")}>{value}</div>
    </div>
  );
}

function stateClass(state: string): string {
  if (state === "completed") {
    return "text-emerald-300";
  }
  if (state === "failed" || state === "cancelled") {
    return "text-rose-300";
  }
  if (state === "pending_transcription_engine" || state === "skipped") {
    return "text-amber-200";
  }
  return "text-cyan-200";
}
