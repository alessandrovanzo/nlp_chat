"""
PDF Processing Module
Handles PDF extraction, chunking, and embedding generation
"""
import PyPDF2
from typing import List, Dict, Any
from openai import OpenAI
from config import oai_key
import json
import sqlite3

# Initialize OpenAI client
client = OpenAI(api_key=oai_key)

# Database path
DB_PATH = "rag_database.db"


def extract_text_from_pdf(pdf_file_path: str) -> List[str]:
    """
    Extract text from PDF, returning a list where each element is a page's text
    
    Args:
        pdf_file_path: Path to the PDF file
        
    Returns:
        List of strings, one per page
    """
    pages_text = []
    
    try:
        with open(pdf_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                pages_text.append(text)
                
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    return pages_text


def chunk_pages(pages: List[str], pages_per_chunk: int = 3) -> List[Dict[str, Any]]:
    """
    Chunk pages into groups of N pages
    
    Args:
        pages: List of page texts
        pages_per_chunk: Number of pages per chunk
        
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
            "total_pages": len(pages)
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
    chunk_metadata: Dict[str, Any]
) -> int:
    """
    Store a chunk with its embedding in the database
    
    Args:
        chunk_text: The text content of the chunk
        embedding: The embedding vector
        source_name: Name of the source document
        description: Description of the source document
        chunk_metadata: Additional metadata (page numbers, etc.)
        
    Returns:
        The ID of the inserted document
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Combine metadata
    metadata = {
        "title": source_name,
        "description": description,
        "source_type": "pdf",
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


def process_pdf(
    pdf_file_path: str,
    source_name: str,
    description: str,
    pages_per_chunk: int = 3
) -> Dict[str, Any]:
    """
    Process a PDF file: extract text, chunk it, create embeddings, and store in database
    
    Args:
        pdf_file_path: Path to the PDF file
        source_name: Name of the source document
        description: Description of the source document
        pages_per_chunk: Number of pages per chunk
        
    Returns:
        Summary of the processing
    """
    try:
        # Extract text from PDF
        pages = extract_text_from_pdf(pdf_file_path)
        
        if not pages:
            raise Exception("No text extracted from PDF")
        
        # Chunk the pages
        chunks = chunk_pages(pages, pages_per_chunk)
        
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
                    "total_chunks": len(chunks)
                }
            )
            
            processed_chunks.append({
                "doc_id": doc_id,
                "chunk_number": i + 1,
                "pages": f"{chunk['start_page']}-{chunk['end_page']}"
            })
        
        return {
            "success": True,
            "source_name": source_name,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "pages_per_chunk": pages_per_chunk,
            "processed_chunks": processed_chunks
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

