import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CodingCockpitShell from "@/components/coding/CodingCockpitShell";

describe("CodingCockpitShell", () => {
  it("renders a clean cockpit shell without diagnostic console clutter", () => {
    render(<CodingCockpitShell />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /advanced diagnostics/i })).toHaveAttribute(
      "href",
      "/proxy-backend",
    );
    expect(screen.getByText("Task Composer")).toBeInTheDocument();
    expect(screen.getByText("No active task")).toBeInTheDocument();
    expect(screen.getByText("Preview safely")).toBeDisabled();

    expect(screen.queryByText(/raw debug json/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/replayable logs/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/proxy safety smoke proposals/i)).not.toBeInTheDocument();
  });
});
