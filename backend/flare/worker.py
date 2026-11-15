"""A database-locked virtual-clock worker. Each batch is committed atomically."""
import logging
import time
import copy
from sqlalchemy import select
from .db import Session, Run
from .service import advance

log = logging.getLogger('flare.worker')

def tick():
    with Session.begin() as db:
        runs = db.scalars(select(Run).with_for_update(skip_locked=True)).all()
        for run in runs:
            p = run.payload
            if p['status'] == 'running' and p.get('next_tick_at', 0) <= time.time():
                advance(db, run, min(p['duration'], p['t'] + p['speed']))
                run.payload = {**copy.deepcopy(run.payload), 'next_tick_at': int(time.time())+1}
                from .service import add_event
                add_event(db, run, 'measurements_committed', {'through_t': run.payload['t']})


def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        started = time.monotonic()
        try:
            tick()
        except Exception:
            log.exception('Worker batch rolled back; retrying from committed position')
        time.sleep(max(0.05, 1 - (time.monotonic() - started)))

if __name__ == '__main__':
    main()
