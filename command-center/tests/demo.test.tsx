import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderApp } from "./helpers";

const walkManifest = {
  label: "DEMO – not a research result",
  title: "Sample run walkthrough",
  note: "DEMO screenshots only.",
  steps: [
    {
      id: "idle",
      title: "Idle Demo page",
      caption: "Controller not required for the static walkthrough.",
      image: "01-idle.png",
    },
    {
      id: "running",
      title: "Run in progress",
      caption: "Models scan one target at a time.",
      image: "02-running.png",
    },
  ],
};

describe("Interview Demo page", () => {
  beforeEach(() => {
    const orig = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("demo/walkthrough/manifest.json")) {
          return new Response(JSON.stringify(walkManifest), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return orig(input, init);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("labels itself as DEMO and keeps Run demo disabled without a controller", async () => {
    await renderApp("/demo", null);
    expect(screen.getAllByText(/DEMO – not a research result/).length).toBeGreaterThan(0);
    const btn = await screen.findByRole("button", { name: /Run demo/i });
    expect(btn).toBeDisabled();
    expect(screen.getByText(/Open this page from the controller/i)).toBeInTheDocument();
  });

  it("renders the sample-run walkthrough carousel with prev/next", async () => {
    await renderApp("/demo", null);
    const region = await screen.findByRole("region", { name: /Sample run walkthrough/i });
    expect(region).toBeInTheDocument();
    expect(await screen.findByText(/Idle Demo page/i)).toBeInTheDocument();
    const next = screen.getByRole("button", { name: /Next step/i });
    fireEvent.click(next);
    expect(await screen.findByText(/Run in progress/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Previous step/i }));
    expect(await screen.findByText(/Idle Demo page/i)).toBeInTheDocument();
  });
});
