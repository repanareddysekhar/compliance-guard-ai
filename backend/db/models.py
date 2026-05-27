from sqlalchemy import Column, String, DateTime, Integer, Numeric, ARRAY, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .database import Base

class ScanRun(Base):
    __tablename__ = "scan_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String, nullable=False)
    repo_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    standards = Column(ARRAY(String))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    services_scanned = Column(Integer, default=0)
    violations_found = Column(Integer, default=0)
    auto_fixed = Column(Integer, default=0)
    compliance_score = Column(Numeric(5, 2))

class Violation(Base):
    __tablename__ = "violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scan_runs.id", ondelete="CASCADE"))
    service = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String)
    line_number = Column(Integer)
    remediation = Column(Text, nullable=False)
    opa_policy_ref = Column(String)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scan_runs.id", ondelete="CASCADE"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    agent = Column(String, nullable=False)
    tool_called = Column(String, nullable=False)
    intent = Column(Text)
    policy_decision = Column(String, nullable=False)
    input_hash = Column(String)
    output_hash = Column(String)
    signature = Column(String)
