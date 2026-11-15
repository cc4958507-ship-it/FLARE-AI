import pytest
from fastapi.testclient import TestClient
from flare.api import app
from flare.ingestion import parse_csv

HEADER = 'channel,sensor_id,seq,t_rel_ms,value,unit\n'


def test_normalization_missing_quarantine_and_duplicates():
    raw = HEADER + 'temperature,s1,0,0,20,degC\ntemperature,s1,1,1000,,degC\ntemperature,s1,1,1000,,degC\ntemperature,s1,2,900,25,degC\nunknown,s2,0,0,7,mystery\n'
    result = parse_csv(raw)
    assert result['accepted_rows'] == 2
    assert result['accepted'][0]['value'] == pytest.approx(293.15)
    assert result['accepted'][1]['value'] is None
    assert result['accepted'][1]['quality'] == 'missing'
    assert result['quarantined_rows'] == 2
    assert result['duplicate_rows'] == 1
    assert result['verification_eligible'] is False


@pytest.mark.parametrize('rows', ['c,s,0,0,nan,K\n', 'c,s,0,0,inf,K\n', 'c,s,0,0,1,K\nc,s,0,0,2,K\n'])
def test_invalid_import_is_rejected_atomically(rows):
    with pytest.raises(ValueError):
        parse_csv(HEADER + rows)


def test_dataset_persistence_idempotency_and_raw_roundtrip():
    client = TestClient(app)
    raw = HEADER + 'temperature,s1,0,0,20,degC\n'
    payload = {'title':'Test fixture, not NASA measurements', 'source_url':'https://example.org/fixture',
               'license':'Test fixture', 'origin':'synthetic', 'csv_text':raw}
    first = client.post('/api/v1/datasets', json=payload)
    assert first.status_code == 201
    dataset_id = first.json()['id']
    assert client.post('/api/v1/datasets', json=payload).json()['reused'] is True
    restored = client.get('/api/v1/datasets/' + dataset_id).json()
    assert restored['items'][0]['value'] == pytest.approx(293.15)
    assert restored['manifest']['review_status'] == 'unreviewed'
    assert client.get('/api/v1/datasets/' + dataset_id + '/raw').text == raw
    assert client.post('/api/v1/datasets', json={**payload, 'csv_text':HEADER+'c,s,0,0,nan,K\n'}).status_code == 422
