"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger
from src.config import settings
from .models import Base


def create_database_engine():
    """Create database engine based on configuration"""
    if settings.database_url.startswith("sqlite"):
        # SQLite configuration for development
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug
        )
    else:
        # PostgreSQL/other databases
        engine = create_engine(
            settings.database_url,
            echo=settings.debug
        )
    
    return engine


def init_database():
    """Initialize database tables"""
    engine = create_database_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_session() -> Session:
    """Get database session"""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Global engine instance
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 