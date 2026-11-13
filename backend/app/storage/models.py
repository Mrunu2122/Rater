from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RunModel(Base):
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    pdf_sha256 = Column(String, nullable=False, index=True)
    pdf_storage_path = Column(String, nullable=False)
    
    status = Column(String, nullable=False, default="queued", index=True) # queued, extracting, resolving, saved, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Engine & Audit fields
    grid_checksum_sha256 = Column(String, nullable=True)
    resolver_version = Column(String, nullable=True)
    model_id = Column(String, nullable=True)
    raw_extraction_json = Column(Text, nullable=True)
    
    # Structured outputs
    facts = Column(JSON, nullable=True)
    rates = Column(JSON, nullable=True)
    confidence = Column(JSON, nullable=True)
    trace = Column(JSON, nullable=True)
    
    error_message = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
