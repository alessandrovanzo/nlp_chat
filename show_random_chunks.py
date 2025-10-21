#!/usr/bin/env python3
"""
Show random chunks from the RAG database
"""

import sqlite3
import json

DB_PATH = "rag_database.db"

def show_random_chunks(n=10):
    """Display n random chunks from the database"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get random chunks
    cursor.execute("""
        SELECT id, content, title, source_type, start_page, end_page, 
               chunk_number, total_chunks, unit_name, active
        FROM documents 
        ORDER BY RANDOM() 
        LIMIT ?
    """, (n,))
    
    chunks = cursor.fetchall()
    conn.close()
    
    if not chunks:
        print("No chunks found in database")
        return
    
    print(f"\n{'='*100}")
    print(f"SHOWING {len(chunks)} RANDOM CHUNKS FROM DATABASE")
    print(f"{'='*100}\n")
    
    for idx, (doc_id, content, title, source_type, start_page, end_page, chunk_number, total_chunks, unit_name, active) in enumerate(chunks, 1):
        
        print(f"\n{'─'*100}")
        print(f"CHUNK #{idx} (DB ID: {doc_id})")
        print(f"{'─'*100}")
        print(f"Source: {title or 'Unknown'}")
        print(f"Type: {source_type or 'Unknown'}")
        print(f"Pages/Chapters: {start_page or '?'}-{end_page or '?'} ({unit_name or 'units'})")
        print(f"Chunk: {chunk_number or '?'}/{total_chunks or '?'}")
        print(f"Active: {'Yes' if active else 'No'}")
        print(f"\nContent length: {len(content)} characters")
        print(f"\nFULL CONTENT:")
        print(f"{'─'*100}")
        print(content)
        print(f"{'─'*100}")

if __name__ == "__main__":
    show_random_chunks(10)

