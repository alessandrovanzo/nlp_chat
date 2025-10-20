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
        SELECT id, content, metadata 
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
    
    for idx, (doc_id, content, metadata_str) in enumerate(chunks, 1):
        metadata = json.loads(metadata_str)
        
        print(f"\n{'─'*100}")
        print(f"CHUNK #{idx} (DB ID: {doc_id})")
        print(f"{'─'*100}")
        print(f"Source: {metadata.get('title', 'Unknown')}")
        print(f"Type: {metadata.get('source_type', 'Unknown')}")
        print(f"Pages/Chapters: {metadata.get('start_page', '?')}-{metadata.get('end_page', '?')} ({metadata.get('unit_name', 'units')})")
        print(f"Chunk: {metadata.get('chunk_number', '?')}/{metadata.get('total_chunks', '?')}")
        if 'split_part' in metadata:
            print(f"Split: {metadata['split_part']}")
        print(f"\nContent length: {len(content)} characters")
        print(f"\nFULL CONTENT:")
        print(f"{'─'*100}")
        print(content)
        print(f"{'─'*100}")

if __name__ == "__main__":
    show_random_chunks(10)

