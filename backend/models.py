import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String

from db import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class SessionRecord(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    consented_at = Column(DateTime, default=datetime.utcnow)
    consent_version = Column(String, nullable=False)


class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    encrypted_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class FieldRecord(Base):
    __tablename__ = "fields"
    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String, nullable=False)
    extracted_value = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    source_box = Column(JSON, nullable=True)
    confirmed_value = Column(String, nullable=True)
    confirmed = Column(Boolean, default=False)
    corrected_at = Column(DateTime, nullable=True)


class AuditLogRecord(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    action = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    rule_version = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
