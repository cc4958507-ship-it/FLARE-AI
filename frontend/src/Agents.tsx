import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from './api';
import { t, useLanguage } from './i18n';
import {datasetLabel} from './presentation';

type Note = {summary:string; findings:{text:string; source_ids:string[]; limitations:string[]}[]; missing_information:string[]; next_steps:string[]; dataset_counts?:{source_records:number;channels:number;measurement_values:number}|null};
type Job = {id:string; kind:string; status:string; input:{question:string; language:string}; result:Note|null; calls_used:number; max_calls:number; error_code:string|null; steps?:{action:string; reason:string; result:unknown}[]; events?:{seq:number; type:string; at:string}[]; calls?:{id:string; state:string; credits:number|null}[]};
type Capabilities = {enabled:boolean; budget:{unknown_calls:number}};
const terminal = ['succeeded','failed','needs_review','cancelled'];

export default function Agents() {
  const language = useLanguage();
  const l = (en:string, ar:string) => language === 'ar' ? ar : en;
  const roles = {research:l('Evidence researcher','باحث الأدلة'), dataset_review:l('Measurement reviewer','مراجع القياسات'), run_review:l('Simulation reviewer','مراجع المحاكاة')};
  const statuses:Record<string,string> = {queued:l('Queued','في الطابور'), running:l('Working','قيد التنفيذ'), retry_wait:l('Waiting to retry','بانتظار إعادة المحاولة'), succeeded:l('Completed','مكتملة'), failed:l('Stopped','متوقفة'), needs_review:l('Needs review','تحتاج مراجعة'), cancelled:l('Cancelled','ملغاة')};
  const [params]=useSearchParams();
  const [datasetId,setDatasetId]=useState(params.get('dataset')||'');
  const [kind,setKind] = useState<keyof typeof roles>(params.get('dataset')?'dataset_review':'research');
  const [selected,setSelected] = useState('');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [question,setQuestion]=useState('');
  const [statusFilter,setStatusFilter]=useState('');
  const detailRef=useRef<HTMLElement>(null);
  useEffect(()=>{if(selected)detailRef.current?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});},[selected]);
  const submission = useRef<{payload:string; key:string}|null>(null);
  const capabilities = useQuery({queryKey:['agents'], queryFn:()=>api<Capabilities>('/agents'), refetchInterval:5000});
  const jobs = useQuery({queryKey:['agent-jobs'], queryFn:()=>api<{items:Job[]}>('/agent-jobs'), refetchInterval:2000});
  const detail = useQuery({queryKey:['agent-job',selected], queryFn:()=>api<Job>('/agent-jobs/'+selected), enabled:!!selected, refetchInterval:2000});
  const datasets = useQuery({queryKey:['datasets'], queryFn:()=>api<{items:{id:string; manifest:{title:string}}[]}>('/datasets')});
  const runs = useQuery({queryKey:['runs'], queryFn:()=>api<{items:{id:string; name:string}[]}>('/runs')});
  const budget = capabilities.data?.budget;
  const blocked = !capabilities.data?.enabled || !!budget?.unknown_calls;
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const fields = new FormData(event.currentTarget);
    const payload = {kind, question:String(fields.get('question')), language, max_calls:Number(fields.get('max_calls')), evidence_ids:['flex','cool-flames'], dataset_id:fields.get('dataset_id') || null, run_id:fields.get('run_id') || null};
    const serialized = JSON.stringify(payload);
    if (submission.current?.payload !== serialized) submission.current = {payload:serialized, key:crypto.randomUUID()};
    try {
      const job = await api<Job>('/agent-jobs',{...payload,idempotency_key:submission.current!.key});
      setSelected(job.id); submission.current = null;
      await jobs.refetch();
    } catch(err) {setError(err instanceof Error ? err.message : l('Could not queue the task. Retry.','تعذّر حفظ المهمة. أعد المحاولة.'));}
    finally {setBusy(false);}
  }
  async function cancel() {
    setBusy(true); setError('');
    try {await api('/agent-jobs/'+selected+'/cancel',{}); await detail.refetch(); await jobs.refetch();}
    catch(err) {setError(err instanceof Error ? err.message : 'Request failed');}
    finally {setBusy(false);}
  }
  const job = detail.data;
  function sourceLink(id:string) {
    const [type,...parts] = id.split(':');
    const value = parts.join(':');
    const href = type==='dataset' ? '/datasets?dataset='+encodeURIComponent(value) : type==='run' ? '/lab/'+encodeURIComponent(value) : '/investigations/'+encodeURIComponent(value);
    return <Link key={id} to={href}><code>{id}</code></Link>;
  }
  return <div className="measurement-imports agent-page">
    <h1 tabIndex={-1}>{l('Research agents','إيجنتس البحث')}</h1>
    <p>{l('Ask a focused question, attach your data and review a source-linked research note. Each task keeps its sources and steps.','اكتب سؤالًا محددًا وأرفق بياناتك، ثم راجع مذكرة مرتبطة بالمصادر. تُحفظ مصادر كل مهمة وخطواتها.')}</p>
    <p className="workflow-hint">{l('New here? Start with a dataset, then choose Measurement reviewer.','أول مرة؟ ابدأ بمجموعة بيانات، ثم اختر مراجع القياسات.')} <Link to="/research-files">{l('Browse available data','تصفّح البيانات المتاحة')}</Link></p>
    <section className="panel" aria-labelledby="task-heading">
      <h2 id="task-heading">{l('Assign a research task','إسناد مهمة بحثية')}</h2>
      {capabilities.isPending && <p role="status">{l('Checking agent availability…','جارٍ التحقق من توفر الإيجنتس…')}</p>}
      {capabilities.isError && <p role="alert">{l('Could not check agent availability.','تعذّر التحقق من توفر الإيجنتس.')} <button className="button" onClick={()=>capabilities.refetch()}>{t('Retry')}</button></p>}
      {!!budget?.unknown_calls && <p role="alert">{l('Agent tasks are paused for service review.','مهام الإيجنتس متوقفة مؤقتًا لمراجعة الخدمة.')}</p>}
      {capabilities.data && !capabilities.data.enabled && <p role="status">{l('Live AI is not configured. A server-side Kie key and live mode are required.','الذكاء المباشر غير مهيّأ. يلزم مفتاح Kie على الخادم وتفعيل الوضع المباشر.')}</p>}
      <form className="agent-form" onSubmit={submit}>
        <label className="agent-question">{l('Research question','السؤال البحثي')}<textarea name="question" required minLength={5} maxLength={2000} rows={3} value={question} onChange={e=>setQuestion(e.target.value)} placeholder={l('What is missing in these observations, and what can we conclude from them?','ما الذي ينقص هذه القياسات، وما الذي يمكن استنتاجه منها؟')} /></label>
        <div className="agent-example"><button type="button" className="button" onClick={()=>setQuestion(kind==='run_review'?l('Review this synthetic run. Explain missing channels and the limits of its conclusions.','راجع هذه المحاكاة ووضّح القنوات المفقودة وحدود الاستنتاجات.'):kind==='dataset_review'?l('Inspect the selected dataset. Describe missing values, unresolved units and calibration limitations.','افحص مجموعة البيانات المحددة ووضّح القيم المفقودة والوحدات غير الموثقة وحدود المعايرة.'):l('Compare the selected FLEX and cool-flame evidence. What is supported and what remains unknown?','قارن أدلة FLEX واللهب البارد: ما الذي تدعمه المصادر وما الذي يبقى مجهولًا؟'))}>{l('Use an example question','استخدم سؤالًا جاهزًا')}</button><span>{l('Edit it before starting.','يمكنك تعديله قبل البدء.')}</span></div>
        <label>{l('Agent role','دور الإيجنت')}<select value={kind} onChange={e=>setKind(e.target.value as keyof typeof roles)}>{Object.entries(roles).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
        <label>{l('Dataset','مجموعة القياسات')}<select name="dataset_id" value={datasetId} onChange={e=>setDatasetId(e.target.value)} required={kind==='dataset_review'}><option value="">{l('No dataset','بدون مجموعة')}</option>{datasets.data?.items.map(d=><option value={d.id} key={d.id}>{datasetLabel(d.manifest.title,language)}</option>)}</select></label>
        <label>{l('Simulation run','تشغيلة المحاكاة')}<select name="run_id" required={kind==='run_review'}><option value="">{l('No run','بدون تشغيلة')}</option>{runs.data?.items.map(r=><option value={r.id} key={r.id}>{r.name}</option>)}</select></label>
        {(datasets.isError || runs.isError) && <p role="alert">{l('Some attachments could not load. Reload this page to retry.','تعذّر تحميل بعض المرفقات. أعد تحميل الصفحة للمحاولة.')}</p>}
        <details className="agent-options"><summary>{l('Advanced task settings','إعدادات المهمة المتقدمة')}</summary><p>{l('Evidence scope: FLEX and Cool Flames source summaries. Attached data is inspected separately.','نطاق الأدلة: ملخصا FLEX واللهب البارد. تُفحص البيانات المرفقة بشكل منفصل.')}</p><label>{l('Maximum model requests','الحد الأقصى لطلبات النموذج')}<select name="max_calls" defaultValue="4">{[2,3,4,5,6].map(n=><option key={n} value={n}>{n}</option>)}</select></label></details>
        <button className="button primary" disabled={busy || blocked}>{l(busy?'Saving…':'Queue task',busy?'جارٍ الحفظ…':'إضافة إلى الطابور')}</button>
      </form>
    </section>
    {error && <p className="error-box" role="alert">{error}</p>}
    <section className="panel" aria-labelledby="queue-heading">
      <h2 id="queue-heading">{l('Saved tasks','المهام المحفوظة')}</h2>
      <label className="task-filter">{l('Task status','حالة المهمة')}<select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option value="">{l('All tasks','كل المهام')}</option>{Object.entries(statuses).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
      {jobs.isPending && <p role="status">{l('Loading tasks…','جارٍ تحميل المهام…')}</p>}
      {jobs.isError && <p role="alert">{l('Tasks unavailable.','تعذّر تحميل المهام.')} <button className="button" onClick={()=>jobs.refetch()}>{t('Retry')}</button></p>}
      {jobs.data?.items.length===0 && <p>{l('No tasks yet. Assign a question above to begin.','لا توجد مهام بعد. أسند سؤالًا أعلاه للبدء.')}</p>}
      {jobs.data&&statusFilter&&!jobs.data.items.some(j=>j.status===statusFilter)&&<p>{l('No tasks with this status. Choose another status.','لا توجد مهام بهذه الحالة. اختر حالة أخرى.')}</p>}
      {jobs.data?.items.filter(j=>!statusFilter||j.status===statusFilter).map(j=><article className={'agent-task-row'+(selected===j.id?' is-selected':'')} key={j.id}><h3>{j.input.question}</h3><p>{roles[j.kind as keyof typeof roles]} · <span className={'task-state state-'+j.status}>{statuses[j.status]}</span></p><button className="button" onClick={()=>setSelected(j.id)}>{l('Inspect task','فحص المهمة')}</button></article>)}
    </section>
    {selected && <section ref={detailRef} className="panel agent-detail" aria-labelledby="detail-heading">
      <h2 id="detail-heading">{l('Task record','سجل المهمة')}</h2>
      {detail.isPending && <p role="status">{l('Loading record…','جارٍ تحميل السجل…')}</p>}
      {detail.isError && <p role="alert">{l('Record unavailable.','تعذّر تحميل السجل.')} <button className="button" onClick={()=>detail.refetch()}>{t('Retry')}</button></p>}
      {job && <>
        <p><strong>{statuses[job.status]}</strong> · <code>{job.id}</code></p>
        {job.error_code && <p role="status">{l('Stopped with code','توقفت بالرمز')}: <code>{job.error_code}</code>. {l('Inspect the saved steps before submitting a new task.','افحص الخطوات المحفوظة قبل إرسال مهمة جديدة.')}</p>}
        {!terminal.includes(job.status) && <><button className="button" disabled={busy} onClick={cancel}>{l('Cancel remaining steps','إلغاء الخطوات المتبقية')}</button><p>{l('An already dispatched request may still finish and consume credits.','قد يكتمل طلب أُرسل بالفعل ويستهلك رصيدًا.')}</p></>}
        <details><summary>{l('Agent steps and source inspection','خطوات الإيجنت وفحص المصادر')} ({job.steps?.length||0})</summary><ol>{job.steps?.map((step,i)=><li key={i}><strong><code>{step.action}</code></strong><p>{step.reason}</p><details><summary>{l('Tool result','نتيجة الأداة')}</summary><pre className="agent-json" dir="ltr">{JSON.stringify(step.result,null,2)}</pre></details></li>)}</ol></details>
        {job.result?.dataset_counts&&<p>{job.result.dataset_counts.source_records.toLocaleString(language)} {l('source records','سجلًا أصليًا')} · {job.result.dataset_counts.channels} {l('channels','قناة')} · {job.result.dataset_counts.measurement_values.toLocaleString(language)} {l('channel values; counts checked against the stored data','قيمة قناة؛ الأعداد مطابقة للبيانات المحفوظة')}</p>}
        {job.result && <div lang={job.input.language} dir={job.input.language==='ar'?'rtl':'ltr'}><h3>{l('Research note','المذكرة البحثية')} ({job.input.language})</h3><p>{job.result.summary}</p>{job.result.findings.map((finding,i)=><article key={i}><p>{finding.text}</p><p className="agent-sources">{finding.source_ids.map(sourceLink)}</p><ul>{finding.limitations.map((s,i)=><li key={i}>{s}</li>)}</ul></article>)}<h3>{l('Missing information','المعلومات الناقصة')}</h3><ul>{job.result.missing_information.map((s,i)=><li key={i}>{s}</li>)}</ul><h3>{l('Next steps','الخطوات التالية')}</h3><ul>{job.result.next_steps.map((s,i)=><li key={i}>{s}</li>)}</ul></div>}
        <details><summary>{l('Requests and reported cost','الطلبات والتكلفة المُبلّغة')}</summary><ul>{job.calls?.map(c=><li key={c.id}><code>{c.id}</code> · {c.state} · {c.credits??l('Unknown','غير معروفة')} {l('credits','رصيد')}</li>)}</ul></details>
        <details><summary>{l('Event history','سجل الأحداث')}</summary><ol>{job.events?.map(e=><li key={e.seq}><code>{e.type}</code> · <time>{new Date(e.at).toLocaleString(language)}</time></li>)}</ol></details>
      </>}
    </section>}
  </div>;
}
