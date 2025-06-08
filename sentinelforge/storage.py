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
    Boolean,
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

    # Enhanced fields for IOC management
    severity = Column(
        String, nullable=False, default="medium"
    )  # low, medium, high, critical
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    confidence = Column(Integer, nullable=False, default=50)  # 0-100 confidence score
    created_by = Column(Integer, nullable=True)  # User ID who created this IOC
    updated_by = Column(Integer, nullable=True)  # User ID who last updated this IOC
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    is_active = Column(Boolean, default=True)  # Soft delete flag

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


class IOCAuditLogEntry(Base):
    __tablename__ = "ioc_audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ioc_type = Column(String, nullable=False)  # IOC type
    ioc_value = Column(String, nullable=False)  # IOC value
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, IMPORT
    user_id = Column(Integer, nullable=False)  # User who performed the action
    changes = Column(JSON, nullable=True)  # JSON of what changed
    justification = Column(Text, nullable=True)  # Reason for the change
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Additional metadata
    source_ip = Column(String, nullable=True)  # IP address of the user
    user_agent = Column(String, nullable=True)  # User agent string


class ThreatFeed(Base):
    __tablename__ = "threat_feeds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)  # URL for remote feeds
    feed_type = Column(String(50), nullable=False)  # csv, json, txt, stix
    format_config = Column(JSON, nullable=True)  # Field mappings and parsing config
    is_active = Column(Boolean, default=True)
    auto_import = Column(Boolean, default=False)  # Enable automatic imports
    import_frequency = Column(Integer, default=24)  # Hours between auto imports
    last_import = Column(DateTime, nullable=True)
    last_import_status = Column(String(50), nullable=True)  # success, error, pending
    last_import_count = Column(Integer, default=0)
    created_by = Column(Integer, nullable=False)  # User ID who created the feed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class FeedImportLog(Base):
    __tablename__ = "feed_import_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_id = Column(
        Integer, ForeignKey("threat_feeds.id"), nullable=True
    )  # Null for manual uploads
    feed_name = Column(String(200), nullable=False)  # Feed name for reference
    import_type = Column(String(50), nullable=False)  # manual, automatic, scheduled
    file_name = Column(String(255), nullable=True)  # Original filename
    file_size = Column(Integer, nullable=True)  # File size in bytes
    total_records = Column(Integer, default=0)  # Total records in file
    imported_count = Column(Integer, default=0)  # Successfully imported
    skipped_count = Column(Integer, default=0)  # Skipped (duplicates)
    error_count = Column(Integer, default=0)  # Failed imports
    errors = Column(JSON, nullable=True)  # Array of error messages
    import_status = Column(String(50), nullable=False)  # success, partial, failed
    duration_seconds = Column(Integer, nullable=True)  # Import duration
    user_id = Column(Integer, nullable=False)  # User who triggered import
    justification = Column(Text, nullable=True)  # Reason for import
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationship to feed
    feed = relationship("ThreatFeed", backref="import_logs")


def init_db():
    # Pass engine explicitly if Base.metadata needs it
    Base.metadata.create_all(bind=engine)
