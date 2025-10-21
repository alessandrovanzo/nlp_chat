"""
Database initialization script
Creates the necessary tables for the RAG knowledge base
"""
import sqlite3
import os
from src.config import DB_PATH


def initialize_db():
    """Initialize the database with required tables"""
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            source_type TEXT,
            total_chunks INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chunks table with foreign key to documents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            start_page INTEGER,
            end_page INTEGER,
            chunk_number INTEGER,
            unit_name TEXT DEFAULT 'page',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    
    # Create indices for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    initialize_db()

