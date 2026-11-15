import hashlib
import json
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from flare.api import app
from flare.db import Session,Dataset,SourceObservation,ResearchAsset
from flare.research_data import parse_native,import_library,asset_path,library_root
from flare.agents import JobRequest,create_job,execute_tool,validate_note
from flare.db import AgentJob

client=TestClient(app)


def source(kind='acme',extra=''):
    if kind=='acme':
        header='Time,'+','.join('sensor'+str(i) for i in range(35))
        return ('2019-02-25,Test Point: 19056A2\n'+header+'\n15:00:00:000,'+','.join(['-0.25']*35)+'\n15:00:00:010,'+','.join(['1']*35)+'\n'+extra).encode()
    header='FCU TimeStamp,'+','.join(f'pressure{i}(PSIA)' if i else 'temperature(Deg C)' for i in range(128))
    values=','.join(['20']+['1']*127)
    return (header+'\n2013-02-08 23:04:38.000000,'+values+'\n2013-02-08 23:04:38.000000,'+values+'\n').encode()


def test_unresolved_units_and_negative_source_values_are_not_reinterpreted():
    raw,rows,report=parse_native(source(),'19056A2_data.csv')
    assert len(rows)==2 and report['accepted_rows']==70
    assert rows[0]['values_json'][0]==-0.25
    assert rows[0]['original_values'][0]=='-0.25'
    assert report['channels'][0]['unit']=='unresolved'
    assert report['channels'][0]['mean']==0.375
    assert rows[1]['t_rel_ms']==10 and report['verification_eligible'] is False


def test_explicit_chamber_units_and_duplicate_clocks_are_preserved():
    _,rows,report=parse_native(source('chamber'),'C039H03_Chamber_Readings.txt')
    assert rows[0]['values_json'][0]==pytest.approx(293.15)
    assert rows[0]['values_json'][1]==pytest.approx(6894.757293168)
    assert rows[0]['original_values'][0]=='20'
    assert len(rows)==2 and rows[0]['t_rel_ms']==rows[1]['t_rel_ms']==0
    assert report['duplicate_timestamp_rows']==1
    assert all('duplicate_source_timestamp' in r['metadata_json']['flags'] for r in rows)
    assert report['calibration_status']=='unverified'


@pytest.mark.parametrize('value',[b'nan',b'inf',b'bad'])
def test_invalid_native_values_cannot_be_imported(value):
    with pytest.raises(ValueError):
        parse_native(source().replace(b'-0.25',value,1),'19056A2_data.csv')


def test_library_path_and_checksum_guard(tmp_path):
    with pytest.raises(ValueError):
        asset_path({'object':'../outside'},tmp_path)
    data=source()
    digest=hashlib.sha256(data).hexdigest()
    (tmp_path/'objects').mkdir()
    (tmp_path/'objects'/digest).write_bytes(data+b'changed')
    (tmp_path/'manifest.json').write_text(json.dumps({'assets':[{'id':digest,'object':'objects/'+digest,'name':'19056A2_data.csv','bytes':len(data)}]}))
    with pytest.raises(ValueError,match='checksum'):
        import_library(tmp_path)


@pytest.fixture(scope='module')
def imported():
    if not (library_root()/'manifest.json').exists():
        pytest.skip('User-supplied research_data library is not mounted')
    result=import_library()
    assert result['assets']==80
    return result


def test_real_native_import_paging_sampling_and_original_download(imported):
    expected={'19056A2_data.csv':(31316,1096060),'19056D2_data.csv':(30841,1079435),'C039H03_Chamber_Readings.txt':(489,62592)}
    for item in imported['datasets']:
        assert (item['observation_rows'],item['measurement_rows'])==expected[item['name']]
        detail=client.get('/api/v1/datasets/'+item['id']+'?limit=1').json()
        channel=detail['channels'][0]['channel']
        last=client.get('/api/v1/datasets/'+item['id'],params={'channel':channel,'offset':item['observation_rows']-1,'limit':25}).json()
        assert last['items'][0]['seq']==item['observation_rows']-1
        assert last['page']['total']==item['observation_rows']
        overview=client.get('/api/v1/datasets/'+item['id']+'/series',params={'channel':channel,'max_points':100}).json()
        assert len(overview['items'])<=101 and overview['total']==item['observation_rows']
        assert overview['items'][-1]['seq']==item['observation_rows']-1
        assert client.get('/api/v1/datasets/'+item['id'],params={'channel':'not-present'}).status_code==404
        raw=client.get('/api/v1/datasets/'+item['id']+'/artifacts/'+item['name'])
        assert raw.status_code==200
        assert hashlib.sha256(raw.content).hexdigest()==detail['manifest']['source_asset_id']


def test_real_library_is_idempotent_and_mixed_sources_are_distinct(imported):
    repeated=import_library()
    assert all(d['reused'] for d in repeated['datasets'])
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(SourceObservation))==62646
    library=client.get('/api/v1/research-files').json()
    assert library['total']==80
    assert all('object' not in a for a in library['items'])
    mixed=client.get('/api/v1/research-files',params={'category':'mixed_experiment_and_model'}).json()['items']
    assert len(mixed)==4
    assert not any(d['name'].startswith('PSI-117') for d in imported['datasets'])
    assert client.get('/api/v1/research-files/not-present/download').status_code==404


def test_agent_uses_complete_native_statistics_not_first_10000_measurements(imported):
    entry=next(d for d in imported['datasets'] if d['name']=='19056A2_data.csv')
    id,_=create_job(JobRequest(kind='dataset_review',question='Review every source record and unresolved units.',dataset_id=entry['id'],idempotency_key=uuid4().hex))
    with Session() as db:
        job=db.get(AgentJob,id)
    result=execute_tool(job,'inspect_dataset',{})
    assert result['examined_rows']==1096060
    assert len(result['channels'])==35 and result['channels'][0]['rows']==31316
    assert result['channels'][0]['unit']=='unresolved'
    assert result['verification_eligible'] is False
    assert result['dataset_counts']=={'source_records':31316,'channels':35,'measurement_values':1096060}
    selected=execute_tool(job,'inspect_dataset',{'channel':result['channels'][0]['channel']})
    assert selected['examined_rows']==31316 and len(selected['channels'])==1
    with pytest.raises(ValueError):
        execute_tool(job,'inspect_dataset',{'channel':'not-present'})
    job.checkpoint=[{'action':'inspect_dataset','result':result}]
    note={'summary':'Source-scale values remain uncalibrated.','findings':[{'text':'Units are unresolved.','source_ids':['dataset:'+entry['id']],'limitations':['No calibration']}],'missing_information':[],'next_steps':[]}
    with pytest.raises(ValueError,match='SOURCE_COUNT_MISMATCH'):
        validate_note(job,note)
    note['dataset_counts']={'source_records':1096060,'channels':35,'measurement_values':1096060}
    with pytest.raises(ValueError,match='SOURCE_COUNT_MISMATCH'):
        validate_note(job,note)
    note['dataset_counts']=result['dataset_counts']
    assert validate_note(job,note)['dataset_counts']['source_records']==31316
