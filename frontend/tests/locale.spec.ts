import { test, expect } from '@playwright/test';

test('language changes preserve form input and survive reload', async ({page}) => {
  await page.goto('/scenario');
  await page.getByLabel('Scenario name', {exact:true}).fill('My unchanged study');
  await page.getByLabel('Language / اللغة', {exact:true}).selectOption('ar');
  await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  await expect(page.getByRole('heading', {name:'ابدأ بسؤال'})).toBeVisible();
  await expect(page.getByLabel('اسم السيناريو', {exact:true})).toHaveValue('My unchanged study');
  await page.reload();
  await expect(page.getByRole('heading', {name:'ابدأ بسؤال'})).toBeVisible();
  await page.getByLabel('Language / اللغة', {exact:true}).selectOption('en');
  await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  await expect(page.getByRole('heading', {name:'Start with a question'})).toBeVisible();
});

for (const width of [320, 390, 1440]) {
  test(`Arabic routes and NASA measurements fit ${width}px`, async ({page}) => {
    await page.setViewportSize({width,height:950});
    await page.goto('/');
    await page.getByLabel('Language / اللغة', {exact:true}).selectOption('ar');
    for (const path of ['/', '/scenario', '/lab', '/archive', '/datasets']) {
      await page.goto(path);
      await expect(page.getByLabel('Language / اللغة', {exact:true})).toHaveValue('ar');
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
    }
    await page.getByRole('button',{name:'تحميل قياسات NASA FLEX-007',exact:true}).click();
    await expect(page.getByRole('combobox',{name:'قناة القياس',exact:true})).toBeVisible();
    await page.getByRole('combobox',{name:'قناة القياس',exact:true}).selectOption('zeroed_droplet_x');
    await expect(page.getByText('لم تُنشر قيم رقمية لهذه القناة. تبقى جميع قيمها مفقودة.')).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
    await page.screenshot({path:`../work/arabic-datasets-${width}.png`,fullPage:true});
    if (width === 1440) {
      await page.getByRole('combobox',{name:'قناة القياس',exact:true}).selectOption('droplet_diameter');
      await page.getByRole('heading',{name:'الأرصاد المسجلة',exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:'../work/bilingual-preview.png'});
    }
  });
}
