"""
SQLAlchemy models for the nextcloud-ingestor state management.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ActivityState(Base):
    """
    Tracks the last processed activity ID and timestamp for incremental updates.
    """
    __tablename__ = 'activity_state'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_activity_id = Column(Integer, nullable=False, default=0)
    last_check_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ActivityState(id={self.id}, last_activity_id={self.last_activity_id}, last_check={self.last_check_timestamp})>"


def create_database_engine(config):
    """Create a SQLAlchemy engine from config."""
    database_url = f"postgresql://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}"
    engine = create_engine(database_url, echo=False)
    return engine


def create_session_factory(engine):
    """Create a sessionmaker from an engine."""
    return sessionmaker(bind=engine)


def create_tables(engine):
    """Create all tables defined by the models."""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables defined by the models."""
    Base.metadata.drop_all(engine)