import asyncio
import csv
import copy
import html
import json
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pathlib import Path
import os
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from .engine import Action, Event, replay
from .db import Session, Record, Run, Frame, AuditEvent
from .corpus import RECORDS, ranked
from .service import uid, now, add_event, create_run
from .ai import explain
from .reporting import render_report
from .ingestion import ImportRequest, parse_csv
from .db import Dataset, Measurement, DatasetArtifact, ResearchAsset
from .dataset_access import measurement_page, chart_series
from .research_data import asset_path
from .nasa_flex import load_flex
from .agents import JobRequest, create_job, job_payload, event as agent_event, TOOLS, TERMINAL
from .db import AgentJob
from .provider import budget_snapshot, ProviderError, utcnow
import hashlib

app = FastAPI(title='FLARE AI', version='0.2.0', description='Synthetic research workbench. No physical hardware connections.')

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Intervention(Strict):
    t: Annotated[int, Field(ge=0, le=3600)]
    action: Action

class SensorFault(Strict):
    channel: Literal['flame_presence', 'thermal_excess', 'co_proxy', 'ventilation_proxy'] = 'co_proxy'
    fault: Literal['drop', 'freeze', 'replay', 'skew', 'saturation'] = 'drop'

class ScheduledFault(SensorFault):
    t: int = Field(ge=0, le=3600)

class ReplayRequest(Strict):
    seed: int = 42
    duration: Annotated[int, Field(ge=1, le=3600)] = 180
    events: Annotated[list[Intervention], Field(max_length=100)] = []
    fault_at: Annotated[int | None, Field(ge=0, le=3600)] = None
    faults: list[ScheduledFault] = Field(default_factory=list, max_length=100)

class Comparison(Strict):
    investigation_ids: list[str] = Field(min_length=2, max_length=3)

class ScenarioRequest(Strict):
    name: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=5, max_length=2000)
    investigation_ids: list[str] = Field(min_length=1, max_length=3)
    fuel: Literal['Abstract liquid droplet'] = 'Abstract liquid droplet'
    geometry: Literal['Single droplet'] = 'Single droplet'

class VersionRequest(Strict):
    version: Literal[1] = 1
    language: Literal['en', 'ar'] = 'en'

class ApproveRequest(Strict):
    plan_version: Literal[1] = 1
    profile_ref: Literal['synthetic-v1'] = 'synthetic-v1'

class RunRequest(Strict):
    plan_ref: str
    seed: int = Field(default=42, ge=0, le=2147483647)
    name: str | None = Field(default=None, max_length=120)
    preset: Literal['manual','reduce','stop','data-loss'] = 'manual'

class Command(Strict):
    command: Literal['start', 'pause', 'resume', 'speed']
    speed: Literal[1,4,16] = 4
    command_id: str = Field(min_length=1,max_length=100)

class Apply(Strict):
    option_id: Action
    effective_t_ms: int | None = Field(default=None, ge=0, le=240000)

class Fault(SensorFault):
    pass

class Branch(Strict):
    parent_t_ms: int = Field(ge=0, le=240000)
    name: str = Field(min_length=1, max_length=120)


def record(db, id, kind):
    row = db.get(Record, id)
    if not row or row.kind != kind:
        raise HTTPException(404, f'{kind} not found')
    return row


def get_run(db, id, lock=False):
    stmt = select(Run).where(Run.id == id)
    if lock:
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if not row:
        raise HTTPException(404, 'Run not found')
    return row


def sources(ids):
    if len(set(ids)) != len(ids):
        raise HTTPException(422, 'Duplicate investigation identifiers')
    rows = [r for r in RECORDS if r['id'] in ids]
    if len(rows) != len(ids):
        raise HTTPException(422, 'Unknown investigation identifier')
    return rows

@app.get('/api/v1/health')
def health():
    return {'status':'ok','mode':'synthetic','model_mode':'live' if os.getenv('AI_MODE')=='live' and os.getenv('KIE_API_KEY') else 'offline','engine_version':'0.1.0'}

@app.get('/api/v1/readiness')
def readiness():
    with Session() as db:
        db.execute(text('SELECT 1'))
    return {'database':'connected'}

@app.get('/api/v1/investigations')
def investigations(q: str = '', family: str | None = None):
    return {'items': ranked(q, family), 'corpus_version':'curated-spec-v1', 'review_status':'Source summaries; NASA FLEX-007 tabulated measurements are separate Replay Only datasets.'}

@app.get('/api/v1/investigations/{id}')
def investigation(id: str):
    return sources([id])[0]

@app.post('/api/v1/comparisons')
def compare(request: Comparison):
    rows = sources(request.investigation_ids)
    return {'items':rows, 'quantitative_comparison':False, 'limitations':['No shared calibrated time series. Compare context and channel availability only.', 'Synthetic values cannot be compared numerically with NASA metadata.']}

@app.post('/api/v1/scenarios', status_code=201)
def scenario(request: ScenarioRequest):
    sources(request.investigation_ids)
    with Session.begin() as db:
        row = Record(id=uid('scenario'), kind='scenario', payload={**request.model_dump(), 'version':1,'scope':'synthetic','created_at':now()})
        db.add(row)
        return {'id':row.id, **row.payload}

@app.get('/api/v1/scenarios/{id}')
def get_scenario(id: str):
    with Session() as db:
        row = record(db,id,'scenario')
        return {'id':row.id,**row.payload}

@app.post('/api/v1/scenarios/{id}/evidence')
async def evidence(id: str, request: VersionRequest):
    with Session() as db:
        scenario = record(db,id,'scenario')
        pack = sources(scenario.payload['investigation_ids'])
    payload = {'scenario_id':id, 'snapshot':'curated-spec-v1','items':pack, 'explanation':await explain(pack, request.language), 'created_at':now()}
    with Session.begin() as db:
        snapshot = Record(id=uid('evidence'), kind='evidence', payload=payload)
        db.add(snapshot)
        return {'id':snapshot.id, **payload}

@app.post('/api/v1/scenarios/{id}/plans', status_code=201)
def plan(id: str, request: VersionRequest):
    with Session.begin() as db:
        scenario = record(db,id,'scenario')
        packs = db.scalars(select(Record).where(Record.kind=='evidence').order_by(Record.created_at.desc())).all()
        snapshot = next((p for p in packs if p.payload['scenario_id']==id), None)
        if not snapshot:
            raise HTTPException(409,'Retrieve evidence before creating a plan')
        payload = {'scenario_id':id,'scenario_version':1,'version':1,'profile_ref':'synthetic-v1','approved':False,
                   'evidence_snapshot_id':snapshot.id,
                   'evidence_ids':scenario.payload['investigation_ids'], 'options':[a.value for a in Action],
                   'required_channels':['flame_presence','thermal_excess','co_proxy','ventilation_proxy'],
                   'verification_hold_s':30,'danger_clear_s':10,'scope':'Synthetic single-droplet only','created_at':now()}
        row = Record(id=uid('plan'),kind='plan',payload=payload)
        db.add(row)
        return {'id':row.id,**payload}

@app.get('/api/v1/plans/{id}')
def get_plan(id: str):
    with Session() as db:
        row=record(db,id,'plan')
        return {'id':id,**row.payload}

@app.post('/api/v1/plans/{id}/approve')
def approve(id: str, request: ApproveRequest):
    with Session.begin() as db:
        row=db.scalar(select(Record).where(Record.id==id).with_for_update())
        if not row or row.kind!='plan':
            raise HTTPException(404,'Plan not found')
        if not row.payload['approved']:
            row.payload={**row.payload,'approved':True,'approved_at':now()}
        return {'id':id,**row.payload}

@app.post('/api/v1/runs', status_code=201)
def new_run(request: RunRequest):
    with Session.begin() as db:
        plan=record(db,request.plan_ref,'plan')
        if not plan.payload['approved']:
            raise HTTPException(409,'Approve the plan before creating a run')
        row=create_run(db,plan,request.seed,request.name,preset=request.preset)
        return {'id':row.id,**row.payload}

@app.get('/api/v1/runs')
def runs():
    with Session() as db:
        rows=db.scalars(select(Run).order_by(Run.created_at.desc())).all()
        return {'items':[{'id':r.id,**r.payload} for r in rows]}

@app.get('/api/v1/runs/{id}')
def run(id: str):
    with Session() as db:
        row=get_run(db,id)
        return {'id':id,'revision':row.revision,**row.payload}

@app.post('/api/v1/runs/{id}/commands')
def command(id: str, request: Command):
    with Session.begin() as db:
        row=get_run(db,id,True)
        previous=db.scalars(select(AuditEvent).where(AuditEvent.run_id==id)).all()
        for event in previous:
            if event.payload.get('command_id')==request.command_id:
                if event.payload.get('command')!=request.command or event.payload.get('speed')!=request.speed:
                    raise HTTPException(409,'Command identifier reused with different payload')
                return event.payload
        p=copy.deepcopy(row.payload)
        if p['status']=='completed':
            raise HTTPException(409,'Completed runs are immutable. Create a branch.')
        if request.command in ('start','resume'):
            p['status']='running'
        elif request.command=='pause':
            p['status']='paused'
        else:
            p['speed']=request.speed
        row.payload=p
        return add_event(db,row,'command',request.model_dump())

@app.post('/api/v1/runs/{id}/interventions')
def intervene(id: str, request: Apply):
    with Session.begin() as db:
        row=get_run(db,id,True)
        p=copy.deepcopy(row.payload)
        t=p['t']+1 if request.effective_t_ms is None else request.effective_t_ms//1000
        if request.effective_t_ms is not None and request.effective_t_ms % 1000:
            raise HTTPException(422,'Intervention time must align to the 1000ms sampling step')
        if t<=p['t'] or t>p['duration'] or p['status']=='completed':
            raise HTTPException(409,'Interventions must target a future sample. Branch to change the past.')
        if any(e['t']==t for e in p['interventions']):
            raise HTTPException(409,'An intervention already exists at that time')
        p['interventions'].append({'t':t,'action':request.option_id.value})
        row.payload=p
        return add_event(db,row,'intervention_scheduled',{'effective_t':t,'action':request.option_id.value})

@app.post('/api/v1/runs/{id}/faults')
def fault(id: str, request: Fault):
    with Session.begin() as db:
        row=get_run(db,id,True)
        if row.payload['status']=='completed':
            raise HTTPException(409,'Branch a completed run to inject a fault')
        t = row.payload['t'] + 1
        if t > row.payload['duration']:
            raise HTTPException(409, 'No future sample available')
        faults = row.payload.get('faults', [])
        if any(f['channel'] == request.channel for f in faults):
            raise HTTPException(409, 'This channel already has a scheduled fault')
        row.payload={**row.payload,'faults':[*faults, {'t':t, **request.model_dump()}]}
        return add_event(db,row,'fault_scheduled',{'effective_t':t,**request.model_dump()})

@app.post('/api/v1/runs/{id}/branches', status_code=201)
def branch(id: str, request: Branch):
    with Session.begin() as db:
        parent=get_run(db,id,True)
        if request.parent_t_ms % 1000 or request.parent_t_ms//1000>parent.payload['t']:
            raise HTTPException(422,'Branch time must be an existing sample boundary')
        plan=record(db,parent.payload['plan_id'],'plan')
        child=create_run(db,plan,parent.payload['seed'],request.name,parent=parent,branch_t=request.parent_t_ms//1000)
        return {'id':child.id,**child.payload}

@app.get('/api/v1/runs/{id}/samples')
def samples(id: str, after_t: int = -1):
    with Session() as db:
        get_run(db,id)
        frames=db.scalars(select(Frame).where(Frame.run_id==id,Frame.t>after_t).order_by(Frame.t)).all()
        return {'items':[{'sample':f.sample,'decision':f.decision} for f in frames]}

@app.get('/api/v1/runs/{id}/events')
async def events(id: str, request: Request, after_seq: int = 0, stream: bool = False):
    with Session() as db:
        get_run(db,id)
    if not stream:
        with Session() as db:
            return {'items':[e.payload for e in db.scalars(select(AuditEvent).where(AuditEvent.run_id==id,AuditEvent.seq>after_seq).order_by(AuditEvent.seq))]}
    try:
        cursor=max(after_seq,int(request.headers.get('last-event-id','0')))
    except ValueError:
        raise HTTPException(422,'Invalid Last-Event-ID')
    async def generate():
        nonlocal cursor
        while not await request.is_disconnected():
            with Session() as db:
                rows=db.scalars(select(AuditEvent).where(AuditEvent.run_id==id,AuditEvent.seq>cursor).order_by(AuditEvent.seq)).all()
                for row in rows:
                    cursor=row.seq
                    yield f'id: {cursor}\nevent: audit\ndata: {json.dumps(row.payload)}\n\n'
            yield ': keepalive\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/v1/runs/{id}/report')
def report(id: str, format: Literal['json','html']='json', language: Literal['en','ar']='en'):
    with Session() as db:
        row=get_run(db,id)
        plan=record(db,row.payload['plan_id'],'plan')
        scenario=record(db,row.payload['scenario_id'],'scenario')
        payload={'run':{'id':id,**row.payload},'plan':plan.payload,'scenario':scenario.payload,
                 'evidence':sources(plan.payload['evidence_ids']),
                 'evidence_snapshot':record(db,plan.payload['evidence_snapshot_id'],'evidence').payload if plan.payload.get('evidence_snapshot_id') else None,
                 'events':[e.payload for e in db.scalars(select(AuditEvent).where(AuditEvent.run_id==id).order_by(AuditEvent.seq))],
                 'frames':[{'sample':f.sample,'decision':f.decision} for f in db.scalars(select(Frame).where(Frame.run_id==id).order_by(Frame.t))],
                 'exported_at':now(),'limitations':['Synthetic demo only; not a safety assessment.','NASA measurements are not used in this synthetic run.','Re-ignition risk not evaluated.']}
    if format=='json':
        return JSONResponse(payload,headers={'Content-Disposition':f'attachment; filename="{id}.json"'})
    return HTMLResponse(render_report(payload, language),headers={'Content-Disposition':f'inline; filename="{id}.html"'})

@app.post('/api/v1/replays')
def run_replay(request: ReplayRequest):
    return replay(request.seed,request.duration,[Event(e.t,e.action) for e in request.events],request.fault_at,[f.model_dump() for f in request.faults])

@app.post('/api/v1/datasets', status_code=201)
def import_dataset(request: ImportRequest):
    try:
        parsed = parse_csv(request.csv_text)
    except (ValueError, csv.Error) as exc:
        raise HTTPException(422, str(exc)) from exc
    manifest = request.model_dump(mode='json', exclude={'csv_text'})
    return save_dataset(manifest, parsed, request.csv_text)


def save_dataset(manifest, parsed, normalized_csv, artifacts=()):
    # Metadata is part of identity so a different source attribution cannot be silently reused.
    digest = hashlib.sha256(json.dumps([manifest, parsed['sha256'], parsed['parser_version']], sort_keys=True).encode()).hexdigest()
    dataset_id = 'data_' + digest[:59]
    summary = {k:v for k,v in parsed.items() if k != 'accepted'}
    with Session.begin() as db:
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': int(digest[:15], 16)})
        existing = db.get(Dataset, dataset_id)
        if existing:
            return {'id': existing.id, 'manifest': existing.manifest, 'report': existing.report, 'reused': True}
        stored_manifest = {'review_status':'unreviewed', **manifest, 'created_at':now()}
        db.add(Dataset(id=dataset_id, manifest=stored_manifest, raw_csv=normalized_csv, report=summary))
        db.flush()
        for artifact in artifacts:
            db.add(DatasetArtifact(dataset_id=dataset_id, name=artifact['name'], content=artifact['content'], metadata_json=artifact['metadata']))
        for sample in parsed['accepted']:
            metadata = {k:v for k,v in sample.items() if k not in ('channel','sensor_id','seq','t_rel_ms','value')}
            db.add(Measurement(dataset_id=dataset_id, **{k:sample[k] for k in ('channel','sensor_id','seq','t_rel_ms','value')}, metadata_json=metadata))
        return {'id':dataset_id, 'manifest':stored_manifest, 'report':summary, 'reused':False}


@app.post('/api/v1/datasets/nasa/flex-007', status_code=201)
def import_nasa_flex():
    try:
        manifest, parsed, normalized_csv, artifacts = load_flex()
    except (ValueError, OSError, KeyError, csv.Error) as exc:
        raise HTTPException(503, 'Bundled NASA source validation failed') from exc
    return save_dataset(manifest, parsed, normalized_csv, artifacts)


@app.get('/api/v1/datasets')
def datasets():
    with Session() as db:
        return {'items':[{'id':d.id, 'manifest':d.manifest, 'report':d.report} for d in db.scalars(select(Dataset))]}


@app.get('/api/v1/datasets/{id}')
def dataset(id: str, offset: int = Query(0, ge=0), limit: int = Query(1000, ge=1, le=10000), channel: str | None = Query(None,max_length=120)):
    with Session() as db:
        row = db.get(Dataset, id)
        if not row:
            raise HTTPException(404, 'Dataset not found')
        try:
            items,page,channels=measurement_page(db,row,offset,limit,channel)
        except ValueError as exc:
            raise HTTPException(404,str(exc)) from exc
        return {'id':id, 'manifest':row.manifest, 'report':row.report,
                'items':items,'page':page,'channels':channels}


@app.get('/api/v1/datasets/{id}/series')
def dataset_series(id: str, channel: str = Query(...,max_length=120), max_points: int = Query(1500,ge=10,le=5000)):
    with Session() as db:
        row=db.get(Dataset,id)
        if not row:
            raise HTTPException(404,'Dataset not found')
        try:
            return chart_series(db,row,channel,max_points)
        except ValueError as exc:
            raise HTTPException(404,str(exc)) from exc


@app.get('/api/v1/datasets/{id}/raw')
def dataset_raw(id: str):
    from fastapi.responses import Response
    with Session() as db:
        row = db.get(Dataset, id)
        if not row:
            raise HTTPException(404, 'Dataset not found')
        return Response(row.raw_csv, media_type='text/csv', headers={'Content-Disposition':'attachment; filename="measurements.csv"'})


@app.get('/api/v1/datasets/{id}/artifacts/{name}')
def dataset_artifact(id: str, name: str):
    from fastapi.responses import Response
    with Session() as db:
        row = db.get(DatasetArtifact, (id, name))
        if not row:
            dataset=db.get(Dataset,id)
            asset=db.get(ResearchAsset,dataset.manifest.get('source_asset_id')) if dataset and dataset.manifest.get('source_file')==name else None
            if asset:
                return research_download(asset.id)
            raise HTTPException(404, 'Source file not found')
        return Response(row.content, media_type='application/octet-stream',
                        headers={'Content-Disposition':f'attachment; filename="{row.name}"',
                                 'X-Content-SHA256':row.metadata_json['sha256']})


@app.get('/api/v1/research-files')
def research_files(q: str = Query('',max_length=300),category: str | None = Query(None,max_length=64)):
    with Session() as db:
        assets=[a.payload for a in db.scalars(select(ResearchAsset))]
        filtered=[a for a in assets if (not category or a['category']==category)
                  and q.casefold() in ' '.join([a['name'],a.get('study_id') or '',*a.get('aliases',[])]).casefold()]
        return {'total':len(assets),'categories':sorted({a['category'] for a in assets}),
                'items':[{k:v for k,v in a.items() if k!='object'} for a in sorted(filtered,key=lambda a:a['name'])]}


@app.get('/api/v1/research-files/{id}/download')
def research_download(id: str):
    with Session() as db:
        row=db.get(ResearchAsset,id)
        if not row:
            raise HTTPException(404,'Research file not found')
        try:
            path=asset_path(row.payload)
        except (ValueError,KeyError) as exc:
            raise HTTPException(503,'Research file unavailable') from exc
        if not path.is_file() or path.stat().st_size!=row.payload['bytes']:
            raise HTTPException(503,'Research file unavailable')
        return FileResponse(path,media_type='application/octet-stream',filename=row.payload['name'],
            headers={'X-Content-SHA256':row.id,'X-Content-Type-Options':'nosniff'})


@app.get('/api/v1/agents')
def agent_capabilities():
    try:
        budget = budget_snapshot()
    except ProviderError as exc:
        raise HTTPException(503, exc.code) from exc
    return {'roles':[{'id':key, 'tools':list(value)} for key,value in TOOLS.items()],
            'enabled':os.getenv('AI_MODE') == 'live' and bool(os.getenv('KIE_API_KEY')),
            'budget':budget, 'authority':'read_only_research', 'max_pending_jobs':20}


@app.post('/api/v1/agent-jobs', status_code=202)
def new_agent_job(request: JobRequest):
    try:
        job_id, reused = create_job(request)
    except ValueError as exc:
        code = str(exc)
        raise HTTPException(409 if code in ('IDEMPOTENCY_CONFLICT','QUEUE_FULL') else 422, code) from exc
    with Session() as db:
        return {**job_payload(db, db.get(AgentJob, job_id)), 'reused':reused}


@app.get('/api/v1/agent-jobs')
def agent_jobs(limit: int = Query(50, ge=1, le=100)):
    with Session() as db:
        rows = db.scalars(select(AgentJob).order_by(AgentJob.created_at.desc()).limit(limit)).all()
        return {'items':[job_payload(db, row) for row in rows]}


@app.get('/api/v1/agent-jobs/{id}')
def agent_job(id: str):
    with Session() as db:
        row = db.get(AgentJob, id)
        if not row:
            raise HTTPException(404, 'Agent job not found')
        return job_payload(db, row, detail=True)


@app.post('/api/v1/agent-jobs/{id}/cancel')
def cancel_agent_job(id: str):
    with Session.begin() as db:
        row = db.scalar(select(AgentJob).where(AgentJob.id == id).with_for_update())
        if not row:
            raise HTTPException(404, 'Agent job not found')
        if row.status in TERMINAL:
            return job_payload(db, row, detail=True)
        row.status, row.updated_at = 'cancelled', utcnow()
        row.lease_owner = row.lease_until = None
        agent_event(db, row, 'cancelled')
        return job_payload(db, row, detail=True)


@app.get('/{path:path}', include_in_schema=False)
def frontend(path: str):
    if path.startswith('api/'):
        raise HTTPException(404,'API route not found')
    root=Path(os.getenv('FLARE_STATIC_DIR',str(Path(__file__).resolve().parents[2]/'frontend'/'dist'))).resolve()
    target=(root/path).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(404,'Not found')
    if target.is_file():
        return FileResponse(target)
    if path.startswith('assets/'):
        raise HTTPException(404,'Asset not found')
    index=root/'index.html'
    if not index.exists():
        raise HTTPException(503,'Build the frontend with npm run build in frontend/ first')
    return FileResponse(index,headers={'Cache-Control':'no-cache'})
