"""
Document Processing Module
Handles PDF and EPUB extraction, chunking, and embedding generation
"""
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from openai import OpenAI
from config import oai_key
import json
import sqlite3
import os

# Initialize OpenAI client
client = OpenAI(api_key=oai_key)

# Database path
DB_PATH = "rag_database.db"


def get_file_type(file_path: str) -> str:
    """
    Determine file type from extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type ('pdf', 'epub', 'txt', or 'unsupported')
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.epub':
        return 'epub'
    elif ext == '.txt':
        return 'txt'
    else:
        return 'unsupported'


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


def extract_text_from_pdf(pdf_file_path: str) -> List[str]:
    """
    Extract text from PDF, returning a list where each element is a page's text
    
    Args:
        pdf_file_path: Path to the PDF file
        
    Returns:
        List of strings, one per page
        
    Raises:
        Exception: If file is corrupted or cannot be read
    """
    pages_text = []
    
    try:
        with open(pdf_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is corrupted
            if len(pdf_reader.pages) == 0:
                raise Exception("PDF file is empty or corrupted")
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                pages_text.append(text)
                
    except PyPDF2.errors.PdfReadError as e:
        raise Exception(f"Corrupted or invalid PDF file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    return pages_text


def extract_text_from_epub(epub_file_path: str) -> List[str]:
    """
    Extract text from EPUB, returning a list where each element is a page's text
    Pages are calculated as 300 words each
    
    Args:
        epub_file_path: Path to the EPUB file
        
    Returns:
        List of strings, one per page (300 words)
        
    Raises:
        Exception: If file is corrupted or cannot be read
    """
    try:
        book = epub.read_epub(epub_file_path)
        
        # Get all document items (chapters)
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        if len(items) == 0:
            raise Exception("EPUB file is empty or corrupted")
        
        # Extract all text from all chapters into one continuous text
        full_text = []
        for item in items:
            # Parse HTML content
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            if text:
                full_text.append(text)
        
        # Combine all text
        combined_text = ' '.join(full_text)
        
        if not combined_text.strip():
            raise Exception("EPUB file contains no text")
        
        # Split into pages of 300 words each
        pages = split_text_by_words(combined_text, words_per_page=300)
        
        return pages
                
    except ebooklib.epub.EpubException as e:
        raise Exception(f"Corrupted or invalid EPUB file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading EPUB: {str(e)}")


def extract_text_from_txt(txt_file_path: str) -> List[str]:
    """
    Extract text from TXT, returning a list where each element is a page's text
    Pages are calculated as 300 words each
    
    Args:
        txt_file_path: Path to the TXT file
        
    Returns:
        List of strings, one per page (300 words)
        
    Raises:
        Exception: If file cannot be read
    """
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if not content.strip():
            raise Exception("TXT file is empty")
        
        # Split into pages of 300 words each
        pages = split_text_by_words(content, words_per_page=300)
        
        return pages
                
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(txt_file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            
            pages = split_text_by_words(content, words_per_page=300)
            return pages
        except Exception as e:
            raise Exception(f"Error reading TXT file with alternative encoding: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")


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


def create_embedding(text: str) -> List[float]:
    """
    Create embedding using OpenAI's text-embedding-3-small model
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list of floats
    """
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        # Check if it's a token limit error
        error_str = str(e)
        if "maximum context length" in error_str or "8192 tokens" in error_str:
            # This will be caught by the caller to split the chunk
            raise Exception(f"TOKEN_LIMIT_EXCEEDED: {error_str}")
        raise Exception(f"Error creating embedding: {str(e)}")


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
        source_type: Type of source document ('pdf' or 'epub')
        
    Returns:
        The ID of the inserted document
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert into database with separate columns
    cursor.execute(
        """INSERT INTO documents 
        (content, embedding, title, description, source_type, start_page, end_page, 
         chunk_number, total_chunks, unit_name, active) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            chunk_text, 
            json.dumps(embedding), 
            source_name,
            description,
            source_type,
            chunk_metadata.get('start_page'),
            chunk_metadata.get('end_page'),
            chunk_metadata.get('chunk_number'),
            chunk_metadata.get('total_chunks'),
            chunk_metadata.get('unit_name'),
            True  # active by default
        )
    )
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return doc_id


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
    Process a document file (PDF or EPUB): extract text, chunk it, create embeddings, and store in database
    
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
                for idx, doc_id in enumerate(doc_ids):
                    suffix = f" (split {idx + 1}/{len(doc_ids)})" if len(doc_ids) > 1 else ""
                    processed_chunks.append({
                        "doc_id": doc_id,
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


# Keep backward compatibility with old function name
def process_pdf(
    pdf_file_path: str,
    source_name: str,
    description: str,
    pages_per_chunk: int = 3
) -> Dict[str, Any]:
    """
    Legacy function - redirects to process_document
    """
    return process_document(pdf_file_path, source_name, description, pages_per_chunk)

