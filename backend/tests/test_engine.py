import pytest
from fastapi.testclient import TestClient
from flare.api import app
from flare.engine import Action, Event, Sample, Verifier, replay


def test_replay_is_deterministic():
    assert replay(42, 180, [Event(20, Action.STOP)]) == replay(42, 180, [Event(20, Action.STOP)])


def test_actions_change_future_and_produce_distinct_endings():
    reduced = replay(42, 200, [Event(20, Action.REDUCE)])
    stopped = replay(42, 200, [Event(20, Action.STOP)])
    assert reduced['samples'][:20] == stopped['samples'][:20]
    assert reduced['samples'][21] != stopped['samples'][21]
    assert reduced['samples'][-1]['flame_presence'] == 0
    assert reduced['decisions'][-1]['combustion_status'] == 'Danger'
    assert stopped['decisions'][-1]['combustion_status'] == 'Verified'
    assert next(d['t'] for d in stopped['decisions'] if d['combustion_status'] == 'Verified') > 60


def test_data_loss_does_not_clear_danger():
    result = replay(42, 180, [Event(20, Action.STOP)], fault_at=25)
    assert result['decisions'][-1]['combustion_status'] == 'Danger'
    assert result['decisions'][-1]['reason_codes'] == ['DANGER_LATCHED_DATA_LOSS']


def test_fault_without_previous_danger_is_uncertain():
    assert replay(42, 180, [Event(0, Action.STOP)], fault_at=0)['decisions'][-1]['combustion_status'] == 'Uncertain'


def test_lost_data_revokes_current_verification_but_preserves_history():
    result = replay(42, 240, [Event(0, Action.STOP)], fault_at=200)
    assert result['decisions'][199]['combustion_status'] == 'Verified'
    assert result['decisions'][-1]['combustion_status'] == 'Uncertain'
    assert result['decisions'][-1]['verified_at'] is not None


def test_scope_cannot_verify_real_measurements():
    engine = Verifier()
    for t in range(100):
        decision = engine.evaluate(Sample(t, 0, 0, 0, 1, 0), scope='NASA-raw')
    assert decision['combustion_status'] == 'Uncertain'


def test_duplicate_time_rejected():
    engine = Verifier()
    sample = Sample(0, 0, 0, 0, 1, 0)
    engine.evaluate(sample)
    with pytest.raises(ValueError):
        engine.evaluate(sample)


@pytest.mark.parametrize('kind', ['drop', 'freeze', 'replay', 'skew', 'saturation'])
def test_advanced_faults_revoke_verification_and_are_reproducible(kind):
    faults = [{'t':200, 'channel':'co_proxy', 'fault':kind}]
    result = replay(42, 240, [Event(0, Action.STOP)], faults=faults)
    assert result == replay(42, 240, [Event(0, Action.STOP)], faults=faults)
    assert result['decisions'][199]['combustion_status'] == 'Verified'
    assert result['decisions'][200]['combustion_status'] == 'Uncertain'
    assert result['decisions'][240]['required_quality'] == 'invalid'
    assert result['samples'][200]['quality_flags'] == ('co_proxy:' + kind,)


def test_stable_values_alone_are_not_a_freeze_fault():
    verifier = Verifier()
    for t in range(100):
        decision = verifier.evaluate(Sample(t, 0, 0, 0, 1, 0))
    assert decision['combustion_status'] == 'Verified'


def test_api_validation_and_replay():
    client = TestClient(app)
    assert client.get('/api/v1/health').json()['mode'] == 'synthetic'
    assert client.post('/api/v1/replays', json={'duration': -1}).status_code == 422
    assert client.post('/api/v1/replays', json={'hardware': True}).status_code == 422
    response = client.post('/api/v1/replays', json={'events': [{'t': 20, 'action': 'SIM_STOP_SOURCE'}]})
    assert response.status_code == 200
    assert response.json()['decisions'][-1]['combustion_status'] == 'Verified'
