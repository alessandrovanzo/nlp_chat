"""
Database initialization script
Creates the necessary tables for the RAG knowledge base using SQLAlchemy
"""
import os
from src.config import DB_PATH
from src.database.models import Base
from src.database.database import get_engine


def initialize_db():
    """Initialize the database with required tables"""
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Create all tables
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    print(f"✓ Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    initialize_db()
