import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Integer,
    JSON,
    Text,
    Table,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Import settings
from sentinelforge.settings import settings

# DATABASE_URL = "sqlite:///./ioc_store.db" # Use settings

# Use URL from settings
engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Junction table for many-to-many relationship between Alerts and IOCs
ioc_alert_association = Table(
    "ioc_alert",
    Base.metadata,
    Column("alert_id", Integer, ForeignKey("alerts.id"), primary_key=True),
    Column("ioc_type", String, ForeignKey("iocs.ioc_type"), primary_key=True),
    Column("ioc_value", String, ForeignKey("iocs.ioc_value"), primary_key=True),
)


class IOC(Base):
    __tablename__ = "iocs"
    ioc_type = Column(String, primary_key=True)
    ioc_value = Column(String, primary_key=True)
    source_feed = Column(String, nullable=False)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    score = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=False, default="low")
    enrichment_data = Column(JSON, nullable=True)
    summary = Column(String, nullable=True)
    explanation_data = Column(JSON, nullable=True)  # SHAP explanation data

    # Relationship to alerts
    alerts = relationship(
        "Alert", secondary=ioc_alert_association, back_populates="iocs"
    )


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    formatted_time = Column(String(50), nullable=True)  # Human-readable time
    threat_type = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False, default="medium")
    confidence = Column(Integer, nullable=False, default=50)  # 0-100
    risk_score = Column(Integer, nullable=False, default=50)  # 0-100 risk assessment
    overridden_risk_score = Column(Integer, nullable=True)  # 0-100 analyst override
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationship to IOCs
    iocs = relationship("IOC", secondary=ioc_alert_association, back_populates="alerts")


class AuditLogEntry(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # User identifier
    original_score = Column(Integer, nullable=False)  # Original risk score
    override_score = Column(Integer, nullable=False)  # New overridden score
    justification = Column(Text, nullable=True)  # Reason for override
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationship to Alert
    alert = relationship("Alert", backref="audit_logs")


def init_db():
    # Pass engine explicitly if Base.metadata needs it
    Base.metadata.create_all(bind=engine)
