#!/usr/bin/env python3
"""
Analyze chunk quality in the database
"""

import sqlite3
import json
import re

DB_PATH = "rag_database.db"

def analyze_chunks():
    """Analyze the quality of chunks in the database"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, content, source_type FROM documents")
    all_chunks = cursor.fetchall()
    conn.close()
    
    print(f"\n{'='*100}")
    print(f"CHUNK QUALITY ANALYSIS")
    print(f"{'='*100}\n")
    print(f"Total chunks in database: {len(all_chunks)}\n")
    
    # Patterns that indicate low-quality content
    junk_patterns = [
        r'Click\s+here',
        r'Double-tap or move your cursor',
        r'to return to the text',
        r'click to zoom',
    ]
    
    short_chunks = []
    junk_chunks = []
    good_chunks = []
    
    for doc_id, content, source_type in all_chunks:
        length = len(content)
        
        # Check if it's junk
        is_junk = any(re.search(pattern, content, re.IGNORECASE) for pattern in junk_patterns)
        
        if is_junk:
            junk_chunks.append((doc_id, length, source_type))
        elif length < 500:  # Very short chunks might be problematic
            short_chunks.append((doc_id, length, source_type))
        else:
            good_chunks.append((doc_id, length, source_type))
    
    print(f"Chunks with junk content (navigation/formatting): {len(junk_chunks)}")
    print(f"Very short chunks (<500 chars): {len(short_chunks)}")
    print(f"Good quality chunks: {len(good_chunks)}")
    
    if junk_chunks:
        print(f"\n{'─'*100}")
        print("JUNK CHUNKS (showing first 20):")
        print(f"{'─'*100}")
        for doc_id, length, source_type in junk_chunks[:20]:
            print(f"  ID {doc_id}: {length} chars ({source_type})")
    
    if short_chunks:
        print(f"\n{'─'*100}")
        print("SHORT CHUNKS (showing first 20):")
        print(f"{'─'*100}")
        for doc_id, length, source_type in short_chunks[:20]:
            print(f"  ID {doc_id}: {length} chars ({source_type})")
    
    # Statistics
    print(f"\n{'─'*100}")
    print("STATISTICS:")
    print(f"{'─'*100}")
    print(f"Percentage of junk chunks: {len(junk_chunks)/len(all_chunks)*100:.1f}%")
    print(f"Percentage of short chunks: {len(short_chunks)/len(all_chunks)*100:.1f}%")
    print(f"Percentage of good chunks: {len(good_chunks)/len(all_chunks)*100:.1f}%")
    
    # Average lengths
    if junk_chunks:
        avg_junk = sum(l for _, l, _ in junk_chunks) / len(junk_chunks)
        print(f"\nAverage junk chunk length: {avg_junk:.0f} chars")
    if good_chunks:
        avg_good = sum(l for _, l, _ in good_chunks) / len(good_chunks)
        print(f"Average good chunk length: {avg_good:.0f} chars")

if __name__ == "__main__":
    analyze_chunks()

