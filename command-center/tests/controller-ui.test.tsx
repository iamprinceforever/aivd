import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BASE, installController, json, refusingStatus, renderApp } from "./helpers";
import { RUN_CONFIRM } from "../src/pages/ExperimentControl";

describe("controller integration (mocked HTTP)", () => {
  it("shows 'Local runner not connected' and no invented values when offline", async () => {
    await renderApp("/control");
    expect(screen.getAllByText(/Local runner not connected/).length).toBeGreaterThan(0);
    const table = screen.getByRole("region", { name: "RC6 run gates" });
    expect(within(table).queryByText("PASS")).toBeNull();
    expect(within(table).getAllByText("NOT VERIFIED").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Run unavailable/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Reveal unavailable/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel run" })).toBeDisabled();
  });

  it("pairs with a one-time code; tokens never touch browser storage", async () => {
    installController();
    await renderApp("/settings", BASE);
    const user = userEvent.setup();
    await screen.findByText("FOUND, NOT PAIRED");
    await user.type(screen.getByLabelText(/One-time pairing code/), "WRONG");
    await user.click(screen.getByRole("button", { name: "Pair" }));
    expect((await screen.findAllByText(/Pairing refused/)).length).toBeGreaterThan(0);
    await user.type(screen.getByLabelText(/One-time pairing code/), "AB12-CD34-EF56");
    await user.click(screen.getByRole("button", { name: "Pair" }));
    expect(await screen.findByText("PAIRED")).toBeInTheDocument();
    expect(JSON.stringify({ ...localStorage })).not.toContain("sess");
    expect(JSON.stringify({ ...sessionStorage })).not.toContain("sess");
    expect(document.cookie).toBe("");
    expect(window.location.href).not.toContain("sess");
  });

  it("rejects non-loopback controller URLs", async () => {
    await renderApp("/settings", null);
    const user = userEvent.setup();
    const input = screen.getByLabelText(/Controller URL/);
    await user.clear(input);
    await user.type(input, "https://evil.example");
    await user.click(screen.getByRole("button", { name: "Set URL" }));
    expect(screen.getByText(/Only http:\/\/127\.0\.0\.1/)).toBeInTheDocument();
  });

  async function pairedAt(route: string, opts = {}) {
    const calls = installController(opts);
    await renderApp("/settings", BASE);
    const user = userEvent.setup();
    await screen.findByText("FOUND, NOT PAIRED");
    await user.type(screen.getByLabelText(/One-time pairing code/), "AB12-CD34-EF56");
    await user.click(screen.getByRole("button", { name: "Pair" }));
    await screen.findByText("PAIRED");
    await user.click(screen.getByRole("link", { name: new RegExp(route) }));
    return { calls, user };
  }

  it("renders every gate's PASS/FAIL with exact reasons and keeps run/reveal locked", async () => {
    await pairedAt("Experiment Control");
    const table = await screen.findByRole("region", { name: "RC6 run gates" });
    expect(await within(table).findAllByText("FAIL")).not.toHaveLength(0);
    expect(within(table).getAllByText("no APPROVED RC6_APPROVALS.json").length).toBe(2);
    expect(within(table).getByText(/AIVD_RC6_PARTB_AUTHORIZED not present/)).toBeInTheDocument();
    expect(within(table).getByText("MemAvailable 6640000 kB < 7600000 kB")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run unavailable/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Reveal unavailable/ })).toBeDisabled();
    expect(screen.getByText(/documents no cancel operation/)).toBeInTheDocument();
  });

  it("lifecycle shows seven separate states; independent validation is never asserted", async () => {
    await pairedAt("Research Integrity");
    const life = await screen.findAllByRole("list", { name: /lifecycle states/ });
    const items = Array.from(life[0].children) as HTMLElement[];
    expect(items).toHaveLength(7);
    expect(within(items[0]).getByText("PASS")).toBeInTheDocument();
    expect(within(items[3]).getByText("FAIL")).toBeInTheDocument();
    expect(within(items[6]).getByText("NOT VERIFIED")).toBeInTheDocument();
    expect(screen.queryByText(/experiment ready/i)).toBeNull();
  });

  it("even with all gates PASS the UI requires model, attempt and the exact phrase; server refusal is shown", async () => {
    const st = refusingStatus();
    st.ops.rc6_run = { available: true, gates: st.ops.rc6_run.gates.map((g) => ({ ...g, state: "PASS" as const, reasons: [] })) };
    let opBody: string | undefined;
    const { user } = await pairedAt("Experiment Control", {
      status: st,
      onOp: (_u: string, init?: RequestInit) => {
        opBody = String(init?.body);
        expect((init?.headers as Record<string, string>)["X-AIVD-CSRF"]).toBe("csrf-tok");
        return json({ status: "REFUSED", gates: [] }, 403);
      },
    });
    const btn = await screen.findByRole("button", { name: "Request guarded run" });
    expect(btn).toBeDisabled();
    await user.selectOptions(screen.getByRole("combobox", { name: "Preregistered model" }), "qwen3:8b");
    await user.type(screen.getByRole("textbox", { name: "Attempt id" }), "a1");
    expect(btn).toBeDisabled();
    await user.type(screen.getByRole("textbox", { name: /Type the confirmation phrase exactly: I AM THE AUTHORIZED OPERATOR AND AUTHORIZE THIS RC6 RUN/ }), RUN_CONFIRM);
    expect(btn).toBeEnabled();
    await user.click(btn);
    expect(await screen.findByText(/HTTP 403 REFUSED/)).toBeInTheDocument();
    expect(JSON.parse(opBody!)).toEqual({ model_id: "qwen3:8b", attempt_id: "a1", confirm: RUN_CONFIRM });
  });

  it("models & runtime show live memory gate and never claim Ollama was started", async () => {
    await pairedAt("Models & Runtime");
    expect(await screen.findByText("MemAvailable 6640000 kB < 7600000 kB")).toBeInTheDocument();
    expect(screen.getByText(/Ollama process running/)).toHaveTextContent("no");
  });
});
