"use client";

// ── SpiritUserProfilePanel - Stage 4 tabs (local-only, no fake memory theater) ────
import { Trash2, X } from "lucide-react";
import { memo, useCallback, useEffect, useState } from "react";

import {
  buildModeAwarePersonalizationSummary,
  buildPersonalizationSummary,
  defaultResearchSettings,
  defaultSpiritUserProfile,
  loadSpiritUserProfile,
  PERSONALIZATION_SUMMARY_MAX_CLIENT,
  saveSpiritUserProfile,
  type SpiritUserPreferenceRow,
  type SpiritUserProfileV1,
} from "@/lib/spirit/spirit-user-profile";
import { getModelProfile, MODEL_PROFILE_ORDER, MODEL_PROFILES } from "@/lib/spirit/model-profiles";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { cn } from "@/lib/cn";

export type SpiritUserProfilePanelProps = {
  open: boolean;
  onClose: () => void;
  variant: "popover" | "sheet";
  anchorClassName?: string;
  onProfileChange?: () => void;
  activeModelProfileId?: ModelProfileId;
};

type ProfileTab = "overview" | "personality" | "modes" | "research" | "memory" | "server";

export const SpiritUserProfilePanel = memo(function SpiritUserProfilePanel({
  open,
  onClose,
  variant,
  anchorClassName = "",
  onProfileChange,
  activeModelProfileId = "normal-peer",
}: SpiritUserProfilePanelProps) {
  const [profile, setProfile] = useState<SpiritUserProfileV1>(() => defaultSpiritUserProfile());
  const [tab, setTab] = useState<ProfileTab>("overview");

  useEffect(() => {
    if (!open) return;
    setProfile(loadSpiritUserProfile());
    setTab("overview");
  }, [open]);

  const persist = useCallback(
    (next: SpiritUserProfileV1) => {
      setProfile(next);
      saveSpiritUserProfile(next);
      onProfileChange?.();
    },
    [onProfileChange],
  );

  const rs = profile.researchSettings ?? defaultResearchSettings();
  const modeAwareSummary = buildModeAwarePersonalizationSummary(profile, activeModelProfileId);
  const legacySummary = buildPersonalizationSummary(profile);

  const addPreference = useCallback(() => {
    const row: SpiritUserPreferenceRow = {
      id: `custom_${Date.now()}`,
      label: "New preference",
      value: "Describe what Spirit should remember.",
      source: "manual",
      confidence: "medium",
      category: "other",
    };
    persist({ ...profile, preferences: [...profile.preferences, row] });
  }, [profile, persist]);

  const updateRow = useCallback(
    (id: string, patch: Partial<SpiritUserPreferenceRow>) => {
      persist({
        ...profile,
        preferences: profile.preferences.map((p) => (p.id === id ? { ...p, ...patch } : p)),
      });
    },
    [profile, persist],
  );

  const deleteRow = useCallback(
    (id: string) => {
      persist({
        ...profile,
        preferences: profile.preferences.filter((p) => p.id !== id),
      });
    },
    [profile, persist],
  );

  const resetLocal = useCallback(() => {
    if (!window.confirm("Reset local Spirit profile to defaults?")) return;
    persist(defaultSpiritUserProfile());
  }, [persist]);

  const exportJson = useCallback(() => {
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "spirit-user-profile.json";
    a.click();
    URL.revokeObjectURL(url);
  }, [profile]);

  const importJson = useCallback(() => {
    const raw = window.prompt("Paste JSON profile");
    if (raw === null) return;
    try {
      const o = JSON.parse(raw) as SpiritUserProfileV1;
      if (o?.version !== 1 || !Array.isArray(o.preferences)) throw new Error("bad shape");
      persist(o);
    } catch {
      window.alert("Invalid JSON profile");
    }
  }, [persist]);

  if (!open) return null;

  const sheet = variant === "sheet";
  const mode = getModelProfile(activeModelProfileId);

  const tabBtn = (id: ProfileTab, label: string, testId: string) => (
    <button
      key={id}
      type="button"
      role="tab"
      aria-selected={tab === id}
      data-testid={testId}
      onClick={() => setTab(id)}
      className={cn(
        "shrink-0 rounded-md px-2 py-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide transition",
        tab === id
          ? "bg-[color:color-mix(in_oklab,var(--spirit-accent)_22%,transparent)] text-[color:var(--spirit-accent-strong)]"
          : "text-chalk/50 hover:bg-white/[0.05] hover:text-chalk/75",
      )}
    >
      {label}
    </button>
  );

  return (
    <>
      <button
        type="button"
        aria-label="Close profile panel"
        className="fixed inset-0 z-[140] bg-black/55 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div
        className={cn(
          "fixed z-[150] flex max-h-[80vh] w-[min(100vw-1rem,min(760px,92vw))] flex-col overflow-hidden rounded-xl border border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,black)] shadow-[0_24px_80px_-24px_rgba(0,0,0,0.75)]",
          sheet
            ? "inset-x-0 bottom-0 mx-auto max-h-[80vh] w-full max-w-lg rounded-b-none rounded-t-2xl border-b-0 pb-[env(safe-area-inset-bottom,0px)]"
            : "right-3 top-[3.25rem] max-lg:right-2 max-lg:top-[6.5rem]",
          anchorClassName,
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="spirit-profile-heading"
      >
        <div className="flex items-center justify-between gap-2 border-b border-[color:var(--spirit-border)] px-3 py-2">
          <div className="min-w-0 flex-1">
            <h2
              id="spirit-profile-heading"
              className="font-mono text-[11px] font-semibold uppercase tracking-wider text-chalk"
            >
              Spirit profile
            </h2>
            <p className="mt-0.5 font-mono text-[9px] leading-snug text-amber-200/80">
              Local only - full automatic learning ships later.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-chalk/60 transition hover:bg-white/[0.06] hover:text-chalk"
            aria-label="Close"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div
          className="scrollbar-hide flex shrink-0 gap-1 overflow-x-auto border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] px-2 py-1.5"
          role="tablist"
        >
          {tabBtn("overview", "Overview", "spirit-profile-tab-overview")}
          {tabBtn("personality", "Personality", "spirit-profile-tab-personality")}
          {tabBtn("modes", "Modes", "spirit-profile-tab-modes")}
          {tabBtn("research", "Research", "spirit-profile-tab-research")}
          {tabBtn("memory", "Memory", "spirit-profile-tab-memory")}
          {tabBtn("server", "Server", "spirit-profile-tab-server")}
        </div>
        <div className="scrollbar-hide min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-2">
          {tab === "overview" ? (
            <div data-testid="spirit-profile-tab-panel-overview" className="space-y-2 font-mono text-[10px] text-chalk/75">
              <p className="text-chalk/50">
                Active chat mode: <span className="text-chalk">{mode.shortLabel}</span>
              </p>
              <p>Spirit is local-only for now. Rows below are editable and optionally sent as a compact summary.</p>
              <ul className="list-disc space-y-1 pl-4">
                {profile.preferences.slice(0, 6).map((p) => (
                  <li key={p.id}>
                    <span className="text-chalk">{p.label}:</span> {p.value}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {tab === "personality" ? (
            <div data-testid="spirit-profile-tab-panel-personality" className="space-y-2">
              <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.16em] text-chalk/40">
                Personality stats · editable rows
              </p>
              {profile.preferences.map((row) => (
                <div
                  key={row.id}
                  className="rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] bg-white/[0.03] p-2"
                >
                  <input
                    value={row.label}
                    onChange={(e) => updateRow(row.id, { label: e.target.value, source: "manual" })}
                    className="mb-1 w-full bg-transparent font-mono text-[10px] font-semibold text-chalk outline-none"
                  />
                  <textarea
                    value={row.value}
                    onChange={(e) => updateRow(row.id, { value: e.target.value, source: "manual" })}
                    rows={2}
                    className="w-full resize-none bg-black/20 px-1.5 py-1 font-mono text-[10px] text-chalk/80 outline-none"
                  />
                  <div className="mt-1 flex flex-wrap gap-2 font-mono text-[9px] text-chalk/50">
                    <label>
                      confidence{" "}
                      <select
                        value={row.confidence ?? "medium"}
                        onChange={(e) =>
                          updateRow(row.id, {
                            confidence: e.target.value as SpiritUserPreferenceRow["confidence"],
                            source: "manual",
                          })
                        }
                        className="rounded border border-chalk/20 bg-black/30 px-1 py-0.5 text-chalk"
                      >
                        <option value="low">low</option>
                        <option value="medium">medium</option>
                        <option value="high">high</option>
                      </select>
                    </label>
                    <label className="flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={Boolean(row.wrongPerspective)}
                        onChange={(e) =>
                          updateRow(row.id, { wrongPerspective: e.target.checked, source: "manual" })
                        }
                      />
                      wrong perspective
                    </label>
                    <button
                      type="button"
                      onClick={() => deleteRow(row.id)}
                      className="ml-auto inline-flex items-center gap-1 text-rose-200/90"
                    >
                      <Trash2 className="h-3 w-3" aria-hidden />
                      remove
                    </button>
                  </div>
                  <p className="mt-1 font-mono text-[8px] text-chalk/35">source: {row.source ?? "default"}</p>
                </div>
              ))}
              <button
                type="button"
                onClick={addPreference}
                className="rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] px-3 py-1 font-mono text-[10px] text-[color:var(--spirit-accent-strong)]"
              >
                Add row
              </button>
            </div>
          ) : null}

          {tab === "modes" ? (
            <div data-testid="spirit-profile-tab-panel-modes" className="grid gap-2 sm:grid-cols-2">
              {MODEL_PROFILE_ORDER.map((id) => {
                const m = MODEL_PROFILES[id];
                return (
                  <div
                    key={id}
                    className="rounded-lg border border-white/[0.06] bg-black/25 p-2 font-mono text-[10px] text-chalk/75"
                  >
                    <p className="font-semibold text-chalk">{m.shortLabel}</p>
                    <p className="mt-1 text-[9px] text-chalk/55">{m.description}</p>
                    <p className="mt-1 text-[9px]">budget: {m.responseBudget ?? "-"}</p>
                  </div>
                );
              })}
            </div>
          ) : null}

          {tab === "research" ? (
            <div data-testid="spirit-profile-tab-panel-research" className="space-y-2 font-mono text-[10px] text-chalk/75">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={rs.webSearchDefaultResearcher}
                  onChange={(e) =>
                    persist({
                      ...profile,
                      researchSettings: { ...rs, webSearchDefaultResearcher: e.target.checked },
                    })
                  }
                />
                Web search default for Researcher: ON when checked
              </label>
              <label className="flex items-center gap-2">
                Preferred source age: last 5 years
                <input
                  type="checkbox"
                  checked={rs.preferredSourceAge === "5y"}
                  onChange={(e) =>
                    persist({
                      ...profile,
                      researchSettings: {
                        ...rs,
                        preferredSourceAge: e.target.checked ? "5y" : "any",
                      },
                    })
                  }
                />
              </label>
              <p className="text-[9px] text-chalk/45">
                Require citations / full source list / warn on failure - wired in prefs object (defaults ON).
              </p>
            </div>
          ) : null}

          {tab === "memory" ? (
            <div data-testid="spirit-profile-tab-panel-memory" className="space-y-2 font-mono text-[10px] text-chalk/75">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={profile.sendPersonalizationToServer}
                  onChange={(e) =>
                    persist({ ...profile, sendPersonalizationToServer: e.target.checked })
                  }
                />
                Send compact summary with chat requests
              </label>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={resetLocal} className="rounded-md border border-chalk/20 px-2 py-1">
                  Reset defaults
                </button>
                <button type="button" onClick={exportJson} className="rounded-md border border-chalk/20 px-2 py-1">
                  Export JSON
                </button>
                <button type="button" onClick={importJson} className="rounded-md border border-chalk/20 px-2 py-1">
                  Import JSON
                </button>
              </div>
            </div>
          ) : null}

          {tab === "server" ? (
            <div data-testid="spirit-profile-tab-panel-server" className="space-y-2">
              <p className="font-mono text-[9px] text-chalk/45">
                Mode-aware summary (Researcher adds research prefs). Max {PERSONALIZATION_SUMMARY_MAX_CLIENT} chars.
              </p>
              <p data-testid="spirit-profile-server-char-count" className="font-mono text-[10px] text-[color:var(--spirit-accent-strong)]">
                {modeAwareSummary.length} characters
              </p>
              <pre className="max-h-[42vh] overflow-y-auto whitespace-pre-wrap rounded-lg border border-white/[0.06] bg-black/40 p-2 font-mono text-[10px] leading-snug text-chalk/80">
                {modeAwareSummary || "(empty - toggle send or fill prefs)"}
              </pre>
              <p className="font-mono text-[9px] text-chalk/40">Base prefs-only preview (no mode block):</p>
              <pre className="max-h-24 overflow-y-auto whitespace-pre-wrap font-mono text-[9px] text-chalk/50">
                {legacySummary || " - "}
              </pre>
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
});
