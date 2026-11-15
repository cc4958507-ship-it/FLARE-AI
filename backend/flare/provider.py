"""Shared, durable admission control for every paid Kie request."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import os
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import httpx
from sqlalchemy import select, text
from .db import Session, AgentJob, LLMCall


class ProviderError(Exception):
    def __init__(self, code, retryable=False, uncertain=False):
        super().__init__(code)
        self.code, self.retryable, self.uncertain = code, retryable, uncertain


def utcnow():
    return datetime.now(timezone.utc)


def settings():
    try:
        credits = Decimal(os.getenv('AI_DAILY_CREDIT_LIMIT', '50'))
        reserve = Decimal(os.getenv('AI_CALL_CREDIT_RESERVE', '10'))
        calls = int(os.getenv('AI_DAILY_CALL_LIMIT', '20'))
        tokens = int(os.getenv('AI_MAX_OUTPUT_TOKENS', '1200'))
        if not credits.is_finite() or not reserve.is_finite() or not 0 < reserve <= credits or not 1 <= calls <= 10000 or not 128 <= tokens <= 4096:
            raise ValueError()
        return credits, reserve, calls, tokens
    except (ValueError, InvalidOperation):
        raise ProviderError('BUDGET_CONFIG_ERROR')


def day_start(now):
    name = os.getenv('AI_BUDGET_TIMEZONE', 'Asia/Amman')
    try:
        zone = ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name != 'Asia/Amman':
            raise ProviderError('BUDGET_CONFIG_ERROR')
        zone = timezone(timedelta(hours=3))
    return now.astimezone(zone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def expire_calls(db, now):
    for call in db.scalars(select(LLMCall).where(LLMCall.state == 'in_flight', LLMCall.updated_at < now - timedelta(seconds=120)).with_for_update()):
        call.state, call.error_code, call.updated_at = 'unknown', 'INTERRUPTED_REQUEST', now


def budget_values(db, now):
    limit, reserve, call_limit, tokens = settings()
    calls = db.scalars(select(LLMCall).where(LLMCall.created_at >= day_start(now))).all()
    unknown = db.scalars(select(LLMCall.id).where(
        (LLMCall.state == 'unknown') | ((LLMCall.state == 'completed') & LLMCall.credits.is_(None)))).all()
    spent = sum((c.credits or Decimal(0) for c in calls), Decimal(0))
    held = sum((c.reserved_credits for c in calls if c.state == 'in_flight'), Decimal(0))
    return {'daily_credit_limit':float(limit), 'reported_credits':float(spent),
            'reserved_credits':float(held), 'per_call_reserve':float(reserve),
            'daily_call_limit':call_limit, 'calls_used_today':len(calls),
            'calls_remaining_today':max(0, call_limit-len(calls)),
            'unknown_calls':len(unknown), 'max_output_tokens':tokens,
            'timezone':os.getenv('AI_BUDGET_TIMEZONE', 'Asia/Amman'),
            'billing_guarantee':False}


def budget_snapshot():
    with Session.begin() as db:
        db.execute(text('SELECT pg_advisory_xact_lock(8426101)'))
        expire_calls(db, utcnow())
        db.flush()
        return budget_values(db, utcnow())


def reserve_call(prompt, purpose, job_id=None, step=0, owner=None):
    if os.getenv('AI_MODE', 'offline') != 'live' or not os.getenv('KIE_API_KEY'):
        raise ProviderError('AI_NOT_CONFIGURED')
    if len(prompt) > 20000:
        raise ProviderError('CONTEXT_LIMIT')
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    now = utcnow()
    with Session.begin() as db:
        db.execute(text('SELECT pg_advisory_xact_lock(8426101)'))
        expire_calls(db, now)
        db.flush()
        if job_id:
            job = db.scalar(select(AgentJob).where(AgentJob.id == job_id).with_for_update())
            if not job or job.status != 'running' or job.lease_owner != owner:
                raise ProviderError('JOB_NOT_ACTIVE')
            previous = db.scalars(select(LLMCall).where(LLMCall.job_id == job_id, LLMCall.step == step).order_by(LLMCall.created_at.desc())).all()
            for call in previous:
                if call.prompt_hash != digest:
                    raise ProviderError('CONTEXT_CONFLICT')
                if call.state == 'completed':
                    if call.credits is None:
                        raise ProviderError('USAGE_REVIEW_REQUIRED', uncertain=True)
                    return call.id, call.response
                if call.state in ('in_flight', 'unknown'):
                    raise ProviderError('USAGE_REVIEW_REQUIRED', uncertain=True)
            if job.calls_used >= job.max_calls:
                raise ProviderError('JOB_CALL_LIMIT')
        budget = budget_values(db, now)
        if budget['unknown_calls']:
            raise ProviderError('USAGE_REVIEW_REQUIRED', uncertain=True)
        if budget['calls_used_today'] >= budget['daily_call_limit']:
            raise ProviderError('DAILY_CALL_LIMIT')
        limit, reserve, _, _ = settings()
        if Decimal(str(budget['reported_credits'])) + Decimal(str(budget['reserved_credits'])) + reserve > limit:
            raise ProviderError('DAILY_CREDIT_LIMIT')
        call = LLMCall(id='call_'+uuid4().hex, job_id=job_id, step=step, purpose=purpose,
                       state='in_flight', prompt_hash=digest, reserved_credits=reserve,
                       created_at=now, updated_at=now)
        db.add(call)
        if job_id:
            job.calls_used += 1
            job.updated_at = now
        return call.id, None


def record_call(call_id, state, body=None, code=None, credits=None):
    with Session.begin() as db:
        call = db.get(LLMCall, call_id)
        call.state, call.response, call.error_code = state, body, code
        call.credits, call.updated_at = credits, utcnow()


def reported_credits(body):
    try:
        value = Decimal(str(body['credits_consumed']))
        return value if value.is_finite() and 0 <= value <= 1000000 else None
    except (KeyError, InvalidOperation, TypeError):
        return None


async def request_model(prompt, purpose='explanation', job_id=None, step=0, owner=None, effort='medium'):
    call_id, cached = reserve_call(prompt, purpose, job_id, step, owner)
    if cached is not None:
        return cached
    url = os.getenv('KIE_BASE_URL', 'https://api.kie.ai').rstrip('/') + '/codex/v1/responses'
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=5)) as client:
            response = await client.post(url, headers={'Authorization':'Bearer '+os.environ['KIE_API_KEY']}, json={
                'model':os.getenv('KIE_MODEL', 'gpt-6-1-sol'), 'stream':False,
                'max_output_tokens':settings()[3], 'reasoning':{'effort':effort},
                'input':[{'role':'user', 'content':[{'type':'input_text', 'text':prompt}]}]})
        if len(response.content) > 1000000:
            raise ValueError('Response too large')
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            raise ValueError('Unexpected response')
        code = body.get('code')
        error = body.get('error')
        error_code = error.get('code') if isinstance(error, dict) else None
        status = response.status_code if response.status_code >= 400 else code or error_code
        if status not in (None, 0, 200, '200') or error or body.get('status') in ('failed','incomplete','cancelled'):
            retry = str(status) in ('429', 'rate_limit_exceeded')
            credits = reported_credits(body)
            # Rejected auth/rate-limit requests did not produce model output.
            if credits is None and str(status) in ('401','402','403','429','rate_limit_exceeded'):
                credits = Decimal(0)
            uncertain = credits is None
            record_call(call_id, 'unknown' if uncertain else 'error', body, 'PROVIDER_REJECTED', credits)
            raise ProviderError('PROVIDER_RATE_LIMIT' if retry else 'PROVIDER_REJECTED', retryable=retry and not uncertain, uncertain=uncertain)
        if 'application/json' not in response.headers.get('content-type','') or not body:
            raise ValueError('Unexpected provider response')
        credits = reported_credits(body)
        record_call(call_id, 'completed', body, credits=credits)
        if credits is None:
            raise ProviderError('USAGE_REVIEW_REQUIRED', uncertain=True)
        return body
    except ProviderError:
        raise
    except httpx.ConnectError:
        record_call(call_id, 'error', code='CONNECT_FAILED', credits=Decimal(0))
        raise ProviderError('CONNECT_FAILED', retryable=True) from None
    except (httpx.HTTPError, ValueError):
        record_call(call_id, 'unknown', code='REQUEST_OUTCOME_UNKNOWN')
        raise ProviderError('REQUEST_OUTCOME_UNKNOWN', uncertain=True) from None
