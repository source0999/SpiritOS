"use client";

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { CheckCircle2, Download, FolderSearch, ShieldAlert, X } from "lucide-react";
import type {
  SpiritFlixSmartBatchPreview,
  SpiritFlixSmartBatchReviewMode,
  SpiritFlixSmartRenamePlan,
} from "@/lib/spiritflix/admin/smart";

interface SpiritFlixSmartBatchPanelProps {
  currentPath: string;
  open: boolean;
  onClose: () => void;
}

interface BatchResponse extends SpiritFlixSmartBatchPreview {
  error?: string;
}

interface RenamePlanResponse extends SpiritFlixSmartRenamePlan {
  error?: string;
}

function statusLabel(status: string): string {
  if (status === "already_current") return "current";
  return status.replace(/_/g, " ");
}

export function SpiritFlixSmartBatchPanel({ currentPath, open, onClose }: SpiritFlixSmartBatchPanelProps) {
  const [result, setResult] = useState<SpiritFlixSmartBatchPreview | null>(null);
  const [renamePlan, setRenamePlan] = useState<SpiritFlixSmartRenamePlan | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const callBatch = useCallback(async (action: "preview" | "run") => {
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/batch", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: currentPath, action, maxItems: 12 }),
      });
      const payload = (await response.json()) as BatchResponse;
      if (!response.ok) throw new Error(payload.error ?? "Smart batch request failed.");
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Smart batch request failed.");
    } finally {
      setRunning(false);
    }
  }, [currentPath]);

  const callReview = useCallback(async (reviewMode: SpiritFlixSmartBatchReviewMode) => {
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/batch", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: currentPath, action: "review", reviewMode, maxItems: 50 }),
      });
      const payload = (await response.json()) as BatchResponse;
      if (!response.ok) throw new Error(payload.error ?? "Smart batch review failed.");
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Smart batch review failed.");
    } finally {
      setRunning(false);
    }
  }, [currentPath]);

  const callRenamePlan = useCallback(async () => {
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/batch", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: currentPath, action: "renamePlan", maxItems: 50 }),
      });
      const payload = (await response.json()) as RenamePlanResponse;
      if (!response.ok) throw new Error(payload.error ?? "Smart rename plan failed.");
      setRenamePlan(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Smart rename plan failed.");
    } finally {
      setRunning(false);
    }
  }, [currentPath]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div className="spiritflix-smart-batch" role="presentation">
      <button className="spiritflix-smart-review__backdrop" type="button" aria-label="Close smart batch panel" onClick={onClose} />
      <aside className="spiritflix-smart-batch__panel" aria-label="Smart batch analysis" role="dialog" aria-modal="true">
        <header className="spiritflix-smart-review__header">
          <div>
            <p className="spiritflix-smart-review__eyebrow">
              <FolderSearch size={15} aria-hidden="true" />
              Batch smart
            </p>
            <h2>Folder analysis</h2>
          </div>
          <button className="spiritflix-smart-review__close" type="button" aria-label="Close" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <p className="spiritflix-smart-review__path">{currentPath}</p>
        <p className="spiritflix-smart-review__boundary">
          S8 writes analysis/review sidecars and exports rename plans only. Real rename or move is disabled here.
        </p>
        {error ? <p className="spiritflix-smart-review__error">{error}</p> : null}

        <section className="spiritflix-smart-review__section">
          <h3>Batch controls</h3>
          <div className="spiritflix-smart-review__action-buttons">
            <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callBatch("preview")}>
              {running ? "Working..." : "Preview folder"}
            </button>
            <button className="spiritflix-smart-review__primary" type="button" disabled={running} onClick={() => void callBatch("run")}>
              {running ? "Working..." : "Analyze folder"}
            </button>
            <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("approve_all_tags")}>
              <CheckCircle2 size={15} aria-hidden="true" />
              Approve tags
            </button>
            <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("reject_all_tags")}>
              <ShieldAlert size={15} aria-hidden="true" />
              Reject tags
            </button>
            <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("mark_reviewed")}>
              Mark reviewed
            </button>
            <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callRenamePlan()}>
              <Download size={15} aria-hidden="true" />
              Rename plan
            </button>
          </div>
        </section>

        {result ? (
          <>
            <section className="spiritflix-smart-review__section">
              <h3>Summary</h3>
              <dl className="spiritflix-smart-review__grid">
                <div>
                  <dt>Mode</dt>
                  <dd>{result.mode}</dd>
                </div>
                <div>
                  <dt>Candidates</dt>
                  <dd>{result.counts.candidates}</dd>
                </div>
                <div>
                  <dt>Analyzed</dt>
                  <dd>{result.counts.analyzed}</dd>
                </div>
                <div>
                  <dt>Current</dt>
                  <dd>{result.counts.already_current}</dd>
                </div>
                <div>
                  <dt>Needs review</dt>
                  <dd>{result.counts.needs_review}</dd>
                </div>
                <div>
                  <dt>Rename previews</dt>
                  <dd>{result.counts.rename_preview_available}</dd>
                </div>
                <div>
                  <dt>Failed</dt>
                  <dd>{result.counts.failed}</dd>
                </div>
              </dl>
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Videos</h3>
              <div className="spiritflix-smart-batch__items">
                {result.items.map((item) => (
                  <article className="spiritflix-smart-batch__item" key={item.path}>
                    <div>
                      <p className="spiritflix-smart-batch__name">{item.name}</p>
                      <p className="spiritflix-smart-batch__meta">
                        {statusLabel(item.status)} · {item.reviewStatus ?? "unreviewed"} · {item.suggestedTagCount} tags
                      </p>
                    </div>
                    <span className={item.renamePreviewAvailable ? "is-ready" : ""}>
                      {item.renamePreviewAvailable ? "rename preview" : item.needsReview ? "review" : "pending"}
                    </span>
                    {item.reason ? <p className="spiritflix-smart-batch__reason">{item.reason}</p> : null}
                  </article>
                ))}
              </div>
            </section>
          </>
        ) : null}

        {renamePlan ? (
          <section className="spiritflix-smart-review__section">
            <h3>Rename plan</h3>
            <p className="spiritflix-smart-review__boundary">{renamePlan.applyGate}</p>
            <dl className="spiritflix-smart-review__grid">
              <div>
                <dt>Ready</dt>
                <dd>{renamePlan.counts.ready}</dd>
              </div>
              <div>
                <dt>Blocked</dt>
                <dd>{renamePlan.counts.blocked}</dd>
              </div>
              <div>
                <dt>Needs review</dt>
                <dd>{renamePlan.counts.needs_review}</dd>
              </div>
              <div>
                <dt>Collisions</dt>
                <dd>{renamePlan.counts.collisions}</dd>
              </div>
              <div>
                <dt>Target conflicts</dt>
                <dd>{renamePlan.counts.target_conflicts}</dd>
              </div>
              <div>
                <dt>Apply enabled</dt>
                <dd>{renamePlan.applyEnabled ? "Yes" : "No"}</dd>
              </div>
            </dl>
            <div className="spiritflix-smart-batch__items">
              {renamePlan.items.map((item) => (
                <article className="spiritflix-smart-batch__item" key={item.sourcePath}>
                  <div>
                    <p className="spiritflix-smart-batch__name">{item.currentName}</p>
                    <p className="spiritflix-smart-batch__meta">
                      {item.suggestedName ?? "no proposal"} - {item.reviewStatus} - {item.status}
                    </p>
                  </div>
                  <span className={item.readyForLevel2Preview ? "is-ready" : ""}>
                    {item.readyForLevel2Preview ? "ready" : "blocked"}
                  </span>
                  {item.warnings.length ? (
                    <p className="spiritflix-smart-batch__reason">{item.warnings.join(" ")}</p>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <footer className="spiritflix-smart-review__footer">
          <button className="spiritflix-smart-review__secondary" type="button" onClick={onClose}>
            Close
          </button>
        </footer>
      </aside>
    </div>,
    document.body,
  );
}
