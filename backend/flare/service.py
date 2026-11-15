import copy
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, func
from .db import Record, Run, Frame, AuditEvent
from .engine import Action, Event, replay


def uid(prefix):
    return prefix + '_' + uuid4().hex[:12]


def now():
    return datetime.now(timezone.utc).isoformat()


def add_event(db, run, kind, detail):
    seq = db.scalar(select(func.max(AuditEvent.seq)).where(AuditEvent.run_id == run.id)) or 0
    value = {'seq': seq + 1, 'type': kind, 't': run.payload['t'], 'created_at': now(), **detail}
    db.add(AuditEvent(run_id=run.id, seq=seq + 1, payload=value))
    db.flush()
    return value


def advance(db, run, target):
    p = copy.deepcopy(run.payload)
    result = replay(p['seed'], target, [Event(e['t'], Action(e['action'])) for e in p['interventions']], p.get('fault_at'), p.get('faults', []))
    previous = p.get('decision', {}).get('combustion_status')
    for t in range(p['t'] + 1, target + 1):
        sample, decision = result['samples'][t], result['decisions'][t]
        db.add(Frame(run_id=run.id, t=t, sample=sample, decision=decision))
        p['t'] = t
        run.payload = copy.deepcopy(p)
        if decision['combustion_status'] != previous:
            add_event(db, run, 'decision_changed', {'decision': decision})
            previous = decision['combustion_status']
    p['t'] = target
    p['decision'] = result['decisions'][target]
    p['sample'] = result['samples'][target]
    p['updated_at'] = now()
    if target >= p['duration']:
        p['status'] = 'completed'
    run.payload = copy.deepcopy(p)
    run.revision += 1
    return p


def create_run(db, plan, seed=42, name=None, duration=240, parent=None, branch_t=0, preset='manual'):
    p = {'name': name or 'Droplet observation', 'seed': seed, 'duration': duration,
         'status': 'ready', 'speed': 4, 't': -1, 'clock_mode': 'replay',
         'profile': 'synthetic-v1', 'plan_id': plan.id, 'scenario_id': plan.payload['scenario_id'],
         'interventions': [], 'fault_at': None, 'faults': [], 'created_at': now(), 'updated_at': now(),
         'parent_id': parent.id if parent else None, 'branch_t': branch_t if parent else None,
         'provenance': 'synthetic', 'engine_version': '0.1.0'}
    if not parent:
        if preset in ('reduce', 'stop'):
            p['interventions'] = [{'t':20, 'action':Action.REDUCE.value if preset == 'reduce' else Action.STOP.value}]
        elif preset == 'data-loss':
            p['interventions'] = [{'t':0, 'action':Action.STOP.value}]
            p['fault_at'] = 0
    if parent:
        p['faults'] = [copy.deepcopy(f) for f in parent.payload.get('faults', []) if f['t'] <= branch_t]
        p['interventions'] = [copy.deepcopy(e) for e in parent.payload['interventions'] if e['t'] <= branch_t]
        f = parent.payload.get('fault_at')
        p['fault_at'] = f if f is not None and f <= branch_t else None
    run = Run(id=uid('run'), payload=p)
    db.add(run)
    db.flush()
    add_event(db, run, 'run_created', {'parent_id': p['parent_id'], 'seed': seed})
    advance(db, run, branch_t if parent else 0)
    return run
