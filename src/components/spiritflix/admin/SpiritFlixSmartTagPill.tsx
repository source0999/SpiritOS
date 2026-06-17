"use client";

import type { SpiritFlixSmartTag } from "@/lib/spiritflix/admin/smart";

interface SpiritFlixSmartTagPillProps {
  tag: SpiritFlixSmartTag;
}

export function SpiritFlixSmartTagPill({ tag }: SpiritFlixSmartTagPillProps) {
  const confidencePct = Math.round(tag.confidence * 100);
  return (
    <span
      className={`spiritflix-smart-tag-pill is-group-${tag.group}${tag.reviewRequired ? " is-review-required" : ""}`}
      title={`${tag.group} · ${confidencePct}% confidence${tag.reviewRequired ? " · review required" : ""}`}
    >
      <span className="spiritflix-smart-tag-pill__label">{tag.label}</span>
      <span className="spiritflix-smart-tag-pill__meta">{confidencePct}%</span>
      {tag.reviewRequired ? <span className="spiritflix-smart-tag-pill__flag">review</span> : null}
    </span>
  );
}
