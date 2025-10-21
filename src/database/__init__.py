"""Database operations and models"""

from src.database.models import Base, Document, Chunk
from src.database.database import get_session, get_engine
from src.database.operations import (
    get_or_create_document,
    create_chunk,
    update_document_chunk_count,
    get_active_chunks_with_documents,
    get_all_documents,
    toggle_document_active,
    delete_document
)

__all__ = [
    # Models
    "Base",
    "Document",
    "Chunk",
    # Database
    "get_session",
    "get_engine",
    # Operations
    "get_or_create_document",
    "create_chunk",
    "update_document_chunk_count",
    "get_active_chunks_with_documents",
    "get_all_documents",
    "toggle_document_active",
    "delete_document",
]
