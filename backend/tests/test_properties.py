from hypothesis import given, strategies as st, settings
from flare.engine import replay, Event, Action

@given(st.integers(min_value=0,max_value=100000),st.integers(min_value=1,max_value=50))
@settings(max_examples=20,deadline=None)
def test_any_seed_replay_is_identical_and_stop_event_eventually_verifies(seed, at):
    result=replay(seed,240,[Event(at,Action.STOP)])
    assert result==replay(seed,240,[Event(at,Action.STOP)])
    assert result['decisions'][-1]['combustion_status']=='Verified'
    assert all(0<=s['thermal_excess']<=1 for s in result['samples'])
