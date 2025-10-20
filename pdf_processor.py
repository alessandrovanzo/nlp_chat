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
        File type ('pdf', 'epub', or 'unsupported')
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.epub':
        return 'epub'
    else:
        return 'unsupported'


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
    Extract text from EPUB, returning a list where each element is a chapter's text
    
    Args:
        epub_file_path: Path to the EPUB file
        
    Returns:
        List of strings, one per chapter
        
    Raises:
        Exception: If file is corrupted or cannot be read
    """
    chapters_text = []
    
    try:
        book = epub.read_epub(epub_file_path)
        
        # Get all document items (chapters)
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        if len(items) == 0:
            raise Exception("EPUB file is empty or corrupted")
        
        for item in items:
            # Parse HTML content
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            if text:  # Only add non-empty chapters
                chapters_text.append(text)
                
    except ebooklib.epub.EpubException as e:
        raise Exception(f"Corrupted or invalid EPUB file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading EPUB: {str(e)}")
    
    return chapters_text


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
    
    # Combine metadata
    metadata = {
        "title": source_name,
        "description": description,
        "source_type": source_type,
        **chunk_metadata
    }
    
    # Insert into database
    cursor.execute(
        "INSERT INTO documents (content, embedding, metadata) VALUES (?, ?, ?)",
        (chunk_text, json.dumps(embedding), json.dumps(metadata))
    )
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return doc_id


def process_document(
    file_path: str,
    source_name: str,
    description: str,
    pages_per_chunk: int = 3
) -> Dict[str, Any]:
    """
    Process a document file (PDF or EPUB): extract text, chunk it, create embeddings, and store in database
    
    Args:
        file_path: Path to the document file
        source_name: Name of the source document
        description: Description of the source document
        pages_per_chunk: Number of pages/chapters per chunk
        
    Returns:
        Summary of the processing
    """
    try:
        # Determine file type
        file_type = get_file_type(file_path)
        
        if file_type == 'unsupported':
            raise Exception(f"Unsupported file format. Please upload a PDF or EPUB file.")
        
        # Extract text based on file type
        if file_type == 'pdf':
            pages = extract_text_from_pdf(file_path)
            unit_name = "page"
        else:  # epub
            pages = extract_text_from_epub(file_path)
            unit_name = "chapter"
        
        if not pages:
            raise Exception(f"No text extracted from {file_type.upper()}")
        
        # Chunk the pages/chapters
        chunks = chunk_pages(pages, pages_per_chunk, unit_name)
        
        # Process each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Create the text to embed: source_name + description + chunk text
            text_to_embed = f"{source_name}\n{description}\n\n{chunk['text']}"
            
            # Create embedding
            embedding = create_embedding(text_to_embed)
            
            # Store in database
            doc_id = store_chunk_in_db(
                chunk_text=chunk['text'],
                embedding=embedding,
                source_name=source_name,
                description=description,
                chunk_metadata={
                    "start_page": chunk['start_page'],
                    "end_page": chunk['end_page'],
                    "chunk_number": i + 1,
                    "total_chunks": len(chunks),
                    "unit_name": unit_name
                },
                source_type=file_type
            )
            
            processed_chunks.append({
                "doc_id": doc_id,
                "chunk_number": i + 1,
                "pages": f"{chunk['start_page']}-{chunk['end_page']}"
            })
        
        return {
            "success": True,
            "source_name": source_name,
            "file_type": file_type,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "pages_per_chunk": pages_per_chunk,
            "unit_name": unit_name,
            "processed_chunks": processed_chunks
        }
        
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

