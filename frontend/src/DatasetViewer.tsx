import { t, useLanguage, msg } from './i18n';
import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as echarts from 'echarts/core';
import { ScatterChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { api } from './api';
echarts.use([ScatterChart,GridComponent,TooltipComponent,CanvasRenderer]);

type Measurement = {channel:string; sensor_id:string; seq:number; t_rel_ms:number; value:number|null; unit:string; quality:string; original_value:string; original_unit:string; source_time_sec?:string; source_timestamp?:string; source_file?:string; source_line?:number; source_column?:string};
type Channel = {channel:string; rows:number; missing:number; unit:string};
type Detail = {items:Measurement[]; channels:Channel[]; page:{total:number}; report:{accepted_rows:number; missing_rows?:number; observation_rows?:number; calibration_status?:string; time_reference?:{source_origin_sec?:string; source_origin?:string; meaning:string}; excluded_columns?:{file:string;column:string;reason:string}[]}};
type Series = {items:{t_rel_ms:number;value:number|null}[]; sampled:boolean; total:number};

export default function DatasetViewer({id}:{id:string}) {
  const language=useLanguage();
  const l=(en:string,ar:string)=>language==='ar'?ar:en;
  const meta=useQuery({queryKey:['dataset-meta',id],queryFn:()=>api<Detail>(`/datasets/${id}?limit=1`)});
  const [channel,setChannel]=useState('');
  const [page,setPage]=useState(0);
  const chartRef=useRef<HTMLDivElement>(null);
  const channels=meta.data?.channels||[];
  const selected=channels.some(c=>c.channel===channel)?channel:channels[0]?.channel;
  const definition=channels.find(c=>c.channel===selected);
  const query=useQuery({queryKey:['dataset-page',id,selected,page],queryFn:()=>api<Detail>(`/datasets/${id}?channel=${encodeURIComponent(selected!)}&offset=${page*25}&limit=25`),enabled:!!selected});
  const series=useQuery({queryKey:['dataset-series',id,selected],queryFn:()=>api<Series>(`/datasets/${id}/series?channel=${encodeURIComponent(selected!)}&max_points=1500`),enabled:!!selected});
  const rows=query.data?.items||[];
  const unit=definition?.unit||'';
  useEffect(()=>setPage(0),[selected,id]);
  useEffect(()=>{
    if(!chartRef.current||!series.data)return;
    const chart=echarts.init(chartRef.current);
    const colors=getComputedStyle(chartRef.current);
    const foreground=colors.getPropertyValue('--graphite').trim();
    const rule=colors.getPropertyValue('--rule').trim();
    chart.setOption({animation:false,grid:{left:75,right:24,bottom:65,top:25},
      tooltip:{trigger:'item',valueFormatter:(v:unknown)=>String(v)},
      xAxis:{type:'value',name:t('Time since first observation (s)'),nameLocation:'middle',nameGap:35,axisLabel:{color:foreground},nameTextStyle:{color:foreground},splitLine:{lineStyle:{color:rule}}},
      yAxis:{type:'value',name:`${selected} (${unit})`,nameTextStyle:{color:foreground},axisLabel:{color:foreground},splitLine:{lineStyle:{color:rule}}},
      series:[{type:'scatter',symbolSize:4,itemStyle:{color:colors.getPropertyValue('--copper').trim()},data:series.data.items.filter(s=>s.value!==null).map(s=>[s.t_rel_ms/1000,s.value])}]});
    const resize=new ResizeObserver(()=>chart.resize());resize.observe(chartRef.current);
    return()=>{resize.disconnect();chart.dispose();};
  },[series.data,selected,unit,language]);
  const time=meta.data?.report.time_reference;
  return <section className="panel measurement-viewer" aria-label={t('Imported measurement viewer')}>
    <h2>{t('Recorded observations')}</h2>
    <p>{t('Replay Only. Points show supplied measurements; gaps are not filled and no combustion state is computed.')}</p>
    {meta.isPending&&<p role="status">{t('Loading measurements…')}</p>}
    {meta.isError&&<p role="alert">{t('Could not load measurements. ')}<button className="button" onClick={()=>meta.refetch()}>{t('Retry')}</button></p>}
    {meta.data&&<>
      <p>{meta.data.report.accepted_rows.toLocaleString(language)}{t(' measurement rows · ')}{meta.data.report.missing_rows??0}{t(' missing values')}</p>
      {meta.data.report.observation_rows&&<p>{meta.data.report.observation_rows.toLocaleString(language)} {l('source records. All records are stored; the table loads one page at a time.','سجلًا أصليًا. جميع السجلات محفوظة؛ يُحمّل الجدول صفحة في كل مرة.')}</p>}
      {time&&<p>{t('Source time origin: ')}<bdi dir="ltr">{time.source_origin_sec!=null?`${time.source_origin_sec} s.`:time.source_origin}</bdi> {t(time.meaning)}{t(' Original source timestamps remain in the table.')}</p>}
      {meta.data.report.calibration_status&&<p>{l('Calibration unverified. Unknown source units remain unresolved; source-scale values must not be interpreted as calibrated physical measurements.','المعايرة غير متحقق منها. تبقى الوحدات غير الموثقة مجهولة؛ لا تُفسّر القيم الأصلية على أنها قياسات فيزيائية معايرة.')}</p>}
      <label>{t('Measurement channel')}<select value={selected||''} onChange={e=>{setChannel(e.target.value);setPage(0);}}>{channels.map(c=><option key={c.channel} value={c.channel}>{t(c.channel)}</option>)}</select></label>
      {series.isPending&&<p role="status">{l('Loading chart…','جارٍ تحميل الرسم…')}</p>}
      {series.isError&&<p role="alert">{l('Could not load chart.','تعذّر تحميل الرسم.')} <button className="button" onClick={()=>series.refetch()}>{t('Retry')}</button></p>}
      <div ref={chartRef} className="measurement-chart" role="img" aria-label={msg('Observed {0} points. Exact values and missing observations are in the table below.',[selected||'measurement'])}/>
      {series.data?.sampled&&<p>{l('Chart overview uses a spaced sample of observations. Exact original records remain available in the paginated table and downloads.','يعرض الرسم عينة متباعدة من الأرصاد. تبقى السجلات الأصلية الدقيقة متاحة في الجدول ذي الصفحات والتنزيلات.')}</p>}
      {!!definition?.rows&&definition.missing===definition.rows&&<p role="status">{t('No numeric observations were supplied for this channel. All values remain missing.')}</p>}
      <p>{definition?.rows.toLocaleString(language)}{t(' observations in this channel · ')}{definition?.missing}{t(' missing')}</p>
      {query.isFetching&&<p role="status">{t('Loading measurements…')}</p>}
      {query.isError&&<p role="alert">{t('Could not load measurements. ')}<button className="button" onClick={()=>query.refetch()}>{t('Retry')}</button></p>}
      <div className="measurement-table-scroll" tabIndex={0} role="region" aria-label={t('Scrollable source measurements')}>
        <table><caption>{t(selected)}{t(': values, original units and source locations')}</caption><thead><tr><th scope="col">{t('Relative time (s)')}</th><th scope="col">{l('Original source time','التوقيت الأصلي')}</th><th scope="col">{t('Value (')}{unit})</th><th scope="col">{t('Original')}</th><th scope="col">{t('Quality')}</th><th scope="col">{t('Source location')}</th></tr></thead>
          <tbody>{rows.map(s=><tr key={`${s.sensor_id}-${s.channel}-${s.seq}`}><td>{s.t_rel_ms/1000}</td><td>{s.source_timestamp??s.source_time_sec??t('Not supplied')}</td><td>{s.value??t('Missing')}</td><td>{s.original_value===''?t('Missing'):s.original_value} {s.original_unit}</td><td>{t(s.quality)}</td><td>{s.source_file?`${s.source_file}:${s.source_line} / ${s.source_column}`:s.sensor_id}</td></tr>)}</tbody>
        </table>
      </div>
      <div className="measurement-pagination"><button className="button" disabled={page===0||query.isFetching} onClick={()=>setPage(p=>p-1)}>{t('Previous observations')}</button><span role="status">{t('Page ')}{page+1}{t(' of ')}{Math.max(1,Math.ceil((definition?.rows||0)/25))}</span><button className="button" disabled={(page+1)*25>=(definition?.rows||0)||query.isFetching} onClick={()=>setPage(p=>p+1)}>{t('Next observations')}</button></div>
      {!!meta.data.report.excluded_columns?.length&&<details><summary>{t('Columns excluded from normalized measurements')}</summary><ul>{meta.data.report.excluded_columns.map(c=><li key={c.file+c.column}>{c.file}: {c.column} — {t(c.reason)}</li>)}</ul></details>}
    </>}
  </section>;
}
