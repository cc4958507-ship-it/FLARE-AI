import hashlib
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from flare.api import app
from flare.nasa_flex import BUNDLE, load_flex


def test_real_source_units_time_origin_missing_values_and_provenance():
    manifest, report, csv_text, artifacts = load_flex()
    assert manifest['doi'] == '10.60555/mbq8-0451'
    assert manifest['license'] == 'CC0-1.0'
    assert len(report['channels']) == 7
    assert report['accepted_rows'] == 3 * 141 + 158 + 3 * 177
    assert report['missing_rows'] >= 282
    first = report['accepted'][0]
    assert first['t_rel_ms'] == 0
    assert float(first['source_time_sec']) < 0
    assert first['value'] == pytest.approx(0.0018532650143266)
    assert first['source_line'] == 2
    assert first['source_column'] == 'DropletDiameter_mm'
    assert first['unit'] == 'm' and first['original_unit'] == 'mm'
    assert report['accepted'][1]['value'] is None
    assert report['accepted'][1]['quality'] == 'missing'
    assert report['verification_eligible'] is False
    assert report['mode'] == 'Replay Only'
    assert len(report['excluded_columns']) == 2
    assert len(artifacts) == 6
    assert 'nan' not in csv_text.lower()


def test_checksum_failure_prevents_import(tmp_path):
    shutil.copytree(BUNDLE, tmp_path / 'bundle')
    (tmp_path / 'bundle' / 'FLEX-007_DropletData.txt').write_bytes(b'changed')
    with pytest.raises(ValueError, match='checksum'):
        load_flex(tmp_path / 'bundle')


def test_invalid_source_times_rejected_even_with_updated_checksum(tmp_path):
    root = tmp_path / 'bundle'
    shutil.copytree(BUNDLE, root)
    name = 'FLEX-007_DropletData.txt'
    data = (root / name).read_text().splitlines()
    data[2] = data[1]
    content = ('\n'.join(data) + '\n').encode()
    (root / name).write_bytes(content)
    manifest = json.loads((root / 'manifest.json').read_text())
    for f in manifest['files']:
        if f['name'] == name:
            f.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    (root / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='Non-increasing'):
        load_flex(root)


def test_nasa_import_is_persisted_idempotent_and_originals_roundtrip():
    client = TestClient(app)
    first = client.post('/api/v1/datasets/nasa/flex-007')
    assert first.status_code == 201
    dataset_id = first.json()['id']
    second = client.post('/api/v1/datasets/nasa/flex-007')
    assert second.json()['id'] == dataset_id
    assert second.json()['reused'] is True
    restored = client.get('/api/v1/datasets/' + dataset_id + '?limit=10000').json()
    assert len(restored['items']) == first.json()['report']['accepted_rows']
    assert restored['report']['verification_eligible'] is False
    for entry in first.json()['manifest']['files']:
        raw = client.get(f'/api/v1/datasets/{dataset_id}/artifacts/' + entry['name'])
        assert raw.status_code == 200
        assert raw.content == (BUNDLE / entry['name']).read_bytes()
        assert hashlib.sha256(raw.content).hexdigest() == entry['sha256']
    assert client.get(f'/api/v1/datasets/{dataset_id}/artifacts/no-such-file').status_code == 404
