"use client";

import type { SpiritFlixSmartTag } from "@/lib/spiritflix/admin/smart/types";

export type SpiritFlixSmartTagReviewState = "approved" | "rejected" | "pending";

interface SpiritFlixSmartTagPillProps {
  tag: SpiritFlixSmartTag;
  reviewState?: SpiritFlixSmartTagReviewState;
  onApprove?: () => void;
  onReject?: () => void;
  onReset?: () => void;
}

export function SpiritFlixSmartTagPill({ tag, reviewState = "pending", onApprove, onReject, onReset }: SpiritFlixSmartTagPillProps) {
  const confidencePct = Math.round(tag.confidence * 100);
  const interactive = Boolean(onApprove || onReject || onReset);

  return (
    <div
      className={`spiritflix-smart-tag-pill-wrap is-${reviewState}${interactive ? " is-interactive" : ""}`}
      data-review-state={reviewState}
    >
      <span
        className={`spiritflix-smart-tag-pill is-group-${tag.group}${tag.reviewRequired ? " is-review-required" : ""}`}
        title={`${tag.group} · ${confidencePct}% confidence${tag.reviewRequired ? " · review required" : ""}`}
      >
        <span className="spiritflix-smart-tag-pill__label">{tag.label}</span>
        <span className="spiritflix-smart-tag-pill__meta">{confidencePct}%</span>
        {tag.reviewRequired ? <span className="spiritflix-smart-tag-pill__flag">review</span> : null}
      </span>
      {interactive ? (
        <div className="spiritflix-smart-tag-pill__actions">
          <button type="button" aria-label={`Approve ${tag.label}`} onClick={onApprove}>
            Approve
          </button>
          <button type="button" aria-label={`Reject ${tag.label}`} onClick={onReject}>
            Reject
          </button>
          <button type="button" aria-label={`Reset ${tag.label}`} onClick={onReset}>
            Reset
          </button>
        </div>
      ) : null}
    </div>
  );
}
