import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./ioc_store.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
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


def init_db():
    Base.metadata.create_all(engine)
