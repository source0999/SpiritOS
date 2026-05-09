import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ResearchPlanPanel } from "@/components/chat/ResearchPlanPanel";
import { draftResearchPlanFromPrompt } from "@/lib/spirit/research-plan";

describe("ResearchPlanPanel", () => {
  it("renders editable steps and no CoT copy", () => {
    const plan = draftResearchPlanFromPrompt("Why is the sky blue?");
    render(
      <ResearchPlanPanel
        open
        plan={plan}
        onClose={() => {}}
        onPlanChange={() => {}}
        onStartResearch={() => {}}
      />,
    );
    expect(screen.getByTestId("research-plan-panel")).toBeInTheDocument();
    expect(screen.getByTestId("research-plan-no-cot")).toHaveTextContent(/No private chain-of-thought/i);
    expect(screen.getAllByLabelText("Step label").length).toBeGreaterThan(0);
  });

  it("Start research invokes handler", () => {
    const plan = draftResearchPlanFromPrompt("x");
    const onStart = vi.fn();
    render(
      <ResearchPlanPanel
        open
        plan={plan}
        onClose={() => {}}
        onPlanChange={() => {}}
        onStartResearch={onStart}
      />,
    );
    fireEvent.click(screen.getByTestId("research-plan-start"));
    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({ id: plan.id }));
  });

  it("Cancel calls onClose", () => {
    const onClose = vi.fn();
    const plan = draftResearchPlanFromPrompt("x");
    render(
      <ResearchPlanPanel
        open
        plan={plan}
        onClose={onClose}
        onPlanChange={() => {}}
        onStartResearch={() => {}}
      />,
    );
    fireEvent.click(screen.getByTestId("research-plan-cancel"));
    expect(onClose).toHaveBeenCalled();
  });
});
