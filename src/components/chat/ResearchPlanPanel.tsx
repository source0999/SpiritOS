"use client";

// ── ResearchPlanPanel — plan gate before /api/spirit research (Prompt 10C-D) ─────
// > Sits above the composer, not under sticky chrome. Internal scroll + sticky actions.

import { Plus, Play, Trash2, X } from "lucide-react";
import { memo, useCallback, useState } from "react";

import type { ResearchPlan, ResearchPlanStep } from "@/lib/spirit/research-plan";
import {
  addResearchPlanStep,
  editResearchPlanStep,
  removeResearchPlanStep,
} from "@/lib/spirit/research-plan";
import { cn } from "@/lib/cn";

export type ResearchPlanPanelProps = {
  open: boolean;
  plan: ResearchPlan | null;
  onClose: () => void;
  onPlanChange: (next: ResearchPlan) => void;
  onStartResearch: (plan: ResearchPlan) => void;
  variant?: "inline" | "sheet";
};

export const ResearchPlanPanel = memo(function ResearchPlanPanel({
  open,
  plan,
  onClose,
  onPlanChange,
  onStartResearch,
  variant = "inline",
}: ResearchPlanPanelProps) {
  const [newLabel, setNewLabel] = useState("");

  const updateStep = useCallback(
    (id: string, patch: Partial<Pick<ResearchPlanStep, "label" | "detail" | "searchQuery">>) => {
      if (!plan) return;
      onPlanChange(editResearchPlanStep(plan, id, patch));
    },
    [plan, onPlanChange],
  );

  const removeStep = useCallback(
    (id: string) => {
      if (!plan) return;
      onPlanChange(removeResearchPlanStep(plan, id));
    },
    [plan, onPlanChange],
  );

  const addStep = useCallback(() => {
    if (!plan || !newLabel.trim()) return;
    onPlanChange(addResearchPlanStep(plan, newLabel.trim()));
    setNewLabel("");
  }, [plan, newLabel, onPlanChange]);

  if (!open || !plan) return null;

  const sheet = variant === "sheet";

  return (
    <div
      data-testid="research-plan-panel"
      className={cn(
        "relative z-[42] flex max-h-[min(280px,45dvh)] min-h-0 shrink-0 flex-col border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-black/40 shadow-[inset_0_-1px_0_rgba(255,255,255,0.03)]",
        sheet && "fixed inset-x-0 bottom-0 z-[120] max-h-[70dvh] rounded-t-xl border-x border-t",
      )}
    >
      <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-2 py-2 sm:px-3">
        <div className="flex shrink-0 items-start justify-between gap-2 border-b border-white/[0.06] pb-2">
          <div>
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-chalk/45">
              Research plan
            </p>
            <p className="mt-0.5 font-mono text-[11px] text-chalk/75">
              Edit the checklist, then <span className="text-[color:var(--spirit-accent-strong)]">Start research</span>{" "}
              — nothing hits /api/spirit until you do.
            </p>
            <p
              data-testid="research-plan-no-cot"
              className="mt-1 font-mono text-[9px] text-chalk/40"
            >
              No private chain-of-thought — editable checklist only.
            </p>
          </div>
          <button
            type="button"
            aria-label="Close research plan"
            onClick={onClose}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[color:var(--spirit-border)]/70 text-chalk/60 hover:bg-white/[0.06]"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <div className="scrollbar-hide min-h-0 flex-1 overflow-y-auto overscroll-y-contain py-2">
          <p className="font-mono text-[10px] font-semibold text-[color:var(--spirit-accent-strong)]">{plan.title}</p>
          <ul className="mt-2 space-y-1.5">
            {plan.steps.map((s) => (
              <li
                key={s.id}
                className="rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] bg-white/[0.03] p-2"
              >
                <input
                  value={s.label}
                  onChange={(e) => updateStep(s.id, { label: e.target.value })}
                  className="w-full bg-transparent font-mono text-[11px] text-chalk outline-none"
                  aria-label="Step label"
                />
                <textarea
                  value={s.detail ?? ""}
                  onChange={(e) => updateStep(s.id, { detail: e.target.value })}
                  placeholder="Optional detail"
                  rows={2}
                  className="mt-1 w-full resize-none bg-black/25 px-1.5 py-1 font-mono text-[10px] text-chalk/80 outline-none"
                />
                <div className="mt-1 flex justify-end">
                  <button
                    type="button"
                    onClick={() => removeStep(s.id)}
                    className="inline-flex items-center gap-1 font-mono text-[9px] text-rose-200/90"
                  >
                    <Trash2 className="h-3 w-3" aria-hidden />
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex flex-wrap items-end gap-2">
            <input
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="New step label"
              className="min-w-[8rem] flex-1 rounded-md border border-[color:var(--spirit-border)] bg-black/30 px-2 py-1 font-mono text-[10px] text-chalk"
            />
            <button
              type="button"
              onClick={addStep}
              className="inline-flex items-center gap-1 rounded-md border border-[color:var(--spirit-border)] px-2 py-1 font-mono text-[10px] text-chalk/80"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden />
              Add step
            </button>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2 border-t border-white/[0.06] bg-[color:color-mix(in_oklab,var(--spirit-bg)_92%,black)] py-2 pt-2">
          <button
            type="button"
            data-testid="research-plan-start"
            onClick={() => onStartResearch(plan)}
            className="inline-flex items-center gap-1.5 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-3 py-1.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-[color:var(--spirit-accent-strong)]"
          >
            <Play className="h-3.5 w-3.5" aria-hidden />
            Start research
          </button>
          <button
            type="button"
            data-testid="research-plan-cancel"
            onClick={onClose}
            className="rounded-full border border-[color:var(--spirit-border)] px-3 py-1.5 font-mono text-[10px] text-chalk/65"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
});
