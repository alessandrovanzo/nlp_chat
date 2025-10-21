"""
Mock vector search engine for toy RAG implementation.

In production, you would use a real vector database like Pinecone, Weaviate, 
or Qdrant. This implementation loads all embeddings into memory and performs 
brute-force cosine similarity search, which is inefficient but simple for demos.
"""
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def vector_search(
    query_embedding: List[float],
    chunks_data: List[Dict[str, Any]],
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search on chunks.
    
    This is a naive implementation that:
    1. Loads all embeddings into memory
    2. Calculates cosine similarity with the query for each chunk
    3. Sorts by similarity and returns top_k results
    
    Args:
        query_embedding: Embedding vector for the search query
        chunks_data: List of chunk dictionaries with 'embedding' and metadata
        top_k: Number of top results to return
        
    Returns:
        List of results sorted by similarity (highest first), each containing:
        - id: chunk ID
        - content: chunk text
        - metadata: document metadata (title, page numbers, etc.)
        - similarity: cosine similarity score
    """
    results = []
    
    for chunk_data in chunks_data:
        try:
            # Build metadata dict
            metadata = {
                "title": chunk_data["title"],
                "description": chunk_data["description"],
                "source_type": chunk_data["source_type"],
                "start_page": chunk_data["start_page"],
                "end_page": chunk_data["end_page"],
                "chunk_number": chunk_data["chunk_number"],
                "total_chunks": chunk_data["total_chunks"],
                "unit_name": chunk_data["unit_name"],
                "document_id": chunk_data["document_id"]
            }
            
            embedding = chunk_data["embedding"]
            
            # Check embedding dimensions
            if len(embedding) != len(query_embedding):
                logger.error(
                    f"Dimension mismatch for chunk {chunk_data['chunk_id']} "
                    f"('{chunk_data['title']}'): "
                    f"query={len(query_embedding)}, chunk={len(embedding)}"
                )
                continue
            
            # Calculate similarity
            similarity = cosine_similarity(query_embedding, embedding)
            results.append({
                "id": chunk_data["chunk_id"],
                "content": chunk_data["content"],
                "metadata": metadata,
                "similarity": similarity
            })
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_data.get('chunk_id', 'unknown')}: {str(e)}")
            continue
    
    # Sort by similarity (highest first) and return top_k
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]

