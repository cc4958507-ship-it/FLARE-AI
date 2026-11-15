import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {api} from './api';
import {useLanguage,t} from './i18n';
import {datasetLabel} from './presentation';

type Asset={id:string;name:string;aliases:string[];bytes:number;category:string;study_id:string|null;source_url:string;review_status:string};
type Dataset={id:string;manifest:{title:string;source_asset_id?:string};report:{observation_rows?:number;accepted_rows:number;channels?:{channel:string}[]}};
export default function ResearchLibrary(){
  const language=useLanguage();const l=(en:string,ar:string)=>language==='ar'?ar:en;
  const [query,setQuery]=useState('');const [category,setCategory]=useState('');
  const assets=useQuery({queryKey:['research-files',query,category],queryFn:()=>api<{items:Asset[];total:number;categories:string[]}>(`/research-files?q=${encodeURIComponent(query)}${category?'&category='+encodeURIComponent(category):''}`)});
  const datasets=useQuery({queryKey:['datasets'],queryFn:()=>api<{items:Dataset[]}>('/datasets')});
  const categories:Record<string,string>={experimental_raw:l('Experimental records','سجلات تجريبية'),mixed_experiment_and_model:l('Mixed experiment / model tables','جداول مختلطة: تجربة ومحاكاة'),command_setpoints:l('Command setpoints','قيم ضبط الأوامر'),study_metadata:l('Study metadata','بيانات وصفية للدراسات'),paper_archive:l('Research papers','أوراق بحثية'),image_archive:l('Image archives','أرشيفات الصور'),settings_archive:l('Settings archives','أرشيفات الإعدادات'),reference_document:l('Reference documents','وثائق مرجعية'),video:l('Video','فيديو'),context_image:l('Context images','صور مساندة'),settings_and_timing:l('Settings and timing','إعدادات وتوقيت')};
  return <div className="measurement-imports research-library">
    <h1 tabIndex={-1}>{l('Research files','ملفات البحث')}</h1>
    <p className="workflow-hint">{l('Choose a dataset → inspect its channels → review it with an agent. Original files stay available below.','اختر مجموعة بيانات ← استعرض قنواتها ← راجعها بإيجنت. الملفات الأصلية متاحة أسفل الصفحة.')}</p>
    <p>{l('Original supplied sources and imported experimental records. Files with identical content share one stored copy. Calibration and repository attribution remain unverified.','المصادر الأصلية المرفقة والسجلات التجريبية المستوردة. تُحفظ نسخة واحدة للمحتوى المتطابق. تبقى المعايرة ونسبة الملفات إلى المستودع غير متحقق منهما.')}</p>
    <section className="panel" aria-labelledby="research-datasets-heading"><h2 id="research-datasets-heading">{l('Datasets ready to inspect','مجموعات جاهزة للفحص')}</h2>
      {datasets.isPending&&<p role="status">{t('Loading datasets…')}</p>}
      {datasets.isError&&<p role="alert">{t('Could not load datasets. ')}<button className="button" onClick={()=>datasets.refetch()}>{t('Retry')}</button></p>}
      {datasets.data?.items.filter(d=>d.manifest.source_asset_id).map(d=><article key={d.id}><h3>{datasetLabel(d.manifest.title,language)}</h3><p>{d.report.observation_rows?.toLocaleString(language)} {l('source records','سجلًا أصليًا')} · {d.report.channels?.length} {l('channels','قناة')} · {l('Replay Only; calibration unverified','للاستعراض فقط؛ المعايرة غير متحقق منها')}</p><div className="research-actions"><Link className="button primary" to={'/datasets?dataset='+d.id}>{t('Inspect measurements')}</Link><Link className="button" to={'/agents?dataset='+d.id}>{l('Review with an agent','مراجعة بواسطة إيجنت')}</Link></div></article>)}
      {datasets.data&&!datasets.data.items.some(d=>d.manifest.source_asset_id)&&<p>{l('No native research records imported yet.','لم تُستورد سجلات البحث بصيغتها الأصلية بعد.')}</p>}
    </section>
    <section className="panel" aria-labelledby="research-sources-heading"><h2 id="research-sources-heading">{l('Original source library','مكتبة المصادر الأصلية')}</h2>
      <p>{l('Mixed experimental and simulated tables are retained as source files; they are not merged into measured channels. Image and video archives require source-specific analysis before they become physical measurements.','تُحفظ الجداول التي تجمع التجربة والمحاكاة كمصادر منفصلة ولا تُدمج في قنوات القياس. تحتاج أرشيفات الصور والفيديو إلى تحليل خاص بالمصدر قبل تحويلها إلى قياسات فيزيائية.')}</p>
      <div className="research-filters"><label>{l('Search filenames or study IDs','البحث باسم الملف أو معرف الدراسة')}<input type="search" value={query} onChange={e=>setQuery(e.target.value)} maxLength={300}/></label><label>{l('File category','فئة الملف')}<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">{l('All categories','كل الفئات')}</option>{assets.data?.categories.map(c=><option value={c} key={c}>{categories[c]||c}</option>)}</select></label></div>
      {assets.isPending&&<p role="status">{l('Loading source files…','جارٍ تحميل ملفات المصادر…')}</p>}
      {assets.isError&&<p role="alert">{l('Could not load source files.','تعذّر تحميل ملفات المصادر.')} <button className="button" onClick={()=>assets.refetch()}>{t('Retry')}</button></p>}
      {assets.data&&<p role="status">{assets.data.items.length} / {assets.data.total} {l('unique source files','ملف مصدر مميز')}</p>}
      {assets.data?.items.length===0&&<p>{l('No files match. Change your search or category.','لا توجد ملفات مطابقة. غيّر البحث أو الفئة.')}</p>}
      {assets.data?.items.map(a=><article className="source-file" key={a.id}><h3 dir="auto">{a.name}</h3><p>{categories[a.category]||a.category} · {a.study_id||l('Study mapping pending','ربط الدراسة قيد المراجعة')} · {(a.bytes/1024/1024).toFixed(2)} MB</p><a className="button" href={'/api/v1/research-files/'+a.id+'/download'}>{l('Download original','تنزيل الأصل')}</a><details><summary>{l('Provenance and checksum','المصدر والبصمة')}</summary><p>{l('User supplied; attribution and usage terms require review.','مرفق من المستخدم؛ نسبة الملف وشروط استخدامه تحتاج مراجعة.')}</p><a href={a.source_url} target="_blank" rel="noreferrer">{l('Repository reference','مرجع المستودع')}</a><p><code>SHA-256 {a.id}</code></p>{a.aliases.length>1&&<p>{l('Identical aliases','أسماء ذات محتوى مطابق')}: {a.aliases.join(' · ')}</p>}</details></article>)}
    </section>
  </div>;
}
