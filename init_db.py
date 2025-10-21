"""
Initialize SQLite database with fake embeddings and content
"""
import sqlite3
import json
import numpy as np
from typing import List

DB_PATH = "rag_database.db"

def fake_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate a fake but consistent embedding for text"""
    np.random.seed(hash(text) % (2**32))
    embedding = np.random.randn(dim)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()

# Sample documents for the knowledge base
SAMPLE_DOCS = [
    {
        "title": "Python Programming Basics",
        "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python's extensive standard library and third-party packages make it suitable for web development, data science, automation, and more.",
        "category": "programming"
    },
    {
        "title": "Machine Learning Introduction",
        "content": "Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It uses statistical techniques to give computers the ability to learn patterns from data. Common types include supervised learning, unsupervised learning, and reinforcement learning.",
        "category": "AI"
    },
    {
        "title": "FastAPI Framework",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It's one of the fastest Python frameworks available, with performance comparable to NodeJS and Go. FastAPI automatically generates interactive API documentation and validates request/response data.",
        "category": "programming"
    },
    {
        "title": "Vector Databases",
        "content": "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently. They're essential for similarity search in applications like recommendation systems, semantic search, and RAG (Retrieval Augmented Generation). Vector databases use techniques like approximate nearest neighbor search for fast retrieval.",
        "category": "database"
    },
    {
        "title": "Natural Language Processing",
        "content": "Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret, and manipulate human language. Modern NLP uses deep learning models like transformers to perform tasks such as translation, sentiment analysis, named entity recognition, and text generation. Popular models include BERT, GPT, and T5.",
        "category": "AI"
    },
    {
        "title": "SQLite Database",
        "content": "SQLite is a lightweight, serverless, self-contained SQL database engine. It's the most widely deployed database in the world, embedded in phones, browsers, and countless applications. SQLite is ideal for embedded databases, local storage, and development environments due to its simplicity and zero configuration.",
        "category": "database"
    },
    {
        "title": "REST API Design",
        "content": "REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs use HTTP methods (GET, POST, PUT, DELETE) to perform CRUD operations. Good REST API design includes proper use of HTTP status codes, clear endpoint naming, versioning, and comprehensive documentation.",
        "category": "programming"
    },
    {
        "title": "Embeddings and Semantic Search",
        "content": "Embeddings are dense vector representations of data that capture semantic meaning. In text, similar concepts have similar embeddings, enabling semantic search that understands meaning rather than just matching keywords. Embeddings are generated using neural networks trained on large corpora and typically have dimensions ranging from 128 to 1536.",
        "category": "AI"
    },
    {
        "title": "Async Programming in Python",
        "content": "Asynchronous programming in Python using async/await syntax allows for concurrent execution of I/O-bound operations without multithreading. The asyncio library provides the foundation for async Python, enabling efficient handling of many concurrent connections. This is particularly useful for web servers, API clients, and database operations.",
        "category": "programming"
    },
    {
        "title": "Retrieval Augmented Generation (RAG)",
        "content": "RAG combines the power of large language models with external knowledge retrieval. It works by first retrieving relevant documents from a knowledge base using semantic search, then using those documents as context for the LLM to generate more accurate and informed responses. RAG helps reduce hallucinations and grounds responses in factual information.",
        "category": "AI"
    }
]

def initialize_db():
    """Create and populate the SQLite database with two-table schema"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS chunks")
    cursor.execute("DROP TABLE IF EXISTS documents")
    
    # Create documents table (document-level info)
    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            source_type TEXT,
            total_chunks INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chunks table (chunk-level info) with foreign key
    cursor.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            start_page INTEGER,
            end_page INTEGER,
            chunk_number INTEGER,
            unit_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX idx_documents_title ON documents(title)")
    cursor.execute("CREATE INDEX idx_documents_source_type ON documents(source_type)")
    cursor.execute("CREATE INDEX idx_documents_active ON documents(active)")
    cursor.execute("CREATE INDEX idx_chunks_document_id ON chunks(document_id)")
    cursor.execute("CREATE INDEX idx_chunks_chunk_number ON chunks(chunk_number)")
    
    print("Populating database with sample documents...")
    
    # Create a single sample document
    cursor.execute(
        """INSERT INTO documents (title, description, source_type, total_chunks, active)
        VALUES (?, ?, ?, ?, ?)""",
        ("Sample Knowledge Base", "Collection of sample documents about various technical topics", 
         "sample", len(SAMPLE_DOCS), True)
    )
    document_id = cursor.lastrowid
    
    # Insert sample docs as chunks of the single document
    for i, doc in enumerate(SAMPLE_DOCS, 1):
        content = doc["content"]
        embedding = fake_embedding(content)
        
        cursor.execute(
            """INSERT INTO chunks 
            (document_id, content, embedding, start_page, end_page, chunk_number, unit_name) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id,
                content, 
                json.dumps(embedding),
                1,
                1,
                i,
                "section"
            )
        )
        print(f"  ✓ Added chunk {i}: {doc['title']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database initialized successfully!")
    print(f"   - 1 document")
    print(f"   - {len(SAMPLE_DOCS)} chunks")
    print(f"   Database location: {DB_PATH}")

if __name__ == "__main__":
    initialize_db()

