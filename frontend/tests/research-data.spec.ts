import {test,expect} from '@playwright/test';

for(const language of ['en','ar']) test(`native research library, paging and agent attachment (${language})`,async({page,request})=>{
  const ar=language==='ar';
  const datasets=await (await request.get('/api/v1/datasets')).json();
  const dataset=datasets.items.find((d:any)=>d.manifest.source_file==='19056A2_data.csv');
  expect(dataset).toBeTruthy();
  await page.goto('/research-files');
  await page.getByLabel('Language / اللغة',{exact:true}).selectOption(language);
  await page.getByLabel(ar?'البحث باسم الملف أو معرف الدراسة':'Search filenames or study IDs',{exact:true}).fill('19056A2');
  await expect(page.getByRole('heading',{name:'19056A2_data.csv',exact:true})).toBeVisible();
  const study=page.locator('article').filter({has:page.locator(`a[href="/datasets?dataset=${dataset.id}"]`)});
  await study.getByRole('link',{name:ar?'مراجعة بواسطة إيجنت':'Review with an agent',exact:true}).click();
  await expect(page.locator('select[name="dataset_id"]')).toHaveValue(dataset.id);
  await expect(page.getByRole('combobox',{name:ar?'دور الإيجنت':'Agent role',exact:true})).toHaveValue('dataset_review');
  await expect(page.locator('.agent-form input[type="checkbox"]')).toHaveCount(0);
  await page.goto('/datasets?dataset='+dataset.id);
  await page.getByRole('combobox',{name:ar?'قناة القياس':'Measurement channel',exact:true}).selectOption('MFCA1StaticMixerFlow');
  await expect(page.locator('.measurement-viewer tbody tr')).toHaveCount(25);
  await expect(page.locator('.measurement-viewer').getByText(/31,316|٣١٬٣١٦/).first()).toBeVisible();
  const expected=await (await request.get(`/api/v1/datasets/${dataset.id}?channel=MFCA1StaticMixerFlow&offset=25&limit=25`)).json();
  await page.getByRole('button',{name:ar?'الأرصاد التالية':'Next observations',exact:true}).click();
  await expect(page.locator('.measurement-viewer tbody tr').first()).toContainText(expected.items[0].source_timestamp);
  await expect(page.locator('.measurement-viewer tbody tr').first()).toContainText(ar?'وحدة غير موثقة':'unit_unresolved');
  for(const width of [320,390,1440]){
    await page.setViewportSize({width,height:1000});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  }
  await page.getByRole('heading',{name:ar?'الأرصاد المسجلة':'Recorded observations',exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:`../work/native-research-${language}.png`});
});
