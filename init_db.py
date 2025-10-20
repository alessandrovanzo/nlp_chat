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
    """Create and populate the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS documents")
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample documents
    print("Populating database with sample documents...")
    for doc in SAMPLE_DOCS:
        content = doc["content"]
        embedding = fake_embedding(content)
        metadata = json.dumps({
            "title": doc["title"],
            "category": doc["category"]
        })
        
        cursor.execute(
            "INSERT INTO documents (content, embedding, metadata) VALUES (?, ?, ?)",
            (content, json.dumps(embedding), metadata)
        )
        print(f"  ✓ Added: {doc['title']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database initialized successfully with {len(SAMPLE_DOCS)} documents!")
    print(f"   Database location: {DB_PATH}")

if __name__ == "__main__":
    initialize_db()

