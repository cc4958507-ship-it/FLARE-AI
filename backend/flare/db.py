import os
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Integer, String, ForeignKey, Text, Float, LargeBinary, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://flare:flare_local_demo@127.0.0.1:5432/flare')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = 'records'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Run(Base):
    __tablename__ = 'runs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Frame(Base):
    __tablename__ = 'frames'
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id'), primary_key=True)
    t: Mapped[int] = mapped_column(Integer, primary_key=True)
    sample: Mapped[dict] = mapped_column(JSON)
    decision: Mapped[dict] = mapped_column(JSON)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id'), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Dataset(Base):
    __tablename__ = 'datasets'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manifest: Mapped[dict] = mapped_column(JSON)
    raw_csv: Mapped[str] = mapped_column(Text)
    report: Mapped[dict] = mapped_column(JSON)


class Measurement(Base):
    __tablename__ = 'measurements'
    dataset_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'), primary_key=True)
    channel: Mapped[str] = mapped_column(String(120), primary_key=True)
    sensor_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    t_rel_ms: Mapped[int] = mapped_column(Integer)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class DatasetArtifact(Base):
    __tablename__ = 'dataset_artifacts'
    dataset_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class SourceObservation(Base):
    __tablename__ = 'source_observations'
    dataset_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    t_rel_ms: Mapped[int] = mapped_column(Integer)
    source_time: Mapped[str] = mapped_column(String(64))
    values_json: Mapped[list] = mapped_column(JSON)
    original_values: Mapped[list] = mapped_column(JSON)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class ResearchAsset(Base):
    __tablename__ = 'research_assets'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class AgentJob(Base):
    __tablename__ = 'agent_jobs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), index=True)
    input: Mapped[dict] = mapped_column(JSON)
    checkpoint: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    max_calls: Mapped[int] = mapped_column(Integer)
    calls_used: Mapped[int] = mapped_column(Integer, default=0)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AgentEvent(Base):
    __tablename__ = 'agent_events'
    job_id: Mapped[str] = mapped_column(ForeignKey('agent_jobs.id'), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class LLMCall(Base):
    __tablename__ = 'llm_calls'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey('agent_jobs.id'), index=True, nullable=True)
    step: Mapped[int] = mapped_column(Integer, default=0)
    purpose: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(24))
    prompt_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    credits: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    reserved_credits: Mapped[float] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
