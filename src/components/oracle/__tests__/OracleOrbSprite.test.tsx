import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OracleOrbSprite } from "@/components/oracle/OracleOrbSprite";

describe("OracleOrbSprite", () => {
  it("renders svg and no external images", () => {
    render(<OracleOrbSprite variant="widget" visualState="idle" />);
    const root = screen.getByTestId("oracle-orb-sprite");
    expect(root.querySelector("svg")).not.toBeNull();
    expect(root.querySelector("img")).toBeNull();
  });
});
