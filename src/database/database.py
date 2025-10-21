"""
Database connection and session management
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import DB_PATH

# Create engine (SQLite)
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Session:
    """
    Context manager for database sessions
    
    Usage:
        with get_session() as session:
            # do database operations
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_engine():
    """Get the database engine"""
    return engine

