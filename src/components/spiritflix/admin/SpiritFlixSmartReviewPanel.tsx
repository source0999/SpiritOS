"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { Sparkles, X } from "lucide-react";
import type { SpiritFlixSmartAnalysis, SpiritFlixSmartReviewInput } from "@/lib/spiritflix/admin/smart/types";
import { buildEmptyReviewDraft, countReviewTagStates, tagReviewState } from "@/lib/spiritflix/admin/smart/review-metadata";
import type { SpiritFlixAdminItem } from "@/lib/spiritflix/admin/types";
import { SpiritFlixSmartTagPill } from "./SpiritFlixSmartTagPill";

interface SpiritFlixSmartReviewPanelProps {
  item: SpiritFlixAdminItem;
  open: boolean;
  onClose: () => void;
}

interface SmartAnalysisResponse {
  analysis: SpiritFlixSmartAnalysis | null;
  sidecarPath?: string;
}

interface ExportMetadataResponse {
  metadataPath?: string;
  metadata?: {
    sourcePath: string;
    displayTitle?: string;
    filenameSuggestion?: string;
    category?: string;
    collections: string[];
    approvedTags: Array<{ id: string; label: string; group: string; confidence: number }>;
    rejectedTagIds: string[];
    reviewStatus: string;
    reviewedAt?: string;
    notes?: string;
  };
  error?: string;
}

interface PrepareRenameResponse {
  renamePreview?: {
    sourcePath: string;
    suggestedName: string;
    targetPath: string;
    warnings: string[];
    readyForLevel2Preview: boolean;
  };
  error?: string;
}

function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatReviewStatus(status: string | undefined): string {
  switch (status) {
    case "partially_reviewed":
      return "Partially reviewed";
    case "reviewed":
      return "Reviewed";
    case "rejected":
      return "Rejected";
    default:
      return "Unreviewed";
  }
}

function collectionsToInput(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

export function SpiritFlixSmartReviewPanel({ item, open, onClose }: SpiritFlixSmartReviewPanelProps) {
  const [analysis, setAnalysis] = useState<SpiritFlixSmartAnalysis | null>(null);
  const [sidecarPath, setSidecarPath] = useState<string | null>(null);
  const [draft, setDraft] = useState<SpiritFlixSmartReviewInput>({
    approvedTagIds: [],
    rejectedTagIds: [],
    editedDisplayTitle: "",
    editedFilenameSuggestion: "",
    editedCategory: "",
    editedCollections: [],
    notes: "",
  });
  const [collectionsInput, setCollectionsInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [marking, setMarking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  // S6 state
  const [exporting, setExporting] = useState(false);
  const [preparingRename, setPreparingRename] = useState(false);
  const [exportResult, setExportResult] = useState<ExportMetadataResponse["metadata"] | null>(null);
  const [renamePreview, setRenamePreview] = useState<PrepareRenameResponse["renamePreview"] | null>(null);

  const syncDraftFromAnalysis = useCallback((next: SpiritFlixSmartAnalysis | null) => {
    const nextDraft = buildEmptyReviewDraft(next);
    setDraft(nextDraft);
    setCollectionsInput((nextDraft.editedCollections ?? []).join(", "));
  }, []);

  const loadAnalysis = useCallback(async () => {
    if (!item.path) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/spiritflix/admin/smart/analysis?path=${encodeURIComponent(item.path)}`, {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      const payload = (await response.json()) as SmartAnalysisResponse & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Failed to load smart analysis.");
      setAnalysis(payload.analysis);
      setSidecarPath(payload.sidecarPath ?? null);
      syncDraftFromAnalysis(payload.analysis);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load smart analysis.");
      setAnalysis(null);
      setSidecarPath(null);
      syncDraftFromAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, [item.path, syncDraftFromAnalysis]);

  useEffect(() => {
    if (!open) return;
    void loadAnalysis();
  }, [open, loadAnalysis]);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  const runAnalyze = useCallback(async () => {
    if (!item.path) return;
    setAnalyzing(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/analysis", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path, action: "analyze" }),
      });
      const payload = (await response.json()) as SmartAnalysisResponse & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Smart analysis failed.");
      setAnalysis(payload.analysis);
      setSidecarPath(payload.sidecarPath ?? null);
      syncDraftFromAnalysis(payload.analysis);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Smart analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }, [item.path, syncDraftFromAnalysis]);

  const runMarkReviewed = useCallback(async () => {
    if (!item.path || !analysis) return;
    setMarking(true);
    setError("");
    try {
      const response = await fetch("/api/spiritflix/admin/smart/analysis", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path, action: "markReviewed" }),
      });
      const payload = (await response.json()) as SmartAnalysisResponse & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Failed to mark reviewed.");
      setAnalysis(payload.analysis);
      setSidecarPath(payload.sidecarPath ?? null);
      syncDraftFromAnalysis(payload.analysis);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to mark reviewed.");
    } finally {
      setMarking(false);
    }
  }, [analysis, item.path, syncDraftFromAnalysis]);

  const runSaveReview = useCallback(async () => {
    if (!item.path || !analysis) return;
    setSaving(true);
    setError("");
    try {
      const payloadReview: SpiritFlixSmartReviewInput = {
        ...draft,
        editedCollections: collectionsToInput(collectionsInput),
        editedDisplayTitle: draft.editedDisplayTitle?.trim() || undefined,
        editedFilenameSuggestion: draft.editedFilenameSuggestion?.trim() || undefined,
        editedCategory: draft.editedCategory?.trim() || undefined,
        notes: draft.notes?.trim() || undefined,
      };
      const response = await fetch("/api/spiritflix/admin/smart/analysis", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path, action: "saveReview", review: payloadReview }),
      });
      const payload = (await response.json()) as SmartAnalysisResponse & { error?: string };
      if (!response.ok) throw new Error(payload.error ?? "Failed to save review.");
      setAnalysis(payload.analysis);
      setSidecarPath(payload.sidecarPath ?? null);
      syncDraftFromAnalysis(payload.analysis);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save review.");
    } finally {
      setSaving(false);
    }
  }, [analysis, collectionsInput, draft, item.path, syncDraftFromAnalysis]);

  // S6: export approved metadata to admin metadata sidecar
  const runExportMetadata = useCallback(async () => {
    if (!item.path || !analysis) return;
    setExporting(true);
    setError("");
    setExportResult(null);
    try {
      const response = await fetch("/api/spiritflix/admin/smart/analysis", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path, action: "exportMetadata" }),
      });
      const payload = (await response.json()) as ExportMetadataResponse;
      if (!response.ok) throw new Error(payload.error ?? "Failed to export metadata.");
      setExportResult(payload.metadata ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to export metadata.");
    } finally {
      setExporting(false);
    }
  }, [analysis, item.path]);

  // S6: prepare rename preview
  const runPrepareRenamePreview = useCallback(async () => {
    if (!item.path || !analysis) return;
    setPreparingRename(true);
    setError("");
    setRenamePreview(null);
    try {
      const response = await fetch("/api/spiritflix/admin/smart/analysis", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ path: item.path, action: "prepareRenamePreview" }),
      });
      const payload = (await response.json()) as PrepareRenameResponse;
      if (!response.ok) throw new Error(payload.error ?? "Failed to prepare rename preview.");
      setRenamePreview(payload.renamePreview ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to prepare rename preview.");
    } finally {
      setPreparingRename(false);
    }
  }, [analysis, item.path]);

  const tagCounts = useMemo(() => (analysis ? countReviewTagStates(analysis, draft) : { approved: 0, rejected: 0, pending: 0 }), [analysis, draft]);

  const setTagDecision = useCallback((tagId: string, decision: "approved" | "rejected" | "pending") => {
    setDraft((current) => {
      const approvedTagIds = current.approvedTagIds.filter((id) => id !== tagId);
      const rejectedTagIds = current.rejectedTagIds.filter((id) => id !== tagId);
      if (decision === "approved") approvedTagIds.push(tagId);
      if (decision === "rejected") rejectedTagIds.push(tagId);
      return { ...current, approvedTagIds, rejectedTagIds };
    });
  }, []);

  if (!open || typeof document === "undefined") return null;

  const reviewStatus = analysis?.reviewedMetadata?.reviewStatus ?? "unreviewed";
  const sampleCount = analysis?.samples.length ?? 0;
  const evidenceTimestamps = analysis?.samples.map((sample) => sample.timestampLabel).join(", ") ?? "";
  const hasReviewedMetadata = analysis?.reviewedMetadata != null && analysis.reviewedMetadata.reviewStatus !== "unreviewed";

  return createPortal(
    <div className="spiritflix-smart-review" role="presentation">
      <button className="spiritflix-smart-review__backdrop" type="button" aria-label="Close smart review panel" onClick={onClose} />
      <aside className="spiritflix-smart-review__panel" aria-label="Smart tag review" role="dialog" aria-modal="true">
        <header className="spiritflix-smart-review__header">
          <div>
            <p className="spiritflix-smart-review__eyebrow">
              <Sparkles size={15} aria-hidden="true" />
              Smart tags
            </p>
            <h2>{item.name}</h2>
          </div>
          <button className="spiritflix-smart-review__close" type="button" aria-label="Close" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <p className="spiritflix-smart-review__path">{item.path}</p>
        <p className="spiritflix-smart-review__boundary">
          S6 prepares metadata and rename preview only. It does not rename or move files.
        </p>

        {loading ? <p className="spiritflix-smart-review__status">Loading smart analysis…</p> : null}
        {error ? <p className="spiritflix-smart-review__error">{error}</p> : null}

        {!loading && !analysis ? (
          <section className="spiritflix-smart-review__section">
            <h3>No smart analysis yet</h3>
            <p>Run a one-video scan to collect metadata, sample frames, and heuristic suggestions. Nothing is renamed or moved.</p>
          </section>
        ) : null}

        {analysis ? (
          <>
            <section className="spiritflix-smart-review__section">
              <h3>Status</h3>
              <dl className="spiritflix-smart-review__grid">
                <div>
                  <dt>Analysis status</dt>
                  <dd>{analysis.status}</dd>
                </div>
                <div>
                  <dt>Review status</dt>
                  <dd>{formatReviewStatus(reviewStatus)}</dd>
                </div>
                <div>
                  <dt>Confidence</dt>
                  <dd>{formatConfidence(analysis.confidence)}</dd>
                </div>
                <div>
                  <dt>Tag counts</dt>
                  <dd>
                    {tagCounts.approved} approved · {tagCounts.rejected} rejected · {tagCounts.pending} pending
                  </dd>
                </div>
                <div>
                  <dt>Safety</dt>
                  <dd>{analysis.safety.requiresHumanReview ? "Human review required" : "Review optional"}</dd>
                </div>
              </dl>
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Review metadata</h3>
              <label className="spiritflix-smart-review__field">
                <span>Display title</span>
                <input
                  type="text"
                  value={draft.editedDisplayTitle ?? ""}
                  onChange={(event) => setDraft((current) => ({ ...current, editedDisplayTitle: event.target.value }))}
                />
              </label>
              <label className="spiritflix-smart-review__field">
                <span>Filename suggestion only</span>
                <input
                  type="text"
                  value={draft.editedFilenameSuggestion ?? ""}
                  onChange={(event) => setDraft((current) => ({ ...current, editedFilenameSuggestion: event.target.value }))}
                />
                <small>This does not rename the file yet.</small>
              </label>
              <label className="spiritflix-smart-review__field">
                <span>Category</span>
                <input
                  type="text"
                  value={draft.editedCategory ?? ""}
                  onChange={(event) => setDraft((current) => ({ ...current, editedCategory: event.target.value }))}
                />
              </label>
              <label className="spiritflix-smart-review__field">
                <span>Collections (comma-separated)</span>
                <input type="text" value={collectionsInput} onChange={(event) => setCollectionsInput(event.target.value)} />
              </label>
              <label className="spiritflix-smart-review__field">
                <span>Review notes</span>
                <textarea value={draft.notes ?? ""} onChange={(event) => setDraft((current) => ({ ...current, notes: event.target.value }))} rows={3} />
              </label>
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Original suggestions</h3>
              <dl className="spiritflix-smart-review__grid">
                <div>
                  <dt>Display title</dt>
                  <dd>{analysis.suggestedDisplayTitle ?? "—"}</dd>
                </div>
                <div>
                  <dt>Suggested filename</dt>
                  <dd>{analysis.suggestedFilename ?? "—"}</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>{analysis.suggestedCategory ?? "—"}</dd>
                </div>
                <div>
                  <dt>Collections</dt>
                  <dd>{analysis.suggestedCollections?.join(", ") || "—"}</dd>
                </div>
              </dl>
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Tags</h3>
              {analysis.suggestedTags.length ? (
                <div className="spiritflix-smart-review__tags">
                  {analysis.suggestedTags.map((tag) => (
                    <SpiritFlixSmartTagPill
                      key={tag.id}
                      tag={tag}
                      reviewState={tagReviewState(tag.id, draft)}
                      onApprove={() => setTagDecision(tag.id, "approved")}
                      onReject={() => setTagDecision(tag.id, "rejected")}
                      onReset={() => setTagDecision(tag.id, "pending")}
                    />
                  ))}
                </div>
              ) : (
                <p>No suggested tags.</p>
              )}
            </section>

            <section className="spiritflix-smart-review__section">
              <h3>Evidence</h3>
              <dl className="spiritflix-smart-review__grid">
                <div>
                  <dt>Samples</dt>
                  <dd>{sampleCount}</dd>
                </div>
                <div>
                  <dt>Timestamps</dt>
                  <dd>{evidenceTimestamps || "—"}</dd>
                </div>
                <div>
                  <dt>Sidecar</dt>
                  <dd className="is-mono">{sidecarPath ? sidecarPath.split("/").slice(-2).join("/") : "—"}</dd>
                </div>
              </dl>
            </section>

            {analysis.notes ? (
              <section className="spiritflix-smart-review__section">
                <h3>Scanner notes</h3>
                <p className="spiritflix-smart-review__notes">{analysis.notes}</p>
              </section>
            ) : null}

            {/* ── S6: Approved metadata section ─────────────────────── */}
            {hasReviewedMetadata ? (
              <>
                <section className="spiritflix-smart-review__section spiritflix-smart-review__section--approved">
                  <h3>Approved metadata</h3>
                  <dl className="spiritflix-smart-review__grid">
                    <div>
                      <dt>Display title</dt>
                      <dd>{analysis.reviewedMetadata!.editedDisplayTitle ?? analysis.suggestedDisplayTitle ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Filename suggestion</dt>
                      <dd className="is-mono">{analysis.reviewedMetadata!.editedFilenameSuggestion ?? analysis.suggestedFilename ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Category</dt>
                      <dd>{analysis.reviewedMetadata!.editedCategory ?? analysis.suggestedCategory ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>Collections</dt>
                      <dd>{(analysis.reviewedMetadata!.editedCollections ?? analysis.suggestedCollections)?.join(", ") || "—"}</dd>
                    </div>
                    <div>
                      <dt>Approved tags</dt>
                      <dd>
                        {analysis.reviewedMetadata!.approvedTagIds.length
                          ? analysis.reviewedMetadata!.approvedTagIds.join(", ")
                          : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt>Rejected tags</dt>
                      <dd>
                        {analysis.reviewedMetadata!.rejectedTagIds.length
                          ? analysis.reviewedMetadata!.rejectedTagIds.join(", ")
                          : "—"}
                      </dd>
                    </div>
                  </dl>
                </section>

                <section className="spiritflix-smart-review__section spiritflix-smart-review__section--actions">
                  <h3>S6 metadata actions</h3>
                  <p className="spiritflix-smart-review__boundary">S6 prepares metadata and rename preview only. It does not rename or move files.</p>
                  <div className="spiritflix-smart-review__action-buttons">
                    <button
                      className="spiritflix-smart-review__primary"
                      type="button"
                      disabled={exporting}
                      onClick={() => void runExportMetadata()}
                    >
                      {exporting ? "Exporting…" : "Export approved metadata"}
                    </button>
                    <button
                      className="spiritflix-smart-review__secondary"
                      type="button"
                      disabled={preparingRename}
                      onClick={() => void runPrepareRenamePreview()}
                    >
                      {preparingRename ? "Preparing…" : "Prepare rename preview"}
                    </button>
                  </div>
                </section>

                {/* Export result */}
                {exportResult ? (
                  <section className="spiritflix-smart-review__section spiritflix-smart-review__section--export-result">
                    <h3>Metadata exported</h3>
                    <dl className="spiritflix-smart-review__grid">
                      <div>
                        <dt>Title</dt>
                        <dd>{exportResult.displayTitle ?? "—"}</dd>
                      </div>
                      <div>
                        <dt>Category</dt>
                        <dd>{exportResult.category ?? "—"}</dd>
                      </div>
                      <div>
                        <dt>Tags</dt>
                        <dd>{exportResult.approvedTags.map((t) => t.label).join(", ") || "—"}</dd>
                      </div>
                      <div>
                        <dt>Path</dt>
                        <dd className="is-mono">{exportResult.sourcePath.split("/").slice(-2).join("/")}</dd>
                      </div>
                    </dl>
                  </section>
                ) : null}

                {/* Rename preview */}
                {renamePreview ? (
                  <section className="spiritflix-smart-review__section spiritflix-smart-review__section--rename-preview">
                    <h3>Rename preview</h3>
                    <dl className="spiritflix-smart-review__grid">
                      <div>
                        <dt>Current filename</dt>
                        <dd className="is-mono">{item.name}</dd>
                      </div>
                      <div>
                        <dt>Suggested filename</dt>
                        <dd className="is-mono">{renamePreview.suggestedName}</dd>
                      </div>
                      <div>
                        <dt>Target path</dt>
                        <dd className="is-mono">{renamePreview.targetPath.split("/").slice(-3).join("/")}</dd>
                      </div>
                      <div>
                        <dt>Warnings</dt>
                        <dd>
                          {renamePreview.warnings.length
                            ? renamePreview.warnings.map((w) => (
                                <p key={w} className="spiritflix-smart-review__warning">{w}</p>
                              ))
                            : "None"}
                        </dd>
                      </div>
                      <div>
                        <dt>Ready for Level 2</dt>
                        <dd>{renamePreview.readyForLevel2Preview ? "Yes" : "No"}</dd>
                      </div>
                    </dl>
                    <p className="spiritflix-smart-review__boundary">Execute rename comes in S7.</p>
                  </section>
                ) : null}
              </>
            ) : null}
          </>
        ) : null}

        <footer className="spiritflix-smart-review__footer">
          <button className="spiritflix-smart-review__primary" type="button" disabled={analyzing} onClick={() => void runAnalyze()}>
            {analyzing ? "Analyzing…" : analysis ? "Refresh suggestions" : "Analyze this video"}
          </button>
          {analysis ? (
            <>
              <button className="spiritflix-smart-review__primary" type="button" disabled={saving} onClick={() => void runSaveReview()}>
                {saving ? "Saving…" : "Save review"}
              </button>
              <button className="spiritflix-smart-review__secondary" type="button" disabled={marking} onClick={() => void runMarkReviewed()}>
                {marking ? "Saving…" : "Mark reviewed"}
              </button>
            </>
          ) : null}
          <button className="spiritflix-smart-review__secondary" type="button" onClick={onClose}>
            Close
          </button>
        </footer>
      </aside>
    </div>,
    document.body,
  );
}
