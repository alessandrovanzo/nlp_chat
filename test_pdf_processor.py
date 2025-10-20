"""
Test script for PDF processing functionality
This script can be used to test PDF processing without the UI
"""
import sys
from pdf_processor import (
    extract_text_from_pdf,
    chunk_pages,
    create_embedding,
    process_pdf
)

def test_extraction(pdf_path: str):
    """Test PDF text extraction"""
    print(f"\n{'='*60}")
    print("TEST 1: PDF Text Extraction")
    print(f"{'='*60}")
    
    try:
        pages = extract_text_from_pdf(pdf_path)
        print(f"✅ Successfully extracted {len(pages)} pages")
        
        # Show first page preview
        if pages:
            preview = pages[0][:200] + "..." if len(pages[0]) > 200 else pages[0]
            print(f"\nFirst page preview:\n{preview}")
        
        return pages
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_chunking(pages: list, pages_per_chunk: int = 3):
    """Test page chunking"""
    print(f"\n{'='*60}")
    print(f"TEST 2: Chunking (pages_per_chunk={pages_per_chunk})")
    print(f"{'='*60}")
    
    try:
        chunks = chunk_pages(pages, pages_per_chunk)
        print(f"✅ Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"  - Pages: {chunk['start_page']}-{chunk['end_page']}")
            print(f"  - Text length: {len(chunk['text'])} characters")
            preview = chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text']
            print(f"  - Preview: {preview}")
        
        return chunks
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_embedding(text: str):
    """Test OpenAI embedding creation"""
    print(f"\n{'='*60}")
    print("TEST 3: OpenAI Embedding Creation")
    print(f"{'='*60}")
    
    try:
        # Use a short sample text
        sample_text = text[:500] if len(text) > 500 else text
        print(f"Creating embedding for {len(sample_text)} characters...")
        
        embedding = create_embedding(sample_text)
        print(f"✅ Successfully created embedding")
        print(f"  - Vector dimension: {len(embedding)}")
        print(f"  - First 5 values: {embedding[:5]}")
        
        return embedding
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure your OpenAI API key is correct in config.py")
        return None

def test_full_pipeline(pdf_path: str, source_name: str, description: str, pages_per_chunk: int = 3):
    """Test the full PDF processing pipeline"""
    print(f"\n{'='*60}")
    print("TEST 4: Full Processing Pipeline")
    print(f"{'='*60}")
    
    print(f"\nProcessing:")
    print(f"  - File: {pdf_path}")
    print(f"  - Source: {source_name}")
    print(f"  - Description: {description}")
    print(f"  - Pages per chunk: {pages_per_chunk}")
    
    try:
        result = process_pdf(
            pdf_file_path=pdf_path,
            source_name=source_name,
            description=description,
            pages_per_chunk=pages_per_chunk
        )
        
        if result["success"]:
            print(f"\n✅ SUCCESS!")
            print(f"  - Total pages: {result['total_pages']}")
            print(f"  - Total chunks: {result['total_chunks']}")
            print(f"  - Chunks created:")
            for chunk_info in result['processed_chunks']:
                print(f"    • Chunk {chunk_info['chunk_number']}: Pages {chunk_info['pages']} → DB ID: {chunk_info['doc_id']}")
        else:
            print(f"\n❌ FAILED: {result['error']}")
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("PDF PROCESSOR TEST SUITE")
    print("="*60)
    
    # Check if PDF path provided
    if len(sys.argv) < 2:
        print("\n❌ Error: No PDF file provided")
        print("\nUsage:")
        print("  python test_pdf_processor.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_pdf_processor.py ~/Downloads/sample.pdf")
        print("\nOptional arguments:")
        print("  python test_pdf_processor.py <pdf> <source_name> <description> <pages_per_chunk>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    source_name = sys.argv[2] if len(sys.argv) > 2 else "Test Document"
    description = sys.argv[3] if len(sys.argv) > 3 else "Test description for PDF processing"
    pages_per_chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    
    # Run tests
    print("\n🔍 Running tests...\n")
    
    # Test 1: Extraction
    pages = test_extraction(pdf_path)
    if not pages:
        print("\n❌ Extraction failed, stopping tests")
        return
    
    # Test 2: Chunking
    chunks = test_chunking(pages, pages_per_chunk)
    if not chunks:
        print("\n❌ Chunking failed, stopping tests")
        return
    
    # Test 3: Embedding (single test)
    if chunks:
        test_embedding(chunks[0]['text'])
    
    # Test 4: Full pipeline
    test_full_pipeline(pdf_path, source_name, description, pages_per_chunk)
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

