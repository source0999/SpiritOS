import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageMarkdown } from "@/components/chat/MessageMarkdown";

describe("MessageMarkdown", () => {
  it("renders bullet list", () => {
    render(<MessageMarkdown text={"- one\n- two"} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("one");
  });

  it("renders inline code", () => {
    render(<MessageMarkdown text="Use `foo` here." />);
    expect(screen.getByText("foo")).toBeInTheDocument();
  });

  it("renders fenced code block", () => {
    const md = "```ts\nconst x = 1\n```";
    render(<MessageMarkdown text={md} />);
    expect(screen.getByText("const x = 1")).toBeInTheDocument();
  });

  it("hydrates degenerate Sources from webSourcesSnapshot", () => {
    const text = "## Sources\n\n1. 1\n2. 2\n";
    const snap = {
      provider: "openai",
      count: 1,
      sources: [{ title: "NIH", url: "https://www.nih.gov/a" }],
    };
    render(<MessageMarkdown text={text} webSourcesSnapshot={snap} />);
    const link = screen.getByRole("link", { name: /NIH/i });
    expect(link).toHaveAttribute("href", "https://www.nih.gov/a");
  });
});
