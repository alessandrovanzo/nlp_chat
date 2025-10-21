"""
Text chunking utilities
"""
from typing import List, Dict, Any


def split_text_by_words(text: str, words_per_page: int = 300) -> List[str]:
    """
    Split text into pages based on word count
    
    Args:
        text: The text to split
        words_per_page: Number of words per page (default: 300)
        
    Returns:
        List of strings, each containing approximately words_per_page words
    """
    # Split text into words
    words = text.split()
    
    if not words:
        return []
    
    pages = []
    current_page_words = []
    
    for word in words:
        current_page_words.append(word)
        
        # When we reach the target word count, create a new page
        if len(current_page_words) >= words_per_page:
            pages.append(' '.join(current_page_words))
            current_page_words = []
    
    # Add any remaining words as the last page
    if current_page_words:
        pages.append(' '.join(current_page_words))
    
    return pages


def chunk_pages(pages: List[str], pages_per_chunk: int = 3, unit_name: str = "page") -> List[Dict[str, Any]]:
    """
    Chunk pages/chapters into groups of N units
    
    Args:
        pages: List of page/chapter texts
        pages_per_chunk: Number of pages/chapters per chunk
        unit_name: Name of the unit ('page' for PDFs, 'chapter' for EPUBs)
        
    Returns:
        List of chunks with metadata
    """
    chunks = []
    
    for i in range(0, len(pages), pages_per_chunk):
        chunk_pages = pages[i:i + pages_per_chunk]
        chunk_text = "\n\n".join(chunk_pages)
        
        chunk = {
            "text": chunk_text,
            "start_page": i + 1,
            "end_page": min(i + pages_per_chunk, len(pages)),
            "total_pages": len(pages),
            "unit_name": unit_name
        }
        chunks.append(chunk)
    
    return chunks

