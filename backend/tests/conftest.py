"""Integration tests use a separate PostgreSQL database, never the app database."""
import os
from pathlib import Path
import subprocess
import sys
import psycopg
import pytest
from sqlalchemy.engine import make_url

if 'TEST_DATABASE_URL' not in os.environ:
    connection=psycopg.connect('postgresql://flare:flare_local_demo@127.0.0.1:5432/postgres',autocommit=True)
    with connection:
        if not connection.execute("SELECT 1 FROM pg_database WHERE datname='flare_test'").fetchone():
            connection.execute('CREATE DATABASE flare_test')
    os.environ['DATABASE_URL']='postgresql+psycopg://flare:flare_local_demo@127.0.0.1:5432/flare_test'
else:
    os.environ['DATABASE_URL']=os.environ['TEST_DATABASE_URL']
database_name = make_url(os.environ['DATABASE_URL']).database or ''
if not (database_name.endswith('_test') or database_name.startswith('test_')):
    raise RuntimeError('Backend tests require a dedicated database named test_* or *_test')
subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=Path(__file__).parents[1],check=True)


@pytest.fixture(autouse=True)
def isolate_agent_accounting(monkeypatch):
    monkeypatch.setenv('AI_MODE', 'offline')
    monkeypatch.setenv('KIE_API_KEY', '')
    from sqlalchemy import delete
    from flare.db import Session, LLMCall, AgentEvent, AgentJob
    # Only the guarded dedicated test database is touched.
    with Session.begin() as db:
        for model in (LLMCall, AgentEvent, AgentJob):
            db.execute(delete(model))
    monkeypatch.setenv('AI_DAILY_CALL_LIMIT', '10000')
    monkeypatch.setenv('AI_DAILY_CREDIT_LIMIT', '100000')
    monkeypatch.setenv('AI_CALL_CREDIT_RESERVE', '1')
