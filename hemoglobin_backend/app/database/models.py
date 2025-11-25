"""
Database models for scan storage.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

Base = declarative_base()


class ScanRecord(Base):
    """Database model for scan records."""
    __tablename__ = "scans"
    
    scan_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Quality metrics
    qc_pass = Column(Boolean)
    qc_sharpness = Column(Float)
    qc_brightness = Column(Float)
    qc_contrast = Column(Float)
    
    # Preprocessing
    tone_cluster = Column(Integer, nullable=True)
    glare_coverage = Column(Float, nullable=True)
    
    # Prediction
    hb_value = Column(Float, nullable=True)
    hb_ci_lower = Column(Float, nullable=True)
    hb_ci_upper = Column(Float, nullable=True)
    uncertainty = Column(Float, nullable=True)
    anemia_stage = Column(String, nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Metadata
    device_model = Column(String, nullable=True)
    model_version = Column(String)
    
    # Full response (JSON)
    response_data = Column(JSON)


# Create engine and session
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
