import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Clock } from "../Clock";

describe("Clock", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("renders current time in HH:MM:SS format", () => {
    render(<Clock />);

    const timeElement = screen.getByText(/\d{2}:\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
    expect(timeElement).toHaveClass("font-mono");
  });
});
