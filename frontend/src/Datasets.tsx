import { t, useLanguage, msg } from "./i18n";
import { useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from './api';
import DatasetViewer from './DatasetViewer';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import {datasetLabel} from './presentation';

type Dataset = { id: string; manifest: {title: string; origin: string; source_url: string; doi?: string; storage?:string; processing_level?: string; files?: {name: string; sha256: string}[]}; report: {accepted_rows: number; quarantined_rows: number; sha256: string; quarantine: {line: number; reason: string}[]; limitations?: string[]} };

export default function Datasets() {
  const language=useLanguage();
  const [params, setParams] = useSearchParams();
  const datasets = useQuery({queryKey:['datasets'], queryFn:() => api<{items: Dataset[]}>('/datasets')});
  const [csv, setCsv] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{template:string; values:(string|number)[]} | null>(null);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    setBusy(true); setError(''); setMessage(null);
    try {
      const result = await api<Dataset>('/datasets', {title:fields.get('title'), source_url:fields.get('source_url'), license:fields.get('license'), origin:fields.get('origin'), csv_text:csv});
      setMessage({template:"Imported {0} rows; {1} quarantined. Replay Only.", values:[result.report.accepted_rows, result.report.quarantined_rows]});
      setParams({dataset:result.id});
      await datasets.refetch();
    } catch (err) { setError(err instanceof Error ? err.message : 'Import failed'); }
    finally { setBusy(false); }
  }
  async function importNasa() {
    setBusy(true); setError(''); setMessage(null);
    try {
      const result = await api<Dataset>('/datasets/nasa/flex-007', {});
      setMessage({template:"NASA FLEX-007: {0} measurement rows available. Replay Only.", values:[result.report.accepted_rows]});
      setParams({dataset:result.id});
      await datasets.refetch();
    } catch (err) { setError(err instanceof Error ? err.message : 'NASA import failed'); }
    finally { setBusy(false); }
  }
  return <div className="measurement-imports">
    <h1 tabIndex={-1}>{t("Measurement imports")}</h1>
    <p><Link to="/research-files">{language==='ar'?'ملفات البحث الأصلية ومجموعات البيانات الجديدة':'Original research files and new datasets'}</Link></p>
    <p>{t("Preserve source data, normalize explicit units and inspect rejected rows. Imported measurements remain Replay Only and cannot use the synthetic verification profile.")}</p>
    <section className="panel">
      <h2>{t("NASA FLEX-007 / 20CAL13")}</h2>
      <p>{t("Heptane droplet, April 10, 2009. NASA-supplied image-analysis measurements from PSI-69: droplet and flame diameters and positions. Seven channels, with original files and source locations.")}</p>
      <p>{t("Preliminary release; some camera images are missing and luminous flame obscures part of the droplet history. No independent calibration or combustion classification.")}</p>
      <p><a href="https://doi.org/10.60555/mbq8-0451" target="_blank" rel="noreferrer">{t("NASA dataset DOI")}</a>{t(" · CC0-1.0")}</p>
      <button className="button primary" disabled={busy} onClick={importNasa}>{t(busy ? 'Importing…' : 'Load NASA FLEX-007 measurements')}</button>
    </section>
    {error && <p role="alert" className="error-box">{t(error)}</p>}
    <p role="status">{message && msg(message.template,message.values)}</p>
    {params.get('dataset') && <DatasetViewer id={params.get('dataset')!} />}
    <section className="panel scenario-form">
      <h2>{t("Import a measurement CSV")}</h2>
      <p>{t("Required header: ")}<code>{t("channel,sensor_id,seq,t_rel_ms,value,unit")}</code>{t(". Up to 10,000 rows / 2 MB. Leave missing values empty. Supported units: Pa, kPa, K, degC, ppm, fraction, m/s, m, mm.")}</p>
      <p>{t("Convert a source file to this format only after checking its channel definitions, clock and units. Source attribution is recorded as unreviewed.")}</p>
      <form onSubmit={submit}>
        <label>{t("Dataset title")}<input name="title" required maxLength={200} /></label>
        <label>{t("Source URL")}<input name="source_url" type="url" required /></label>
        <label>{t("License / usage terms")}<textarea name="license" required maxLength={2000} /></label>
        <label>{t("Data origin")}<select name="origin"><option value="experimental">{t("Experimental")}</option><option value="NASA raw">{t("NASA raw (requires source review)")}</option><option value="synthetic">{t("Synthetic test fixture")}</option></select></label>
        <label>{t("CSV file")}<input type="file" accept=".csv,text/csv" required disabled={busy} onChange={async e => {
          setCsv(''); setError(''); const file = e.target.files?.[0];
          if (!file) return;
          if (file.size > 2_000_000) { setError('Choose a CSV smaller than 2 MB.'); return; }
          try { setCsv(await file.text()); } catch { setError('Could not read file. Choose it again.'); }
        }} /></label>
        <button className="button primary" disabled={busy || !csv}>{t(busy ? 'Importing…' : 'Validate and import')}</button>
      </form>
    </section>
    <section className="panel">
      <h2>{t("Imported datasets")}</h2>
      {datasets.isPending && <p role="status">{t("Loading datasets…")}</p>}
      {datasets.isError && <p role="alert">{t("Could not load datasets. ")}<button className="button" onClick={() => datasets.refetch()}>{t("Retry")}</button></p>}
      {datasets.data?.items.length === 0 && <p>{t("No datasets imported yet. Start with a documented source CSV.")}</p>}
      {datasets.data?.items.map(d => <article key={d.id}>
        <h3>{d.manifest.doi ? t(d.manifest.title) : datasetLabel(d.manifest.title,language)}</h3>
        <p>{t(d.manifest.origin)} · {t(d.manifest.doi ? 'NASA source files verified; calibration unverified' : 'Unreviewed attribution')}{t(" · Replay Only · ")}{t(d.report.accepted_rows)}{t(" accepted / ")}{t(d.report.quarantined_rows)}{t(" quarantined")}</p>
        {d.manifest.processing_level && <p>{t(d.manifest.processing_level)}</p>}
        <button className="button" onClick={() => setParams({dataset:d.id})}>{t("Inspect measurements")}</button>{t(' · ')}
        <a href={d.manifest.source_url} target="_blank" rel="noreferrer">{t("Source")}</a>{t(' · ')}
        <a href={`/api/v1/datasets/${d.id}/raw`}>{t(d.manifest.storage==='native-wide' ? 'Download original CSV' : d.manifest.files ? 'Download normalized CSV' : 'Download original CSV')}</a>{t(' · ')}
        <a href={`/api/v1/datasets/${d.id}`} target="_blank" rel="noreferrer">{t("Measurements and validation report")}</a>
        {d.manifest.files && <details><summary>{t("Original source files and checksums")}</summary><ul>{d.manifest.files.map(f => <li key={f.name}><a href={`/api/v1/datasets/${d.id}/artifacts/${encodeURIComponent(f.name)}`}>{t(f.name)}</a><br /><code>{t("SHA-256 ")}{t(f.sha256)}</code></li>)}</ul></details>}
        {d.report.limitations && <details><summary>{t("Data limitations")}</summary><ul>{d.report.limitations.map(l => <li key={l}>{t(l)}</li>)}</ul></details>}
        {d.report.quarantine.length > 0 && <details><summary>{t("Quarantined rows")}</summary><ul>{d.report.quarantine.map(q => <li key={q.line}>{t("Row ")}{t(q.line)}: {t(q.reason)}</li>)}</ul></details>}
      </article>)}
    </section>
  </div>;
}
