import datetime
from typing import Optional
from sqlalchemy.orm import Session
from config import Config
from database import create_database_engine, create_session_factory, create_tables, ActivityState
from utils import logger


class StateManager:
    """Manages activity tracking state in PostgreSQL using SQLAlchemy."""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = create_database_engine(config)
        self.SessionFactory = create_session_factory(self.engine)
        logger.info(f"Initialized SQLAlchemy engine for {config.postgres_host}:{config.postgres_port}/{config.postgres_db}")
    
    def initialize_schema(self):
        """Create the necessary tables for state management."""
        try:
            create_tables(self.engine)
            
            # Ensure we have exactly one row for activity state
            with self.SessionFactory() as session:
                count = session.query(ActivityState).count()
                if count == 0:
                    initial_state = ActivityState(
                        last_activity_id=0,
                        last_check_timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    session.add(initial_state)
                    session.commit()
                    logger.info("Initialized activity_state table with default values")
                
            logger.info("PostgreSQL schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise
    
    def get_last_activity_state(self) -> tuple[int, datetime.datetime]:
        """Get the last processed activity ID and timestamp."""
        try:
            with self.SessionFactory() as session:
                activity_state = session.query(ActivityState).order_by(ActivityState.id.desc()).first()
                
                if activity_state:
                    return activity_state.last_activity_id, activity_state.last_check_timestamp
                else:
                    # Fallback if no state exists - return UTC timezone-aware datetime
                    return 0, datetime.datetime.now(datetime.timezone.utc)
        except Exception as e:
            logger.error(f"Failed to get last activity state: {e}")
            raise
    
    def update_activity_state(self, activity_id: int, timestamp: Optional[datetime.datetime] = None):
        """Update the last processed activity ID and timestamp."""
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            with self.SessionFactory() as session:
                # Get the most recent activity state record
                activity_state = session.query(ActivityState).order_by(ActivityState.id.desc()).first()
                
                if activity_state:
                    # Update existing record
                    activity_state.last_activity_id = activity_id
                    activity_state.last_check_timestamp = timestamp
                    activity_state.updated_at = datetime.datetime.now(datetime.timezone.utc)
                else:
                    # Create new record if none exists
                    logger.warning("No activity_state record found to update, creating new one")
                    activity_state = ActivityState(
                        last_activity_id=activity_id,
                        last_check_timestamp=timestamp
                    )
                    session.add(activity_state)
                
                session.commit()
                logger.debug(f"Updated activity state: activity_id={activity_id}, timestamp={timestamp}")
        except Exception as e:
            logger.error(f"Failed to update activity state: {e}")
            raise
    
    def close(self):
        """Close the database engine (cleanup resources)."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.dispose()
            logger.debug("SQLAlchemy engine disposed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()