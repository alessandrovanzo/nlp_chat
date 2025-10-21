#!/usr/bin/env python3
"""
Check a specific chunk by ID
"""

import sqlite3
import json

DB_PATH = "rag_database.db"

def show_chunk(doc_id):
    """Display a specific chunk by ID"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, content, title, source_type, start_page, end_page, 
               chunk_number, total_chunks, unit_name, active
        FROM documents 
        WHERE id = ?
    """, (doc_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"No chunk found with ID {doc_id}")
        return
    
    doc_id, content, title, source_type, start_page, end_page, chunk_number, total_chunks, unit_name, active = result
    
    print(f"\n{'='*100}")
    print(f"CHUNK DETAILS (DB ID: {doc_id})")
    print(f"{'='*100}")
    print(f"Source: {title or 'Unknown'}")
    print(f"Type: {source_type or 'Unknown'}")
    print(f"Pages/Chapters: {start_page or '?'}-{end_page or '?'} ({unit_name or 'units'})")
    print(f"Chunk: {chunk_number or '?'}/{total_chunks or '?'}")
    print(f"Active: {'Yes' if active else 'No'}")
    print(f"\nContent length: {len(content)} characters")
    print(f"\n{'='*100}")
    print("FULL CONTENT:")
    print(f"{'='*100}")
    print(content)
    print(f"{'='*100}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        doc_id = int(sys.argv[1])
        show_chunk(doc_id)
    else:
        print("Usage: python check_chunk.py <doc_id>")

