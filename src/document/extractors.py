"""
Text extraction from various document formats (PDF, EPUB, TXT)
"""
import os
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List


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
        from .chunker import split_text_by_words
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
        from .chunker import split_text_by_words
        pages = split_text_by_words(content, words_per_page=300)
        
        return pages
                
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(txt_file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            
            from .chunker import split_text_by_words
            pages = split_text_by_words(content, words_per_page=300)
            return pages
        except Exception as e:
            raise Exception(f"Error reading TXT file with alternative encoding: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")

