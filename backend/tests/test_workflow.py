import json
from fastapi.testclient import TestClient
from sqlalchemy import select
from flare.api import app
from flare.db import Session, Run, Frame, AuditEvent
from flare.service import advance
from flare.worker import tick

client=TestClient(app)


def prepared(preset='manual'):
    scenario=client.post('/api/v1/scenarios',json={'name':'Acceptance test','question':'What happens after visible flame disappears?','investigation_ids':['flex','cool-flames']})
    assert scenario.status_code==201
    sid=scenario.json()['id']
    pack=client.post(f'/api/v1/scenarios/{sid}/evidence',json={'version':1}).json()
    assert pack['explanation']['mode']=='offline'
    p=client.post(f'/api/v1/scenarios/{sid}/plans',json={'version':1}).json()
    assert client.post('/api/v1/runs',json={'plan_ref':p['id']}).status_code==409
    assert client.post(f"/api/v1/plans/{p['id']}/approve",json={}).status_code==200
    run=client.post('/api/v1/runs',json={'plan_ref':p['id'],'preset':preset}).json()
    return run


def finish(run):
    with Session.begin() as db:
        row=db.scalar(select(Run).where(Run.id==run['id']).with_for_update())
        advance(db,row,240)
    return client.get('/api/v1/runs/'+run['id']).json()


def test_three_software_outcomes_from_generator_events():
    reduced=finish(prepared('reduce'))
    stopped=finish(prepared('stop'))
    missing=finish(prepared('data-loss'))
    assert reduced['sample']['flame_presence']==0
    assert reduced['decision']['combustion_status']=='Danger'
    assert stopped['decision']['combustion_status']=='Verified'
    assert stopped['decision']['verified_at']>=60
    assert missing['decision']['combustion_status']=='Uncertain'
    assert missing['decision']['required_quality']=='invalid'


def test_commands_idempotency_worker_resume_and_persistence():
    run=prepared()
    path='/api/v1/runs/'+run['id']
    payload={'command':'start','command_id':'acceptance-start'}
    first=client.post(path+'/commands',json=payload).json()
    assert client.post(path+'/commands',json=payload).json()==first
    assert client.post(path+'/commands',json={**payload,'command':'pause'}).status_code==409
    tick()
    at=client.get(path).json()['t']
    assert at>0
    client.post(path+'/commands',json={'command':'pause','command_id':'acceptance-pause'})
    tick()
    assert client.get(path).json()['t']==at
    # A fresh independent SQLAlchemy session observes the same committed position.
    with Session() as db:
        assert db.get(Run,run['id']).payload['t']==at
        frames=db.scalars(select(Frame).where(Frame.run_id==run['id'])).all()
        assert len(frames)==at+1


def test_branch_preserves_parent_frames_and_future_events_are_independent():
    parent=finish(prepared('reduce'))
    path='/api/v1/runs/'+parent['id']
    snapshot=client.get(path+'/samples').json()
    child=client.post(path+'/branches',json={'name':'Stop instead','parent_t_ms':19000}).json()
    cpath='/api/v1/runs/'+child['id']
    assert child['parent_id']==parent['id']
    assert not child['interventions']
    assert client.post(cpath+'/interventions',json={'option_id':'SIM_STOP_SOURCE'}).status_code==200
    assert finish(child)['decision']['combustion_status']=='Verified'
    assert client.get(path+'/samples').json()==snapshot
    assert client.post(path+'/interventions',json={'option_id':'SIM_STOP_SOURCE'}).status_code==409
    assert client.post(cpath+'/branches',json={'name':'Invalid future','parent_t_ms':250000}).status_code==422


def test_reports_have_sources_and_ordered_event_cursor():
    run=finish(prepared('stop'))
    path='/api/v1/runs/'+run['id']
    report=client.get(path+'/report').json()
    assert report['run']['seed']==42
    assert report['evidence'][0]['url'].startswith('https://')
    assert len(report['frames'])==241
    events=client.get(path+'/events').json()['items']
    seq=[e['seq'] for e in events]
    assert seq==list(range(1,len(seq)+1))
    assert all(e['seq']>2 for e in client.get(path+'/events?after_seq=2').json()['items'])
    assert 'Synthetic demo only' in client.get(path+'/report?format=html').text
    arabic = client.get(path+'/report?format=html&language=ar')
    assert arabic.status_code == 200
    assert 'lang="ar" dir="rtl"' in arabic.text
    assert 'التشغيل والقرار' in arabic.text
    assert 'ليس تقييمًا للسلامة' in arabic.text
    assert 'سياق' in arabic.text
    assert client.get(path+'/report?format=html&language=xx').status_code == 422


def test_filters_comparison_and_schema_rejection():
    assert client.get('/api/v1/investigations?q=قطرة').json()['items']
    assert len(client.get('/api/v1/investigations').json()['items'])==6
    assert client.get('/api/v1/investigations?q=impossiblematch').json()['items']==[]
    assert client.post('/api/v1/comparisons',json={'investigation_ids':['flex','flex']}).status_code==422
    comparison=client.post('/api/v1/comparisons',json={'investigation_ids':['flex','synthetic-v1']}).json()
    assert comparison['quantitative_comparison'] is False
    assert client.post('/api/v1/scenarios',json={'name':'x','question':'question','investigation_ids':['unknown']}).status_code==422


def test_fault_schedule_survives_branch_and_does_not_change_parent():
    run = prepared('stop')
    path = '/api/v1/runs/' + run['id']
    assert client.post(path + '/faults', json={'channel':'co_proxy', 'fault':'freeze'}).status_code == 200
    assert client.post(path + '/faults', json={'channel':'co_proxy', 'fault':'drop'}).status_code == 409
    parent = finish(run)
    assert parent['decision']['required_quality'] == 'invalid'
    child = client.post(path + '/branches', json={'name':'Fault retained', 'parent_t_ms':10000}).json()
    assert child['faults'] == parent['faults']
    assert child['decision']['required_quality'] == 'invalid'
    before = client.post(path + '/branches', json={'name':'Before fault', 'parent_t_ms':0}).json()
    assert before['faults'] == []
    assert client.get(path).json()['faults'] == parent['faults']
