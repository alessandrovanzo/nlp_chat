"""
Business logic for RAG mcp_server operations
"""
import json
import logging
import traceback
from typing import List, Dict, Any, Tuple

from src.database.database import get_session
from src.database.operations import (
    get_active_chunks_with_documents,
    get_all_documents,
    toggle_document_active,
    delete_document
)
from src.database.mock_vector_engine import vector_search
from src.document_processing.embeddings import create_embedding

logger = logging.getLogger(__name__)


def search_knowledge_base(query: str, top_k: int = 3) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Search the knowledge base using vector similarity
    
    Args:
        query: Search query string
        top_k: Number of top results to return
        
    Returns:
        Tuple of (success, message, results)
        - success: Boolean indicating if search was successful
        - message: Human-readable message or error description
        - results: List of matching chunks with metadata and similarity scores
    """
    if not query:
        logger.warning("Empty query received")
        return False, "Query cannot be empty", []
    
    logger.info(f"Searching knowledge base for: '{query}' (top_k={top_k})")
    
    # Generate embedding for query
    try:
        query_embedding = create_embedding(query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
    except Exception as e:
        logger.error(f"Failed to create OpenAI embedding: {str(e)}")
        return False, f"Error creating embedding: {str(e)}", []
    
    # Search database (only active documents)
    try:
        with get_session() as session:
            chunks_data = get_active_chunks_with_documents(session)
            
            if not chunks_data:
                logger.warning("No active documents found in database")
                return True, "No active documents found in the knowledge base. Please activate some sources in the upload interface.", []
            
            logger.info(f"Retrieved {len(chunks_data)} chunks from active documents")
            
            # Perform vector search
            top_results = vector_search(query_embedding, chunks_data, top_k)
            
            if not top_results:
                error_msg = "All documents had incompatible embeddings. Database may contain mixed embedding dimensions."
                logger.error(error_msg)
                return False, error_msg, []
            
            logger.info(f"Returning top {len(top_results)} results with similarities: {[r['similarity'] for r in top_results]}")
            
            return True, f"Found {len(top_results)} relevant document(s)", top_results
            
    except Exception as e:
        logger.error(f"Error in search_knowledge_base: {str(e)}")
        logger.error(traceback.format_exc())
        return False, f"Error during search: {str(e)}", []


def list_all_sources() -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get list of all documents with their status
    
    Returns:
        Tuple of (success, message, sources)
    """
    logger.info("Listing all sources")
    try:
        with get_session() as session:
            documents = get_all_documents(session)
            
            sources = []
            for doc in documents:
                sources.append({
                    "id": doc.id,
                    "title": doc.title,
                    "description": doc.description,
                    "source_type": doc.source_type or "unknown",
                    "chunk_count": doc.total_chunks,
                    "active": bool(doc.active)
                })
            
            logger.info(f"Found {len(sources)} sources")
            return True, f"Found {len(sources)} sources", sources
            
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e), []


def toggle_source_active(title: str, active: bool) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Toggle active status of a source document_processing
    
    Args:
        title: Document title
        active: New active status
        
    Returns:
        Tuple of (success, message, data)
    """
    if not title:
        return False, "Title is required", {}
    
    logger.info(f"Toggling source '{title}' to active={active}")
    
    try:
        with get_session() as session:
            document = toggle_document_active(session, title, active)
            
            if not document:
                return False, "Source not found", {}
            
            session.commit()
            logger.info(f"Updated source '{title}' (affects {document.total_chunks} chunks)")
            
            return True, f"Source updated successfully", {
                "updated_chunks": document.total_chunks,
                "active": active
            }
            
    except Exception as e:
        logger.error(f"Error toggling source: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e), {}


def delete_source(title: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Delete a source document_processing and all its chunks
    
    Args:
        title: Document title
        
    Returns:
        Tuple of (success, message, data)
    """
    if not title:
        return False, "Title is required", {}
    
    logger.info(f"Deleting source '{title}'")
    
    try:
        with get_session() as session:
            chunk_count = delete_document(session, title)
            
            if chunk_count is None:
                return False, "Source not found", {}
            
            session.commit()
            logger.info(f"Deleted document_processing '{title}' and {chunk_count} chunks (CASCADE)")
            
            return True, "Source deleted successfully", {"deleted_chunks": chunk_count}
            
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e), {}


def get_available_sources() -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get list of all available sources (documents) with their metadata for LLM tool use
    
    Returns:
        Tuple of (success, message, sources)
        - success: Boolean indicating if operation was successful
        - message: Human-readable message
        - sources: List of documents with id, title, description, total_chunks, and active status
    """
    logger.info("Getting available sources for LLM tool call")
    try:
        with get_session() as session:
            documents = get_all_documents(session)
            
            sources = []
            for doc in documents:
                sources.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "description": doc.description or "No description available",
                    "source_type": doc.source_type or "unknown",
                    "total_chunks": doc.total_chunks,
                    "active": bool(doc.active)
                })
            
            logger.info(f"Found {len(sources)} sources")
            return True, f"Found {len(sources)} available sources", sources
            
    except Exception as e:
        logger.error(f"Error getting available sources: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e), []


def search_specific_documents(
    query: str,
    document_ids: List[int],
    top_k: int = 3
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Search the knowledge base restricted to specific documents using vector similarity
    
    Args:
        query: Search query string
        document_ids: List of document IDs to restrict search to
        top_k: Number of top results to return
        
    Returns:
        Tuple of (success, message, results)
        - success: Boolean indicating if search was successful
        - message: Human-readable message or error description
        - results: List of matching chunks with metadata and similarity scores
    """
    if not query:
        logger.warning("Empty query received")
        return False, "Query cannot be empty", []
    
    if not document_ids:
        logger.warning("No document IDs provided")
        return False, "At least one document ID is required", []
    
    logger.info(f"Searching specific documents {document_ids} for: '{query}' (top_k={top_k})")
    
    # Generate embedding for query
    try:
        query_embedding = create_embedding(query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
    except Exception as e:
        logger.error(f"Failed to create OpenAI embedding: {str(e)}")
        return False, f"Error creating embedding: {str(e)}", []
    
    # Search database (only specified documents, and only if active)
    try:
        with get_session() as session:
            chunks_data = get_active_chunks_with_documents(session)
            
            # Filter by document IDs
            filtered_chunks = [
                chunk for chunk in chunks_data 
                if chunk["document_id"] in document_ids
            ]
            
            if not filtered_chunks:
                logger.warning(f"No active chunks found for document IDs: {document_ids}")
                return True, f"No active chunks found for the specified documents (IDs: {document_ids}). Make sure the documents exist and are active.", []
            
            logger.info(f"Retrieved {len(filtered_chunks)} chunks from {len(document_ids)} specified document(s)")
            
            # Perform vector search
            top_results = vector_search(query_embedding, filtered_chunks, top_k)
            
            if not top_results:
                error_msg = "All documents had incompatible embeddings. Database may contain mixed embedding dimensions."
                logger.error(error_msg)
                return False, error_msg, []
            
            logger.info(f"Returning top {len(top_results)} results with similarities: {[r['similarity'] for r in top_results]}")
            
            return True, f"Found {len(top_results)} relevant chunk(s) from specified documents", top_results
            
    except Exception as e:
        logger.error(f"Error in search_specific_documents: {str(e)}")
        logger.error(traceback.format_exc())
        return False, f"Error during search: {str(e)}", []

