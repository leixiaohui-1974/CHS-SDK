from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging
from contextlib import contextmanager
import time

from api.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine_kwargs = {
    "echo": settings.database_echo,
    "future": True,
}

# Special configuration for SQLite
if settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20,
        },
    })

# Create engine
engine = create_engine(settings.get_database_url(), **engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Create Base class for models
Base = declarative_base()

# Metadata for database operations
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def drop_tables():
    """
    Drop all tables in the database
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise

def reset_database():
    """
    Reset the database by dropping and recreating all tables
    """
    logger.warning("Resetting database - all data will be lost")
    drop_tables()
    create_tables()

def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_info() -> dict:
    """
    Get database information
    """
    try:
        with engine.connect() as connection:
            # Get database version and other info
            result = connection.execute("SELECT sqlite_version()" if settings.database_url.startswith("sqlite") else "SELECT version()")
            version = result.scalar()
            
            return {
                "url": settings.get_database_url(),
                "version": version,
                "echo": settings.database_echo,
                "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else -1,
                "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else -1,
            }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {"error": str(e)}

# Database health check
def health_check() -> dict:
    """
    Perform database health check
    """
    try:
        start_time = time.time()
        
        with get_db_context() as db:
            # Simple query to test connection
            db.execute("SELECT 1")
            
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "database_info": get_database_info()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_info": get_database_info()
        }