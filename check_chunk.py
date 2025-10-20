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
        SELECT id, content, metadata 
        FROM documents 
        WHERE id = ?
    """, (doc_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"No chunk found with ID {doc_id}")
        return
    
    doc_id, content, metadata_str = result
    metadata = json.loads(metadata_str)
    
    print(f"\n{'='*100}")
    print(f"CHUNK DETAILS (DB ID: {doc_id})")
    print(f"{'='*100}")
    print(f"Source: {metadata.get('title', 'Unknown')}")
    print(f"Type: {metadata.get('source_type', 'Unknown')}")
    print(f"Pages/Chapters: {metadata.get('start_page', '?')}-{metadata.get('end_page', '?')} ({metadata.get('unit_name', 'units')})")
    print(f"Chunk: {metadata.get('chunk_number', '?')}/{metadata.get('total_chunks', '?')}")
    if 'split_part' in metadata:
        print(f"Split: {metadata['split_part']}")
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

