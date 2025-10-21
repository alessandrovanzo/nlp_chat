"""
Database CRUD operations
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models import Document, Chunk


def get_or_create_document(
    session: Session,
    title: str,
    description: str,
    source_type: str
) -> Document:
    """
    Get existing document or create a new one
    
    Args:
        session: Database session
        title: Name of the source document
        description: Description of the source document
        source_type: Type of source document ('pdf', 'epub', 'txt')
        
    Returns:
        The Document instance
    """
    # Check if document already exists
    stmt = select(Document).where(
        Document.title == title,
        Document.source_type == source_type
    )
    document = session.execute(stmt).scalar_one_or_none()
    
    if document:
        return document
    
    # Create new document
    document = Document(
        title=title,
        description=description,
        source_type=source_type,
        total_chunks=0,
        active=1
    )
    session.add(document)
    session.flush()  # Get the ID without committing
    
    return document


def create_chunk(
    session: Session,
    document_id: int,
    content: str,
    embedding: List[float],
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    chunk_number: Optional[int] = None,
    unit_name: str = "page"
) -> Chunk:
    """
    Create a new chunk
    
    Args:
        session: Database session
        document_id: ID of the parent document
        content: Text content of the chunk
        embedding: Embedding vector
        start_page: Starting page number
        end_page: Ending page number
        chunk_number: Chunk number in sequence
        unit_name: Name of the unit (page, chapter, etc.)
        
    Returns:
        The created Chunk instance
    """
    chunk = Chunk(
        document_id=document_id,
        content=content,
        embedding=json.dumps(embedding),
        start_page=start_page,
        end_page=end_page,
        chunk_number=chunk_number,
        unit_name=unit_name
    )
    session.add(chunk)
    session.flush()
    
    return chunk


def update_document_chunk_count(session: Session, document_id: int) -> None:
    """
    Update the total_chunks count for a document
    
    Args:
        session: Database session
        document_id: ID of the document to update
    """
    document = session.get(Document, document_id)
    if document:
        chunk_count = session.query(Chunk).filter(Chunk.document_id == document_id).count()
        document.total_chunks = chunk_count
        session.flush()


def get_active_chunks_with_documents(session: Session) -> List[Dict[str, Any]]:
    """
    Get all chunks from active documents with their metadata
    
    Args:
        session: Database session
        
    Returns:
        List of dictionaries containing chunk and document information
    """
    stmt = (
        select(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.active == 1)
    )
    
    results = session.execute(stmt).all()
    
    chunks_data = []
    for chunk, document in results:
        chunks_data.append({
            "chunk_id": chunk.id,
            "content": chunk.content,
            "embedding": json.loads(chunk.embedding),
            "start_page": chunk.start_page,
            "end_page": chunk.end_page,
            "chunk_number": chunk.chunk_number,
            "unit_name": chunk.unit_name,
            "document_id": document.id,
            "title": document.title,
            "description": document.description,
            "source_type": document.source_type,
            "total_chunks": document.total_chunks
        })
    
    return chunks_data


def get_all_documents(session: Session) -> List[Document]:
    """
    Get all documents ordered by creation date (newest first)
    
    Args:
        session: Database session
        
    Returns:
        List of Document instances
    """
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(session.execute(stmt).scalars())


def toggle_document_active(session: Session, title: str, active: bool) -> Optional[Document]:
    """
    Toggle the active status of a document by title
    
    Args:
        session: Database session
        title: Title of the document
        active: New active status
        
    Returns:
        The updated Document instance or None if not found
    """
    stmt = select(Document).where(Document.title == title)
    document = session.execute(stmt).scalar_one_or_none()
    
    if document:
        document.active = 1 if active else 0
        session.flush()
    
    return document


def delete_document(session: Session, title: str) -> Optional[int]:
    """
    Delete a document by title (will cascade to chunks)
    
    Args:
        session: Database session
        title: Title of the document to delete
        
    Returns:
        The number of chunks that were deleted, or None if document not found
    """
    stmt = select(Document).where(Document.title == title)
    document = session.execute(stmt).scalar_one_or_none()
    
    if document:
        chunk_count = document.total_chunks
        session.delete(document)
        session.flush()
        return chunk_count
    
    return None

