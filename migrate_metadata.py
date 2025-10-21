"""
Migrate metadata from JSON column to separate columns
"""
import sqlite3
import json

DB_PATH = "rag_database.db"

def migrate_database():
    """Migrate metadata fields to separate columns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Create new table with separate columns
    print("1. Creating new table structure...")
    cursor.execute("""
        CREATE TABLE documents_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            title TEXT,
            description TEXT,
            source_type TEXT,
            start_page INTEGER,
            end_page INTEGER,
            chunk_number INTEGER,
            total_chunks INTEGER,
            unit_name TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Get all documents from old table
    print("2. Fetching existing documents...")
    cursor.execute("SELECT id, content, embedding, metadata, created_at FROM documents")
    rows = cursor.fetchall()
    print(f"   Found {len(rows)} documents to migrate")
    
    # Migrate data
    print("3. Migrating data to new structure...")
    migrated = 0
    for row in rows:
        doc_id, content, embedding, metadata_json, created_at = row
        
        # Parse metadata
        metadata = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                print(f"   Warning: Could not parse metadata for document {doc_id}")
        
        # Insert into new table
        cursor.execute("""
            INSERT INTO documents_new 
            (id, content, embedding, title, description, source_type, 
             start_page, end_page, chunk_number, total_chunks, unit_name, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            content,
            embedding,
            metadata.get('title'),
            metadata.get('description'),
            metadata.get('source_type'),
            metadata.get('start_page'),
            metadata.get('end_page'),
            metadata.get('chunk_number'),
            metadata.get('total_chunks'),
            metadata.get('unit_name'),
            metadata.get('active', True),
            created_at
        ))
        migrated += 1
        if migrated % 50 == 0:
            print(f"   Migrated {migrated}/{len(rows)} documents...")
    
    print(f"   ✓ Migrated all {migrated} documents")
    
    # Drop old table and rename new one
    print("4. Replacing old table with new structure...")
    cursor.execute("DROP TABLE documents")
    cursor.execute("ALTER TABLE documents_new RENAME TO documents")
    
    # Create indexes for common query patterns
    print("5. Creating indexes for better query performance...")
    cursor.execute("CREATE INDEX idx_source_type ON documents(source_type)")
    cursor.execute("CREATE INDEX idx_title ON documents(title)")
    cursor.execute("CREATE INDEX idx_chunk_number ON documents(chunk_number)")
    cursor.execute("CREATE INDEX idx_active ON documents(active)")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print(f"   - Migrated {migrated} documents")
    print(f"   - Removed metadata JSON column")
    print(f"   - Added separate columns for each field")
    print(f"   - Created performance indexes")

def verify_migration():
    """Verify the migration was successful"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Show new schema
    print("\nNew schema:")
    cursor.execute("PRAGMA table_info(documents)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")
    
    # Show counts by source type
    print("\nDocument counts by source type:")
    cursor.execute("SELECT source_type, COUNT(*) FROM documents GROUP BY source_type")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} documents")
    
    # Show sample records
    print("\nSample EPUB record:")
    cursor.execute("""
        SELECT id, title, source_type, start_page, end_page, chunk_number, total_chunks, unit_name, active
        FROM documents WHERE source_type = 'epub' LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"  ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Source: {row[2]}")
        print(f"  Pages: {row[3]}-{row[4]}")
        print(f"  Chunk: {row[5]}/{row[6]}")
        print(f"  Unit: {row[7]}")
        print(f"  Active: {row[8]}")
    
    print("\nSample PDF record:")
    cursor.execute("""
        SELECT id, title, source_type, start_page, end_page, chunk_number, total_chunks, unit_name, active
        FROM documents WHERE source_type = 'pdf' LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"  ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Source: {row[2]}")
        print(f"  Pages: {row[3]}-{row[4]}")
        print(f"  Chunk: {row[5]}/{row[6]}")
        print(f"  Unit: {row[7]}")
        print(f"  Active: {row[8]}")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()
    verify_migration()

