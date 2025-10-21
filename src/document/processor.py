"""
Document processing orchestration
Handles extraction, chunking, embedding, and storage
"""
from typing import List, Dict, Any

from src.document.embeddings import create_embedding
from src.document.extractors import (
    get_file_type,
    extract_text_from_pdf,
    extract_text_from_epub,
    extract_text_from_txt
)
from src.document.chunker import chunk_pages
from src.database.database import get_session
from src.database.operations import (
    create_document,
    create_chunk,
    update_document_chunk_count
)


def process_chunk_with_splitting(
    session,
    chunk_text: str,
    document_id: int,
    chunk_metadata: Dict[str, Any],
    source_name: str,
    description: str,
    prepend_metadata: bool = True,
    max_depth: int = 3
) -> List[int]:
    """
    Process a chunk and split it if it's too large for embedding
    
    Args:
        session: Database session
        chunk_text: The chunk text to process
        document_id: ID of the parent document
        chunk_metadata: Metadata for the chunk
        source_name: Name of the source document (for prepending)
        description: Description of the source document (for prepending)
        prepend_metadata: Whether to prepend metadata when creating embeddings
        max_depth: Maximum number of times to split (prevents infinite recursion)
        
    Returns:
        List of chunk IDs created
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
        chunk = create_chunk(
            session=session,
            document_id=document_id,
            content=chunk_text,
            embedding=embedding,
            start_page=chunk_metadata.get('start_page'),
            end_page=chunk_metadata.get('end_page'),
            chunk_number=chunk_metadata.get('chunk_number'),
            unit_name=chunk_metadata.get('unit_name', 'page')
        )
        
        return [chunk.id]
        
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
            chunk_ids = []
            chunk_ids.extend(process_chunk_with_splitting(
                session, first_half, document_id, first_metadata,
                source_name, description, prepend_metadata, max_depth - 1
            ))
            chunk_ids.extend(process_chunk_with_splitting(
                session, second_half, document_id, second_metadata,
                source_name, description, prepend_metadata, max_depth - 1
            ))
            
            return chunk_ids
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
        
        # Use a single database session for all operations
        with get_session() as session:
            # Create the document (will raise ValueError if title exists)
            document = create_document(
                session=session,
                title=source_name,
                description=description,
                source_type=file_type
            )
            
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
                    chunk_ids = process_chunk_with_splitting(
                        session=session,
                        chunk_text=chunk['text'],
                        document_id=document.id,
                        chunk_metadata=chunk_metadata,
                        source_name=source_name,
                        description=description,
                        prepend_metadata=prepend_metadata
                    )
                    
                    # Track how many sub-chunks were created
                    if len(chunk_ids) > 1:
                        total_splits += len(chunk_ids) - 1
                    
                    # Add info about all created chunks
                    for idx, chunk_id in enumerate(chunk_ids):
                        suffix = f" (split {idx + 1}/{len(chunk_ids)})" if len(chunk_ids) > 1 else ""
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
            
            # Update the document's total_chunks count
            update_document_chunk_count(session, document.id)
            
            # Commit all changes
            session.commit()
        
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

