"use client";

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { FolderSearch, X } from "lucide-react";
import type { SpiritFlixSmartBatchPreview } from "@/lib/spiritflix/admin/smart";

interface SpiritFlixSmartBatchPanelProps {
  currentPath: string;
  open: boolean;
  onClose: () => void;
}

interface BatchResponse extends SpiritFlixSmartBatchPreview {
  error?: string;
}

function statusLabel(status: string): string {
  if (status === "already_current") return "current";
  return status.replace(/_/g, " ");
}

export function SpiritFlixSmartBatchPanel({ currentPath, open, onClose }: SpiritFlixSmartBatchPanelProps) {
  const [result, setResult] = useState<SpiritFlixSmartBatchPreview | null>(null);
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
          S7 writes analysis sidecars only. It does not rename, move, or auto-approve files.
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
