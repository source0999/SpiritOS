"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";

import { useChatThreads } from "@/hooks/useChatThreads";
import { useChatFolders } from "@/hooks/useChatFolders";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";

const ctaLink =
  "inline-flex min-h-[36px] touch-manipulation items-center justify-center gap-1.5 rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-accent)_46%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-3 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 active:scale-[0.98]";

const noop = () => () => {};

export function HomelabChatCoreWidget({ className = "" }: { className?: string }) {
  const mounted = useSyncExternalStore(noop, () => true, () => false);

  const { threads, isLoading: threadsLoading } = useChatThreads(mounted);
  const { folders, isLoading: foldersLoading } = useChatFolders(mounted);

  const threadCount = threads.length;
  const folderCount = folders.length;
  const latestThread = threads[0] ?? null;
  const loading = threadsLoading || foldersLoading;

  return (
    <section
      aria-label="Chat Core"
      className={`homelab-panel homelab-panel-accent p-5 ${className}`}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
            <span className="homelab-status-dot" aria-hidden />
            Spirit · Chat Core
          </p>
          <h2 className="mt-1 font-mono text-[20px] font-semibold uppercase tracking-tight text-chalk">
            Chat Core
          </h2>
          <p className="mt-0.5 font-mono text-[10px] text-chalk/40">
            Dexie persistence · saved threads · folder rail
          </p>
        </div>
        <HomelabStatusBadge variant="live">Ready</HomelabStatusBadge>
      </div>

      <dl className="mb-4 grid gap-y-1.5 font-mono text-[11px]">
        <div className="flex gap-x-2">
          <dt className="text-chalk/45">Threads</dt>
          <dd className="tabular-nums text-chalk/85">
            {!mounted || loading ? " - " : threadCount === 0 ? "No saved threads" : String(threadCount)}
          </dd>
        </div>
        <div className="flex gap-x-2">
          <dt className="text-chalk/45">Folders</dt>
          <dd className="tabular-nums text-chalk/85">
            {!mounted || loading ? " - " : folderCount === 0 ? "None" : String(folderCount)}
          </dd>
        </div>
        <div className="flex gap-x-2">
          <dt className="text-chalk/45">Latest</dt>
          <dd className="min-w-0 flex-1 truncate text-chalk/75">
            {!mounted || loading
              ? " - "
              : latestThread
                ? latestThread.title || "Untitled thread"
                : "No threads yet"}
          </dd>
        </div>
        <div className="flex gap-x-2">
          <dt className="text-chalk/45">Storage</dt>
          <dd className="text-chalk/75">IndexedDB · Dexie</dd>
        </div>
      </dl>

      {mounted && !loading && threadCount === 0 && (
        <p className="mb-4 rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-2 font-mono text-[10px] text-chalk/45">
          No saved threads - start a chat to create your first session.
        </p>
      )}

      <Link href="/chat" className={ctaLink} style={{ width: "100%", justifyContent: "center" }}>
        Open Chat Workspace →
      </Link>
    </section>
  );
}
