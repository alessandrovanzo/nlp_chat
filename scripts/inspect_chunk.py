#!/usr/bin/env python3
"""
Inspect a specific chunk by ID for debugging purposes
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from src.config import DB_PATH


def show_chunk(chunk_id):
    """Display a specific chunk by ID"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.content, c.start_page, c.end_page, 
               c.chunk_number, c.unit_name,
               d.title, d.description, d.source_type, d.total_chunks, d.active
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.id = ?
    """, (chunk_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"No chunk found with ID {chunk_id}")
        return
    
    chunk_id, content, start_page, end_page, chunk_number, unit_name, title, description, source_type, total_chunks, active = result
    
    print(f"\n{'='*100}")
    print(f"CHUNK DETAILS (DB ID: {chunk_id})")
    print(f"{'='*100}")
    print(f"Source: {title or 'Unknown'}")
    print(f"Description: {description or 'N/A'}")
    print(f"Type: {source_type or 'Unknown'}")
    print(f"Pages/Units: {start_page or '?'}-{end_page or '?'} ({unit_name or 'units'})")
    print(f"Chunk: {chunk_number or '?'}/{total_chunks or '?'}")
    print(f"Active: {'Yes' if active else 'No'}")
    print(f"\nContent length: {len(content)} characters")
    print(f"\n{'='*100}")
    print("FULL CONTENT:")
    print(f"{'='*100}")
    print(content)
    print(f"{'='*100}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        chunk_id = int(sys.argv[1])
        show_chunk(chunk_id)
    else:
        print("Usage: python scripts/inspect_chunk.py <chunk_id>")

