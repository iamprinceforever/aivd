import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp } from "./helpers";

describe("Interview Demo page", () => {
  it("labels itself as DEMO and keeps Run demo disabled without a controller", async () => {
    await renderApp("/demo", null);
    expect(screen.getAllByText(/DEMO – not a research result/).length).toBeGreaterThan(0);
    const btn = await screen.findByRole("button", { name: /Run demo/i });
    expect(btn).toBeDisabled();
    expect(screen.getByText(/Open this page from the controller/i)).toBeInTheDocument();
  });
});
