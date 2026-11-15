import { test, expect } from "@playwright/test";

test("research journey: search, comparison, review, controls, branch and export", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Look beyond/ }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search the evidence library" })
    .fill("notarecord");
  await expect(
    page.getByRole("heading", { name: "No records match these filters" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("checkbox", { name: "Compare" }).nth(0).check();
  await page.getByRole("checkbox", { name: "Compare" }).nth(1).check();
  await page.getByRole("link", { name: "Compare records" }).click();
  await expect(
    page.getByRole("heading", { name: "Compare the conditions" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Build scenario with these sources" })
    .click();
  await page.getByLabel("Scenario name").fill("Browser acceptance run");
  await page.getByLabel("Initial event schedule").selectOption("stop");
  await page
    .getByRole("button", { name: "Retrieve evidence & review plan" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review your observation plan" }),
  ).toBeFocused();
  await page.getByRole("checkbox", { name: /I reviewed/ }).check();
  await page.getByRole("button", { name: "Approve plan & open lab" }).click();
  await expect(
    page.getByRole("heading", { name: "Browser acceptance run" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Browser acceptance run" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "16×", exact: true }).click();
  await page.getByRole("button", { name: "Start run" }).click();
  await expect(
    page.getByRole("button", { name: "Pause", exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(2200);
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await page.getByRole("button", { name: "Inspect decision" }).click();
  await expect(
    page.getByRole("dialog", { name: "Decision trace" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.locator("summary").click();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("button", { name: "New branch" }).click();
  await expect(
    page.getByRole("dialog", { name: "Create an independent branch" }),
  ).toBeVisible();
  await page.getByLabel("Branch name").fill("Browser acceptance branch");
  await page.getByLabel("Branch at virtual second").fill("19");
  await page
    .getByRole("button", { name: "Create branch", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Browser acceptance branch" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Stop source/ }).click();
  await page.getByRole("button", { name: "Apply to next sample" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export run" }).click();
  expect((await download).suggestedFilename()).toMatch(/run_.*\.json/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Browser acceptance branch" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset view" }).click();
  await page.getByRole("button", { name: "Inject sensor fault" }).click();
  await page.getByRole("button", { name: "Apply to next sample" }).click();
  await page.getByRole("link", { name: /Run archive/ }).click();
  await expect(
    page
      .getByRole("link", { name: "Browser acceptance branch", exact: true })
      .first(),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

for (const width of [320, 390, 768, 1440]) {
  test(`library and lab fit ${width}px in both themes`, async ({ page }) => {
    await page.setViewportSize({ width, height: 950 });
    await page.goto("/");
    await page
      .getByRole("button", {
        name: "Flame Extinguishment Experiment",
        exact: true,
      })
      .click();
    await expect(page.getByRole("dialog", { name: "FLEX" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", {
        name: "Flame Extinguishment Experiment",
        exact: true,
      }),
    ).toBeFocused();
    for (const theme of ["light", "dark"]) {
      if (theme === "dark")
        await page
          .getByRole("button", { name: "Switch to dark theme" })
          .click();
      await expect(
        page.getByRole("heading", { name: /Look beyond/ }),
      ).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBeTruthy();
      await page.screenshot({
        path: `../work/library-${width}-${theme}.png`,
        fullPage: true,
      });
    }
    await page
      .getByRole("link", { name: "Simulation lab", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "What do the signals show?" }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({ path: `../work/lab-${width}.png`, fullPage: true });
  });
}

test("keyboard skip link, search, modal focus and reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await page
    .getByRole("button", {
      name: "Flame Extinguishment Experiment",
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog", { name: "FLEX" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", {
      name: "Flame Extinguishment Experiment",
      exact: true,
    }),
  ).toBeFocused();
  expect(
    await page.evaluate(
      () =>
        getComputedStyle(document.querySelector("button")!).transitionDuration,
    ),
  ).toBe("0s");
});

test("each preset reaches an independently computed state", async ({
  page,
  request,
}) => {
  const runs: { id: string; expected: string }[] = [];
  for (const [preset, expected] of [
    ["reduce", "Danger"],
    ["stop", "Verified"],
    ["data-loss", "Uncertain"],
  ]) {
    const scenario = await (
      await request.post("/api/v1/scenarios", {
        data: {
          name: "Browser preset " + preset,
          question: "Which observations remain after this source intervention?",
          investigation_ids: ["flex", "synthetic-v1"],
        },
      })
    ).json();
    await request.post(`/api/v1/scenarios/${scenario.id}/evidence`, {
      data: { version: 1 },
    });
    const plan = await (
      await request.post(`/api/v1/scenarios/${scenario.id}/plans`, {
        data: { version: 1 },
      })
    ).json();
    await request.post(`/api/v1/plans/${plan.id}/approve`, { data: {} });
    const run = await (
      await request.post("/api/v1/runs", {
        data: { plan_ref: plan.id, preset, name: "Browser preset " + preset },
      })
    ).json();
    runs.push({ id: run.id, expected });
    await request.post(`/api/v1/runs/${run.id}/commands`, {
      data: { command: "speed", speed: 16, command_id: "preset-speed" },
    });
    await request.post(`/api/v1/runs/${run.id}/commands`, {
      data: { command: "start", command_id: "preset-start" },
    });
  }
  for (const run of runs) {
    await expect
      .poll(
        async () =>
          (await (await request.get("/api/v1/runs/" + run.id)).json()).status,
        { timeout: 25000 },
      )
      .toBe("completed");
    await page.goto("/lab/" + run.id);
    await expect(
      page.getByRole("heading", { name: run.expected, exact: true }),
    ).toBeVisible();
    if (run.expected === "Verified")
      await expect(
        page.getByText("Verified within simulated conditions", { exact: true }),
      ).toBeVisible();
  }
});

test("filters, source review, limit notice and network recovery", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("combobox", { name: "Filter by research family" })
    .selectOption("Gas monitoring");
  await expect(
    page.getByRole("button", {
      name: "The Combustion Product Monitor",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Flame Extinguishment Experiment",
      exact: true,
    }),
  ).not.toBeVisible();
  await page
    .getByRole("combobox", { name: "Filter by research family" })
    .selectOption("");
  for (let i = 0; i < 4; i++)
    await page.getByRole("checkbox", { name: "Compare" }).nth(i).click();
  await expect(
    page.getByText(
      "Compare up to three records. Remove one before adding another.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear selection" }).click();
  await page
    .getByRole("button", {
      name: "Flame Extinguishment Experiment",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("link", { name: "Open source record" }),
  ).toHaveAttribute(
    "href",
    "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69",
  );
  await page.keyboard.press("Escape");
  await page.route("**/api/v1/investigations?*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Research index is temporarily unavailable. Retry the request.",
      }),
    }),
  );
  await page
    .getByRole("textbox", { name: "Search the evidence library" })
    .fill("thermal");
  await expect(page.getByRole("alert")).toContainText(
    "Research index is temporarily unavailable",
  );
  await page.unroute("**/api/v1/investigations?*");
  await page.getByRole("button", { name: "Retry request" }).click();
  await expect(page.getByRole("alert")).not.toBeVisible();
});
