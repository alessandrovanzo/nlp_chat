"""
Database operations for RAG knowledge base
"""
import sqlite3
import json
from typing import List, Dict, Any
from contextlib import contextmanager
from src.config import DB_PATH
from src.document.embeddings import create_embedding
from src.document.extractors import get_file_type, extract_text_from_pdf, extract_text_from_epub, extract_text_from_txt
from src.document.chunker import chunk_pages


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_or_create_document(
    conn: sqlite3.Connection,
    source_name: str,
    description: str,
    source_type: str
) -> int:
    """
    Get existing document or create a new one
    
    Args:
        conn: Database connection
        source_name: Name of the source document
        description: Description of the source document
        source_type: Type of source document ('pdf', 'epub', 'txt')
        
    Returns:
        The ID of the document
    """
    cursor = conn.cursor()
    
    # Check if document already exists
    cursor.execute(
        "SELECT id FROM documents WHERE title = ? AND source_type = ?",
        (source_name, source_type)
    )
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Create new document
    cursor.execute(
        """INSERT INTO documents (title, description, source_type, total_chunks, active)
        VALUES (?, ?, ?, 0, 1)""",
        (source_name, description, source_type)
    )
    
    return cursor.lastrowid


def store_chunk_in_db(
    chunk_text: str,
    embedding: List[float],
    source_name: str,
    description: str,
    chunk_metadata: Dict[str, Any],
    source_type: str = "pdf"
) -> int:
    """
    Store a chunk with its embedding in the database
    
    Args:
        chunk_text: The text content of the chunk
        embedding: The embedding vector
        source_name: Name of the source document
        description: Description of the source document
        chunk_metadata: Additional metadata (page numbers, etc.)
        source_type: Type of source document ('pdf', 'epub', or 'txt')
        
    Returns:
        The ID of the inserted chunk
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get or create the document
        document_id = get_or_create_document(conn, source_name, description, source_type)
        
        # Insert chunk with foreign key reference
        cursor.execute(
            """INSERT INTO chunks 
            (document_id, content, embedding, start_page, end_page, chunk_number, unit_name) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id,
                chunk_text, 
                json.dumps(embedding),
                chunk_metadata.get('start_page'),
                chunk_metadata.get('end_page'),
                chunk_metadata.get('chunk_number'),
                chunk_metadata.get('unit_name')
            )
        )
        
        chunk_id = cursor.lastrowid
        
        # Update total_chunks count in document
        cursor.execute(
            "UPDATE documents SET total_chunks = (SELECT COUNT(*) FROM chunks WHERE document_id = ?) WHERE id = ?",
            (document_id, document_id)
        )
        
        conn.commit()
        
        return chunk_id


def process_chunk_with_splitting(
    chunk_text: str,
    source_name: str,
    description: str,
    chunk_metadata: Dict[str, Any],
    source_type: str,
    prepend_metadata: bool = True,
    max_depth: int = 3
) -> List[int]:
    """
    Process a chunk and split it if it's too large for embedding
    
    Args:
        chunk_text: The chunk text to process
        source_name: Name of the source document
        description: Description of the source document
        chunk_metadata: Metadata for the chunk
        source_type: Type of source document
        prepend_metadata: Whether to prepend metadata when creating embeddings
        max_depth: Maximum number of times to split (prevents infinite recursion)
        
    Returns:
        List of document IDs created
    """
    if max_depth <= 0:
        raise Exception("Chunk is too large even after multiple splits")
    
    # Create the text to embed: optionally prepend source_name + description
    if prepend_metadata:
        text_to_embed = f"{source_name}\n{description}\n\n{chunk_text}"
    else:
        text_to_embed = chunk_text
    
    try:
        # Try to create embedding
        embedding = create_embedding(text_to_embed)
        
        # Success! Store in database
        doc_id = store_chunk_in_db(
            chunk_text=chunk_text,
            embedding=embedding,
            source_name=source_name,
            description=description,
            chunk_metadata=chunk_metadata,
            source_type=source_type
        )
        return [doc_id]
        
    except Exception as e:
        # Check if it's a token limit error
        if "TOKEN_LIMIT_EXCEEDED" in str(e):
            # Split the chunk in half
            mid_point = len(chunk_text) // 2
            
            # Find a good split point (prefer splitting at sentence or paragraph boundary)
            split_point = mid_point
            for delimiter in ['\n\n', '\n', '. ', ' ']:
                pos = chunk_text.rfind(delimiter, mid_point - 500, mid_point + 500)
                if pos != -1:
                    split_point = pos + len(delimiter)
                    break
            
            first_half = chunk_text[:split_point].strip()
            second_half = chunk_text[split_point:].strip()
            
            # Create metadata for both halves
            first_metadata = chunk_metadata.copy()
            first_metadata["split_part"] = "1/2"
            
            second_metadata = chunk_metadata.copy()
            second_metadata["split_part"] = "2/2"
            
            # Recursively process both halves
            doc_ids = []
            doc_ids.extend(process_chunk_with_splitting(
                first_half, source_name, description, first_metadata, source_type, prepend_metadata, max_depth - 1
            ))
            doc_ids.extend(process_chunk_with_splitting(
                second_half, source_name, description, second_metadata, source_type, prepend_metadata, max_depth - 1
            ))
            
            return doc_ids
        else:
            # Different error, re-raise
            raise


def process_document(
    file_path: str,
    source_name: str,
    description: str,
    pages_per_chunk: int = 3,
    prepend_metadata: bool = True
) -> Dict[str, Any]:
    """
    Process a document file (PDF, EPUB, or TXT): extract text, chunk it, create embeddings, and store in database
    
    Args:
        file_path: Path to the document file
        source_name: Name of the source document
        description: Description of the source document
        pages_per_chunk: Number of pages/chapters per chunk
        prepend_metadata: Whether to prepend metadata (source name + description) when creating embeddings
        
    Returns:
        Summary of the processing
    """
    try:
        # Determine file type
        file_type = get_file_type(file_path)
        
        if file_type == 'unsupported':
            raise Exception(f"Unsupported file format. Please upload a PDF, EPUB, or TXT file.")
        
        # Extract text based on file type
        if file_type == 'pdf':
            pages = extract_text_from_pdf(file_path)
            unit_name = "page"
        elif file_type == 'epub':
            pages = extract_text_from_epub(file_path)
            unit_name = "page"  # EPUB now uses word-count-based pages (300 words each)
        else:  # txt
            pages = extract_text_from_txt(file_path)
            unit_name = "page"  # TXT uses word-count-based pages (300 words each)
        
        if not pages:
            raise Exception(f"No text extracted from {file_type.upper()}")
        
        # Chunk the pages/chapters
        chunks = chunk_pages(pages, pages_per_chunk, unit_name)
        
        # Process each chunk (with automatic splitting if needed)
        processed_chunks = []
        failed_chunks = []
        total_splits = 0
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "start_page": chunk['start_page'],
                "end_page": chunk['end_page'],
                "chunk_number": i + 1,
                "total_chunks": len(chunks),
                "unit_name": unit_name
            }
            
            try:
                # Process chunk with automatic splitting if needed
                doc_ids = process_chunk_with_splitting(
                    chunk_text=chunk['text'],
                    source_name=source_name,
                    description=description,
                    chunk_metadata=chunk_metadata,
                    source_type=file_type,
                    prepend_metadata=prepend_metadata
                )
                
                # Track how many sub-chunks were created
                if len(doc_ids) > 1:
                    total_splits += len(doc_ids) - 1
                
                # Add info about all created chunks
                for idx, chunk_id in enumerate(doc_ids):
                    suffix = f" (split {idx + 1}/{len(doc_ids)})" if len(doc_ids) > 1 else ""
                    processed_chunks.append({
                        "chunk_id": chunk_id,
                        "doc_id": chunk_id,  # For backward compatibility
                        "chunk_number": i + 1,
                        "pages": f"{chunk['start_page']}-{chunk['end_page']}{suffix}"
                    })
            except Exception as e:
                # Log failed chunk but continue processing
                error_msg = str(e)
                failed_chunks.append({
                    "chunk_number": i + 1,
                    "pages": f"{chunk['start_page']}-{chunk['end_page']}",
                    "error": error_msg
                })
                print(f"Warning: Failed to process chunk {i + 1} ({chunk['start_page']}-{chunk['end_page']}): {error_msg}")
                continue
        
        result = {
            "success": True,
            "source_name": source_name,
            "file_type": file_type,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "pages_per_chunk": pages_per_chunk,
            "unit_name": unit_name,
            "processed_chunks": processed_chunks,
            "successful_chunks": len(processed_chunks),
            "failed_chunks": failed_chunks,
            "failed_count": len(failed_chunks)
        }
        
        # Add notes about splits and failures
        notes = []
        if total_splits > 0:
            notes.append(f"{total_splits} chunk(s) were automatically split due to size")
        if len(failed_chunks) > 0:
            notes.append(f"{len(failed_chunks)} chunk(s) failed to process and were skipped")
        
        if notes:
            result["note"] = " | ".join(notes)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

