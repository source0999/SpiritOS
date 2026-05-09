import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SpiritWorkflowVisualizer } from "@/components/chat/SpiritWorkflowVisualizer";

const idleSteps = [
  { id: "1", label: "Understanding request", status: "done" as const },
  { id: "2", label: "Complete", status: "done" as const },
];

describe("SpiritWorkflowVisualizer", () => {
  it("returns null when not visible (idle simple Peer hides rail)", () => {
    const { container } = render(
      <SpiritWorkflowVisualizer visible={false} busy={false} steps={idleSteps} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders when busy", () => {
    render(
      <SpiritWorkflowVisualizer
        visible
        busy
        lane="local-chat"
        steps={[
          { id: "1", label: "Understanding request", status: "done" },
          { id: "2", label: "Drafting answer", status: "active" },
        ]}
      />,
    );
    expect(screen.getByTestId("spirit-workflow-visualizer")).toBeInTheDocument();
    expect(screen.getByText(/Spirit is working/i)).toBeInTheDocument();
  });

  it("shows search proof line when used", () => {
    render(
      <SpiritWorkflowVisualizer
        visible
        busy={false}
        lane="openai-web-search"
        searchStatus="used"
        searchUsed
        sourceCount={6}
        provider="openai"
        steps={idleSteps}
      />,
    );
    expect(screen.getByTestId("spirit-workflow-route-line")).toHaveTextContent("OpenAI web search");
    const proof = screen.getByTestId("spirit-workflow-search-proof");
    expect(proof).toHaveTextContent("Search: used");
    expect(proof).toHaveTextContent("Sources: 6");
  });

  it("shows no chain-of-thought disclaimer", () => {
    render(<SpiritWorkflowVisualizer visible busy lane="local-chat" steps={idleSteps} />);
    expect(screen.getByTestId("spirit-workflow-no-cot")).toHaveTextContent(
      /No private chain-of-thought/i,
    );
  });

  it("renders real source links only when url exists", () => {
    render(
      <SpiritWorkflowVisualizer
        visible
        busy={false}
        lane="openai-web-search"
        steps={idleSteps}
        sources={[
          { title: "Example", url: "https://example.com/a", snippet: "A bit of text" },
          { title: "No URL card", url: "" },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: /Example/i });
    expect(link).toHaveAttribute("href", "https://example.com/a");
    expect(link).toHaveAttribute("target", "_blank");
    expect(screen.getByText(/No URL - not clickable/i)).toBeInTheDocument();
  });

  it("compact mode shows summary line", () => {
    const onExpand = vi.fn();
    render(
      <SpiritWorkflowVisualizer
        visible
        compact
        busy={false}
        completedSummary="Search complete - 4 sources"
        onExpand={onExpand}
        lane="openai-web-search"
        steps={idleSteps}
      />,
    );
    expect(screen.getByTestId("spirit-workflow-visualizer-compact")).toBeInTheDocument();
    expect(screen.getByTestId("spirit-workflow-compact-summary")).toHaveTextContent(
      "Search complete - 4 sources",
    );
    fireEvent.click(screen.getByTestId("spirit-workflow-expand"));
    expect(onExpand).toHaveBeenCalled();
  });

  it("shows failed search proof without leaking long reasons", () => {
    render(
      <SpiritWorkflowVisualizer
        visible
        busy={false}
        lane="openai-web-search"
        searchStatus="failed"
        skipReason="missing_openai_key"
        provider="openai"
        steps={idleSteps}
      />,
    );
    expect(screen.getByTestId("spirit-workflow-search-proof")).toHaveTextContent(/missing API key/i);
  });

  it("calls onDismiss when dismiss clicked", () => {
    const onDismiss = vi.fn();
    render(
      <SpiritWorkflowVisualizer visible busy steps={idleSteps} onDismiss={onDismiss} />,
    );
    fireEvent.click(screen.getByTestId("spirit-workflow-dismiss"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
