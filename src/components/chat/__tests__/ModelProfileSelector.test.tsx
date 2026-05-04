import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";

describe("ModelProfileSelector", () => {
  it("renders all profile options", () => {
    const onChange = vi.fn();
    render(
      <ModelProfileSelector
        value="normal-peer"
        onChange={onChange}
      />,
    );
    const sel = screen.getByLabelText(/model profile/i);
    const opts = Array.from(
      (sel as HTMLSelectElement).querySelectorAll("option"),
    ).map((o) => ({ value: o.value, text: o.textContent?.trim() }));
    expect(opts[0]?.value).toBe("normal-peer");
    expect(opts[0]?.text).toBe("Peer");
  });

  it("calls onChange when selection changes", () => {
    const onChange = vi.fn();
    render(
      <ModelProfileSelector
        value="normal-peer"
        onChange={onChange}
      />,
    );
    const sel = screen.getByLabelText(/model profile/i);
    fireEvent.change(sel, { target: { value: "teacher" } });
    expect(onChange).toHaveBeenCalledWith("teacher");
  });

  it("topBar keeps Mode screen-reader only (compact bar)", () => {
    const { container } = render(
      <ModelProfileSelector
        variant="topBar"
        value="normal-peer"
        onChange={vi.fn()}
        compact
      />,
    );
    const sr = container.querySelector(".sr-only");
    expect(sr?.textContent?.trim()).toBe("Mode");
    const sel = screen.getByLabelText(/model profile/i);
    expect(sel.className).toMatch(/max-w-\[130px\]/);
  });
});
