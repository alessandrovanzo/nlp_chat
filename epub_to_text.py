#!/usr/bin/env python3
"""
Simple EPUB to Text Converter
Extracts all text from an EPUB file and saves it to a text file
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sys


def epub_to_text(epub_file_path, output_file_path):
    """
    Convert EPUB to plain text file
    
    Args:
        epub_file_path: Path to the EPUB file
        output_file_path: Path to save the output text file
    """
    print(f"Reading EPUB file: {epub_file_path}")
    
    try:
        # Read the EPUB file
        book = epub.read_epub(epub_file_path)
        
        # Get all document items (chapters/sections)
        items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        
        if len(items) == 0:
            print("ERROR: EPUB file is empty or corrupted")
            return False
        
        print(f"Found {len(items)} chapters/sections")
        
        # Open output file for writing
        with open(output_file_path, 'w', encoding='utf-8') as f:
            chapter_count = 0
            
            for idx, item in enumerate(items, 1):
                # Parse HTML content using BeautifulSoup
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Extract text (same method as in pdf_processor.py)
                text = soup.get_text(separator='\n', strip=True)
                
                # Only write non-empty chapters
                if text:
                    chapter_count += 1
                    
                    # Write chapter separator
                    f.write(f"\n{'='*80}\n")
                    f.write(f"CHAPTER/SECTION {chapter_count} (Item {idx})\n")
                    f.write(f"{'='*80}\n\n")
                    
                    # Write the extracted text
                    f.write(text)
                    f.write("\n\n")
                    
                    print(f"  Processed chapter {chapter_count}: {len(text)} characters")
        
        print(f"\nSuccess! Extracted {chapter_count} chapters")
        print(f"Output saved to: {output_file_path}")
        return True
        
    except ebooklib.epub.EpubException as e:
        print(f"ERROR: Corrupted or invalid EPUB file: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Define file paths
    epub_file = "taleb.epub"
    output_file = "taleb_extracted.txt"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        epub_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("="*80)
    print("EPUB to Text Converter")
    print("="*80)
    print(f"Input:  {epub_file}")
    print(f"Output: {output_file}")
    print("="*80 + "\n")
    
    # Convert the file
    success = epub_to_text(epub_file, output_file)
    
    if success:
        print("\nDone!")
        sys.exit(0)
    else:
        print("\nFailed to convert EPUB file")
        sys.exit(1)

