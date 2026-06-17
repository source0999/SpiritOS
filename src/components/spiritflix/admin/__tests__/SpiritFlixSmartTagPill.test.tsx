import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { SpiritFlixSmartTag } from "@/lib/spiritflix/admin/smart";
import { SpiritFlixSmartTagPill } from "../SpiritFlixSmartTagPill";

const tag: SpiritFlixSmartTag = {
  id: "full-hd",
  label: "full HD",
  group: "quality",
  confidence: 0.82,
  evidenceTimestamps: [],
  reviewRequired: true,
};

describe("SpiritFlixSmartTagPill", () => {
  it("shows label, confidence, and reviewRequired marker", () => {
    render(<SpiritFlixSmartTagPill tag={tag} />);
    expect(screen.getByText("full HD")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("review")).toBeInTheDocument();
  });
});
