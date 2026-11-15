import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import json
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from flare.api import app
from flare.agents import JobRequest, create_job, claim_job, process_job, execute_tool, prompt_for
from flare.db import Session, AgentJob, LLMCall, Run
from flare.provider import reserve_call, record_call, request_model, budget_snapshot, ProviderError, utcnow, day_start

client = TestClient(app)


def request(**changes):
    return JobRequest(question='Which source observations support this research question?',
                      idempotency_key=uuid4().hex, **changes)


def job(id):
    with Session() as db:
        return db.get(AgentJob,id)


def live(monkeypatch):
    monkeypatch.setenv('AI_MODE','live')
    monkeypatch.setenv('KIE_API_KEY','test-key-never-sent')


def test_operator_reconciliation_clears_usage_lock_without_requeue(monkeypatch):
    from flare.reconcile import reconcile
    live(monkeypatch)
    id,_=create_job(request())
    assert claim_job('worker')==id
    call,_=reserve_call('uncertain request','agent:research',id,0,'worker')
    record_call(call,'unknown',code='REQUEST_OUTCOME_UNKNOWN')
    with Session.begin() as db:
        db.get(AgentJob,id).status='needs_review'
    assert budget_snapshot()['unknown_calls']==1
    with pytest.raises(ValueError):
        reconcile(call,'NaN','billing-review-123')
    reconcile(call,'0.17','billing-review-123')
    assert budget_snapshot()['unknown_calls']==0
    assert budget_snapshot()['reported_credits']==0.17
    assert job(id).status=='needs_review'
    with pytest.raises(ValueError):
        reconcile(call,'0','billing-review-123')


def reply(action, arguments):
    return {'output_text':json.dumps({'action':action,'arguments':arguments,'reason':'Inspect supplied evidence'}),
            'credits_consumed':0.1,'model':'test-model','usage':{'output_tokens':100}}


def final(source='evidence:flex'):
    return {'summary':'A bounded research note', 'findings':[{'text':'Scope is limited', 'source_ids':[source], 'limitations':['No safety claim']}], 'missing_information':['Calibration'], 'next_steps':['Review original source']}


def mock_provider(monkeypatch, outputs):
    calls = []
    async def post(self,*args,**kwargs):
        calls.append(kwargs['json'])
        output = outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return httpx.Response(200,json=output,headers={'content-type':'application/json'},request=httpx.Request('POST','https://example.test'))
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    return calls


def step(id, owner='test-worker'):
    assert claim_job(owner) == id
    asyncio.run(process_job(id,owner))


def test_job_idempotency_scope_and_role_validation():
    value=request()
    first=client.post('/api/v1/agent-jobs',json=value.model_dump())
    assert first.status_code==202
    assert client.post('/api/v1/agent-jobs',json=value.model_dump()).json()['reused'] is True
    assert client.post('/api/v1/agent-jobs',json={**value.model_dump(),'question':'A different research question'}).status_code==409
    assert client.post('/api/v1/agent-jobs',json=request(kind='dataset_review').model_dump()).status_code==422
    assert client.post('/api/v1/agent-jobs',json=request(evidence_ids=['unknown']).model_dump()).status_code==422
    assert client.post('/api/v1/agent-jobs',json={**value.model_dump(),'shell':'rm'}).status_code==422


def test_agent_selects_tool_then_finishes_with_observed_references(monkeypatch):
    live(monkeypatch)
    calls=mock_provider(monkeypatch,[reply('read_evidence',{'evidence_ids':['flex']}),reply('finish',final())])
    id,_=create_job(request())
    step(id)
    assert job(id).status=='queued' and len(job(id).checkpoint)==1
    # A new worker/session resumes the committed checkpoint.
    step(id,'another-worker')
    saved=client.get('/api/v1/agent-jobs/'+id).json()
    assert saved['status']=='succeeded' and saved['calls_used']==2
    assert saved['result']['findings'][0]['source_ids']==['evidence:flex']
    assert len(saved['steps'])==1 and len(saved['calls'])==2
    assert 'Scope is limited' not in calls[0]['input'][0]['content'][0]['text']
    assert 'Flame Extinguishment Experiment' in calls[1]['input'][0]['content'][0]['text']


def test_completed_provider_response_is_reused_after_worker_crash(monkeypatch):
    live(monkeypatch)
    calls=mock_provider(monkeypatch,[reply('read_evidence',{'evidence_ids':['flex']})])
    id,_=create_job(request())
    assert claim_job('crashed-worker')==id
    saved=job(id)
    asyncio.run(request_model(prompt_for(saved),'agent:research',id,0,'crashed-worker',effort='low'))
    with Session.begin() as db:
        db.get(AgentJob,id).lease_until=utcnow()-timedelta(seconds=1)
    step(id,'replacement-worker')
    assert len(calls)==1
    assert job(id).calls_used==1 and len(job(id).checkpoint)==1
    events=client.get('/api/v1/agent-jobs/'+id).json()['events']
    assert any(e['type']=='lease_recovered' for e in events)


def test_rate_limit_retries_are_delayed_bounded_and_counted(monkeypatch):
    live(monkeypatch)
    calls=mock_provider(monkeypatch,[{'code':429,'msg':'Rate limited'},reply('read_evidence',{'evidence_ids':['flex']}),reply('finish',final())])
    id,_=create_job(request())
    step(id)
    assert job(id).status=='retry_wait' and job(id).retries==1
    assert claim_job('too-soon') is None
    with Session.begin() as db:
        db.get(AgentJob,id).available_at=utcnow()-timedelta(seconds=1)
    step(id)
    step(id)
    assert job(id).status=='succeeded' and job(id).calls_used==3
    assert len(calls)==3
    assert budget_snapshot()['reported_credits']==pytest.approx(0.2)


def test_ambiguous_timeout_does_not_repeat_paid_request(monkeypatch):
    live(monkeypatch)
    calls=mock_provider(monkeypatch,[httpx.ReadTimeout('do not expose provider internals')])
    id,_=create_job(request())
    step(id)
    assert job(id).status=='needs_review'
    assert job(id).error_code=='REQUEST_OUTCOME_UNKNOWN'
    assert claim_job('replacement') is None
    assert len(calls)==1 and budget_snapshot()['unknown_calls']==1
    with pytest.raises(ProviderError,match='USAGE_REVIEW_REQUIRED'):
        reserve_call('Other request','explanation')


def test_expired_inflight_lease_is_quarantined(monkeypatch):
    live(monkeypatch)
    id,_=create_job(request())
    assert claim_job('dead')==id
    reserve_call(prompt_for(job(id)),'agent:research',id,0,'dead')
    with Session.begin() as db:
        db.get(AgentJob,id).lease_until=utcnow()-timedelta(seconds=1)
    assert claim_job('new') is None
    assert job(id).status=='needs_review'
    assert budget_snapshot()['unknown_calls']==1


def test_daily_call_admission_is_atomic_across_workers(monkeypatch):
    live(monkeypatch)
    monkeypatch.setenv('AI_DAILY_CALL_LIMIT','3')
    def attempt(i):
        try:
            reserve_call('Prompt '+str(i),'test')
            return 'reserved'
        except ProviderError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(attempt,range(6)))
    assert results.count('reserved')==3
    assert results.count('DAILY_CALL_LIMIT')==3
    assert budget_snapshot()['calls_used_today']==3


def test_credit_reservations_and_reported_spend_block_more_calls(monkeypatch):
    live(monkeypatch)
    monkeypatch.setenv('AI_DAILY_CREDIT_LIMIT','50')
    monkeypatch.setenv('AI_CALL_CREDIT_RESERVE','10')
    id,_=reserve_call('First','test')
    record_call(id,'completed',body={'credits_consumed':45},credits=Decimal(45))
    with pytest.raises(ProviderError,match='DAILY_CREDIT_LIMIT'):
        reserve_call('Second','test')
    assert budget_snapshot()['reported_credits']==45


def test_missing_usage_blocks_future_paid_work(monkeypatch):
    live(monkeypatch)
    mock_provider(monkeypatch,[{'output_text':'{}'}])
    with pytest.raises(ProviderError,match='USAGE_REVIEW_REQUIRED'):
        asyncio.run(request_model('Prompt','test'))
    assert budget_snapshot()['unknown_calls']==1


def test_invalid_or_unobserved_source_output_needs_review(monkeypatch):
    live(monkeypatch)
    calls=mock_provider(monkeypatch,[reply('finish',final('dataset:invented'))])
    id,_=create_job(request())
    step(id)
    assert job(id).status=='needs_review'
    assert job(id).result is None and len(calls)==1


def test_tools_cannot_access_resources_outside_task_scope():
    id,_=create_job(request(evidence_ids=['flex']))
    with pytest.raises(ValueError,match='SOURCE_OUTSIDE_TASK_SCOPE'):
        execute_tool(job(id),'read_evidence',{'evidence_ids':['synthetic-v1']})
    with pytest.raises(ValueError,match='TOOL_NOT_ALLOWED'):
        execute_tool(job(id),'inspect_dataset',{})
    with pytest.raises(ValueError,match='TOOL_NOT_ALLOWED'):
        execute_tool(job(id),'approve_plan',{})


def test_dataset_reviewer_reads_actual_counts_without_calibration_claims():
    dataset=client.post('/api/v1/datasets/nasa/flex-007').json()
    id,_=create_job(request(kind='dataset_review',dataset_id=dataset['id']))
    result=execute_tool(job(id),'inspect_dataset',{})
    assert result['total_rows']==1112
    assert sum(c['missing'] for c in result['channels'])==282
    assert len(result['channels'])==7 and result['verification_eligible'] is False
    assert result['source_ids']==['dataset:'+dataset['id']]
    with pytest.raises(ValueError):
        execute_tool(job(id),'inspect_dataset',{'dataset_id':'another-dataset'})


def test_cancel_during_request_retains_accounting_and_stops_steps(monkeypatch):
    live(monkeypatch)
    id,_=create_job(request())
    async def post(self,*args,**kwargs):
        assert client.post('/api/v1/agent-jobs/'+id+'/cancel').status_code==200
        return httpx.Response(200,json=reply('read_evidence',{'evidence_ids':['flex']}),headers={'content-type':'application/json'},request=httpx.Request('POST','https://example.test'))
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    step(id)
    assert job(id).status=='cancelled' and job(id).checkpoint==[]
    assert budget_snapshot()['reported_credits']==pytest.approx(0.1)
    assert claim_job('new') is None


def test_budget_day_uses_amman_midnight():
    now=utcnow().replace(hour=22,minute=0,second=0,microsecond=0)
    start=day_start(now)
    assert start.hour==21 and start.date()==now.date()
