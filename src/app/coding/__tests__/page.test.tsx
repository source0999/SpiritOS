import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import CodingPage from "@/app/coding/page";

const navMock = vi.hoisted(() => ({ path: "/coding" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navMock.path,
}));

describe("CodingPage", () => {
  it("renders the Source Proxy cockpit shell for /coding", () => {
    render(<CodingPage />);

    expect(screen.getByRole("heading", { level: 1, name: "Coding" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Spirit app desktop navigation" }))
      .toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Task Composer" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Review pane" })).toBeInTheDocument();
    expect(screen.getByText("Preview safely")).toBeInTheDocument();
  });
});
