"""Operator-only reconciliation after checking a request in the Kie billing ledger."""
import argparse
from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from .db import Session, LLMCall, AgentJob
from .agents import event
from .provider import utcnow


def reconcile(call_id, credits, reference):
    try:
        amount = Decimal(str(credits))
        if not amount.is_finite() or not 0 <= amount <= 1000000:
            raise ValueError('Invalid credit amount')
    except InvalidOperation:
        raise ValueError('Invalid credit amount') from None
    if not 5 <= len(reference.strip()) <= 200:
        raise ValueError('A billing-ledger reference is required')
    with Session.begin() as db:
        call = db.scalar(select(LLMCall).where(LLMCall.id == call_id).with_for_update())
        if not call or not (call.state == 'unknown' or (call.state == 'completed' and call.credits is None)):
            raise ValueError('Only unresolved calls can be reconciled')
        call.credits, call.updated_at = amount, utcnow()
        call.state = 'completed' if call.response and call.response.get('status') == 'completed' else 'error'
        call.error_code = 'MANUALLY_RECONCILED'
        call.response = {**(call.response or {}), '_reconciliation':{'reference':reference, 'at':utcnow().isoformat(), 'credits':str(amount)}}
        if call.job_id:
            job = db.scalar(select(AgentJob).where(AgentJob.id == call.job_id).with_for_update())
            event(db, job, 'billing_reconciled', call_id=call.id, credits=str(amount), reference=reference)
        # Reconciliation never requeues an uncertain task or repeats a paid call.


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--call', required=True)
    parser.add_argument('--credits', required=True)
    parser.add_argument('--billing-reference', required=True)
    args = parser.parse_args()
    reconcile(args.call, args.credits, args.billing_reference)
    print('Usage reconciled. Task remains stopped for review.')
