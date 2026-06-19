"use client";

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { CheckCircle2, Download, FolderSearch, RotateCw, ShieldAlert, X } from "lucide-react";
import type {
  SpiritFlixSmartBatchItem,
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

function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function renameStatusLabel(item: SpiritFlixSmartBatchItem): string {
  if (item.renamePreviewStatus === "ready") return "Rename preview ready";
  if (item.renamePreviewStatus === "provisional") return "Provisional preview";
  if (item.renamePreviewStatus === "needs_review") return "Needs review first";
  if (item.renamePreviewStatus === "missing_suggestion") return "No approved filename";
  if (item.renamePreviewStatus === "blocked") return "Rename preview blocked";
  return "Rename preview unavailable";
}

function operatorStatus(item: SpiritFlixSmartBatchItem): string {
  if (item.status === "failed") return "failed";
  if (item.reviewStatus === "reviewed") return "reviewed";
  if (item.needsReview || item.pendingTagCount > 0 || item.renamePreviewStatus === "needs_review") return "needs review";
  if (item.status === "analyzed" || item.status === "already_current" || item.sidecarCurrent) return "analyzed";
  return "candidate";
}

function tagEmptyMessage(result: SpiritFlixSmartBatchPreview, item: SpiritFlixSmartBatchItem): string {
  if (result.mode === "preview" && item.status === "candidate") return "No tags yet - run Analyze folder";
  if (!item.sidecarCurrent && !item.analysisStatus) return "No tags yet - run Analyze folder";
  return "No tags found";
}

function recommendedNameMessage(item: SpiritFlixSmartBatchItem): { title: string; detail?: string; blocked?: boolean } {
  if (item.proposedFilename && item.renamePreviewStatus === "ready") {
    return { title: item.proposedFilename, detail: "Ready recommended name" };
  }
  if (item.proposedFilename) {
    return { title: item.proposedFilename, detail: "Provisional recommended name, not apply-ready" };
  }
  if (!item.sidecarCurrent && !item.analysisStatus) return { title: "Run Analyze folder first" };
  if (item.reviewStatus === "unreviewed" || item.renamePreviewStatus === "needs_review") {
    return { title: "Review/approve tags to unlock final rename preview" };
  }
  if (item.renameBlocker) return { title: item.renameBlocker, blocked: true };
  return { title: "No recommended name available" };
}

function renamePlanButtonLabel(result: SpiritFlixSmartBatchPreview | null): string {
  if (!result) return "Rename plan";
  const hasAnalyzed = result.counts.analyzed > 0 || result.counts.already_current > 0;
  if (!hasAnalyzed) return "Analyze folder first";
  if (result.counts.needs_review > 0) return "Review/approve items to create final rename plan";
  return "View rename plan";
}

function renamePlanHint(result: SpiritFlixSmartBatchPreview | null): string {
  if (!result) return "Run Preview folder or Analyze folder to inspect names.";
  const hasAnalyzed = result.counts.analyzed > 0 || result.counts.already_current > 0;
  const hasProvisional = result.items.some((item) => item.renamePreviewStatus === "provisional" && item.proposedFilename);
  if (!hasAnalyzed) return "Analyze folder first.";
  if (result.counts.needs_review > 0) return "Review/approve items to create final rename plan.";
  if (hasProvisional) return "Provisional names are visible, but not apply-ready.";
  return "Rename plan remains preview-only; real apply is disabled.";
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

  const callReview = useCallback(async (reviewMode: SpiritFlixSmartBatchReviewMode, paths?: string[]) => {
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/batch", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: currentPath, paths, action: "review", reviewMode, maxItems: 50 }),
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

  const refreshItem = useCallback(async (path: string) => {
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/batch", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: currentPath, paths: [path], action: "run", force: true, maxItems: 1 }),
      });
      const payload = (await response.json()) as BatchResponse;
      if (!response.ok) throw new Error(payload.error ?? "Smart item refresh failed.");
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Smart item refresh failed.");
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
          S8.1 writes analysis/review sidecars and exports rename plans only. Real rename/move apply is disabled until Britton explicitly approves a future apply task.
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
              {renamePlanButtonLabel(result)}
            </button>
          </div>
          <p className="spiritflix-smart-batch__hint">{renamePlanHint(result)}</p>
        </section>

        {result ? (
          <>
            <section className="spiritflix-smart-review__section">
              <h3>Summary</h3>
              <dl className="spiritflix-smart-review__grid">
                <div>
                  <dt>Candidates</dt>
                  <dd>{result.counts.candidates}</dd>
                </div>
                <div>
                  <dt>Analyzed</dt>
                  <dd>{result.counts.analyzed}</dd>
                </div>
                <div>
                  <dt>Needs review</dt>
                  <dd>{result.counts.needs_review}</dd>
                </div>
                <div>
                  <dt>Ready names</dt>
                  <dd>{result.counts.rename_preview_available}</dd>
                </div>
                <div>
                  <dt>Failed</dt>
                  <dd>{result.counts.failed}</dd>
                </div>
              </dl>
              <p className="spiritflix-smart-review__boundary">
                Preview folder only lists candidates. Analyze folder reads metadata and creates smart tags. Recommended names become final after review/approval.
              </p>
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Videos</h3>
              <div className="spiritflix-smart-batch__items">
                {result.items.map((item) => (
                  <article className="spiritflix-smart-batch__item" key={item.path}>
                    <div className="spiritflix-smart-batch__item-header">
                      <div className="spiritflix-smart-batch__title-block">
                      <p className="spiritflix-smart-batch__name">{item.name}</p>
                        <p className="spiritflix-smart-batch__meta">{item.parentPath}</p>
                      </div>
                      <span className={`spiritflix-smart-batch__status is-${operatorStatus(item).replace(/\s+/g, "-")}`}>
                        {operatorStatus(item)}
                      </span>
                    </div>

                    <section className="spiritflix-smart-batch__operator-section">
                      <h4>Smart tags</h4>
                      {item.tags.length ? (
                        <div className="spiritflix-smart-review__tags">
                          {item.tags.map((tag) => (
                            <span
                              className={`spiritflix-smart-tag-pill is-group-${tag.group}${tag.reviewRequired ? " is-review-required" : ""}`}
                              key={tag.id}
                              title={`${tag.group} - ${formatConfidence(tag.confidence)} confidence${tag.reviewRequired ? " - review required" : ""}`}
                            >
                              <span className="spiritflix-smart-tag-pill__label">{tag.label}</span>
                              <span className="spiritflix-smart-tag-pill__meta">{formatConfidence(tag.confidence)}</span>
                              <span className="spiritflix-smart-tag-pill__flag">{tag.reviewState}</span>
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="spiritflix-smart-batch__empty">{tagEmptyMessage(result, item)}</p>
                      )}
                    </section>

                    <section className="spiritflix-smart-batch__operator-section">
                      <h4>Recommended name</h4>
                      {(() => {
                        const message = recommendedNameMessage(item);
                        return (
                          <>
                            <p className={message.blocked ? "spiritflix-smart-batch__blocker" : "spiritflix-smart-batch__recommended-name"}>{message.title}</p>
                            {message.detail ? <p className="spiritflix-smart-batch__meta">{message.detail}</p> : null}
                          </>
                        );
                      })()}
                    </section>

                    <div className="spiritflix-smart-batch__actions">
                      <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void refreshItem(item.path)}>
                        <RotateCw size={15} aria-hidden="true" />
                        Analyze/refresh item
                      </button>
                      <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("approve_all_tags", [item.path])}>
                        Approve tags
                      </button>
                      <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("reject_all_tags", [item.path])}>
                        Reject tags
                      </button>
                      <button className="spiritflix-smart-review__secondary" type="button" disabled={running} onClick={() => void callReview("mark_reviewed", [item.path])}>
                        Mark reviewed
                      </button>
                    </div>

                    <details className="spiritflix-smart-batch__advanced">
                      <summary>Advanced details</summary>
                      <dl className="spiritflix-smart-review__grid">
                        <div>
                          <dt>Batch status</dt>
                          <dd>{statusLabel(item.status)}</dd>
                        </div>
                        <div>
                          <dt>Analysis status</dt>
                          <dd>{item.analysisStatus ?? "not analyzed"}</dd>
                        </div>
                        <div>
                          <dt>Review status</dt>
                          <dd>{item.reviewStatus ?? "unreviewed"}</dd>
                        </div>
                        <div>
                          <dt>Tag counts</dt>
                          <dd>{item.approvedTagCount} approved, {item.rejectedTagCount} rejected, {item.pendingTagCount} pending</dd>
                        </div>
                        <div>
                          <dt>Rename status</dt>
                          <dd>{renameStatusLabel(item)}</dd>
                        </div>
                        <div>
                          <dt>Sidecar</dt>
                          <dd>{item.sidecarRef ?? "none"}</dd>
                        </div>
                        <div>
                          <dt>Target path</dt>
                          <dd className="is-mono">{item.proposedTargetPath ?? "not available"}</dd>
                        </div>
                      </dl>
                      {item.renameBlocker ? <p className="spiritflix-smart-batch__reason">{item.renameBlocker}</p> : null}
                      {item.renameWarnings.length ? <p className="spiritflix-smart-batch__reason">{item.renameWarnings.join(" ")}</p> : null}
                      {item.reason ? <p className="spiritflix-smart-batch__reason">{item.reason}</p> : null}
                    </details>
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
                      {item.suggestedName ?? "no proposal"} - {item.readyForLevel2Preview ? "ready recommended name" : "not apply-ready"}
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
