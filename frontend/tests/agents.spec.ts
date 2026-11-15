import {test,expect} from '@playwright/test';

for (const language of ['en','ar']) test(`saved agent task and offline worker (${language})`,async({page,request})=>{
  // The private test server/worker have no provider key. Enable only the form for this integration test.
  const health = await (await request.get('/api/v1/health')).json();
  expect(health.model_mode).toBe('offline');
  await page.route('**/api/v1/agents', async route=>{
    const response = await route.fetch();
    await route.fulfill({response,json:{...await response.json(),enabled:true}});
  });
  await page.goto('/agents');
  await page.getByLabel('Language / اللغة',{exact:true}).selectOption(language);
  const ar = language==='ar';
  const question = `Agent browser acceptance ${language} ${Date.now()}`;
  await page.getByLabel(ar?'السؤال البحثي':'Research question',{exact:true}).fill(question);
  await page.getByRole('button',{name:ar?'إضافة إلى الطابور':'Queue task',exact:true}).click();
  await expect(page.getByRole('heading',{name:question,exact:true})).toBeVisible();
  await expect(page.getByText('AI_NOT_CONFIGURED',{exact:true})).toBeVisible({timeout:15000});
  await page.reload();
  await page.getByRole('heading',{name:question,exact:true}).locator('..').getByRole('button').click();
  await expect(page.getByText('AI_NOT_CONFIGURED',{exact:true})).toBeVisible();
  for (const width of [320,1440]) {
    await page.setViewportSize({width,height:950});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
    await page.screenshot({path:`../work/agents-${language}-${width}.png`,fullPage:true});
  }
});
