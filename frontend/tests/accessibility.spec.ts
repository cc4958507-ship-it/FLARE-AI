import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
for (const language of ['en','ar']) for (const theme of ["light", "dark"]) {
  test(`automated accessibility checks across primary screens (${language}, ${theme})`, async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByLabel('Language / اللغة', {exact:true}).selectOption(language);
    for (const path of ["/", "/scenario", "/lab", "/archive", "/datasets", "/agents", "/research-files"]) {
      await page.goto(path);
      await page.waitForTimeout(350);
      if (
        theme === "dark" &&
        (await page
          .getByRole("button", { name: language === 'ar' ? 'التبديل إلى الوضع الداكن' : "Switch to dark theme" })
          .count())
      )
        await page
          .getByRole("button", { name: language === 'ar' ? 'التبديل إلى الوضع الداكن' : "Switch to dark theme" })
          .click();
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze();
      expect(
        results.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.map((n) => n.target),
        })),
      ).toEqual([]);
    }
  });
}
