"use client";

// ── ModelProfileSelector — Prompt 7 persona strip (Spirit chalk / cyan) ───────
import { memo } from "react";

import { MODEL_PROFILE_ORDER, MODEL_PROFILES } from "@/lib/spirit/model-profiles";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { cn } from "@/lib/cn";

export type ModelProfileSelectorProps = {
  value: ModelProfileId;
  onChange: (profileId: ModelProfileId) => void;
  disabled?: boolean;
  compact?: boolean;
  /** Mobile chat top bar: hide visible “Mode” label, cap select width so Voice/Threads survive. */
  variant?: "default" | "topBar";
};

export const ModelProfileSelector = memo(function ModelProfileSelector({
  value,
  onChange,
  disabled = false,
  compact = false,
  variant = "default",
}: ModelProfileSelectorProps) {
  const topBar = variant === "topBar";
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2",
        compact && "gap-1.5",
        topBar && "min-w-0 max-w-full flex-nowrap gap-1",
      )}
    >
      <span
        className={cn(
          "font-mono text-[9px] font-semibold uppercase tracking-[0.2em] text-chalk/45",
          topBar && "sr-only",
        )}
      >
        Mode
      </span>
      <select
        aria-label="Model profile"
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value as ModelProfileId)}
        className={cn(
          "max-w-full min-w-0 cursor-pointer rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/35 px-2.5 py-1.5 font-mono text-[11px] text-chalk/90 outline-none transition",
          "hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] focus:border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_48%,transparent)] focus:ring-1 focus:ring-[color:color-mix(in_oklab,var(--spirit-accent)_25%,transparent)]",
          "disabled:cursor-not-allowed disabled:opacity-40",
          compact && "py-1 text-[10px]",
          topBar && "max-w-[130px] flex-1 truncate py-1.5 text-[10px]",
        )}
      >
        {MODEL_PROFILE_ORDER.map((id) => (
          <option key={id} value={id}>
            {MODEL_PROFILES[id].shortLabel}
          </option>
        ))}
      </select>
    </div>
  );
});
