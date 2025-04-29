import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Import settings
from sentinelforge.settings import settings

# DATABASE_URL = "sqlite:///./ioc_store.db" # Use settings

# Use URL from settings
engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


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


def init_db():
    # Pass engine explicitly if Base.metadata needs it
    Base.metadata.create_all(bind=engine)
