# PDF Upload Feature - Setup Guide

This document describes the new PDF upload functionality added to the RAG chat application.

## Overview

The PDF upload feature allows you to:
- Upload PDF documents to your knowledge base
- Configure chunking size (1-10 pages per chunk)
- Add metadata (source name and description)
- Automatically generate embeddings using OpenAI's `text-embedding-3-small` model
- Store documents in the vector database for semantic search

## Architecture

### Components

1. **pdf_processor.py** - Core PDF processing module
   - Extracts text from PDFs using PyPDF2
   - Chunks pages into configurable groups
   - Generates OpenAI embeddings
   - Stores chunks in SQLite database

2. **pdf_upload_app.py** - Chainlit-based upload interface
   - Conversational UI for PDF uploads
   - Collects metadata (source name, description)
   - Configurable chunking (1-10 pages per chunk)
   - Progress feedback and error handling

3. **mcp_server.py** - Updated to use real OpenAI embeddings
   - Now uses OpenAI embeddings for queries
   - Matches embedding space of uploaded PDFs
   - Falls back to fake embeddings if API fails

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `PyPDF2==3.0.1` - PDF text extraction
- `python-multipart==0.0.6` - File upload support

### 2. Verify OpenAI API Key

Make sure your OpenAI API key is set in `config.py`:

```python
oai_key = 'your-openai-api-key'
```

## Usage

### Starting the Applications

You'll need to run **three separate services**:

#### Terminal 1: MCP Server
```bash
python mcp_server.py
# Runs on http://localhost:8001
```

#### Terminal 2: Main Chat Application
```bash
chainlit run app.py
# Runs on http://localhost:8000
```

#### Terminal 3: PDF Upload Application
```bash
./start_pdf_upload.sh
# OR
chainlit run pdf_upload_app.py --port 8002
# Runs on http://localhost:8002
```

### Uploading a PDF

1. Open the PDF upload interface at `http://localhost:8002`
2. Click the attachment button (📎) and select a PDF file
3. Follow the prompts to provide:
   - **Source Name**: A title for the document (e.g., "Python Tutorial")
   - **Description**: Brief description of content (e.g., "Comprehensive Python programming guide")
   - **Pages per Chunk**: Number (1-10) - how many pages to group together (default: 3)
4. The app will process the PDF and add it to the knowledge base
5. You can now search for this content in the main chat app!

### How It Works

#### 1. Text Extraction
```python
# Each page is extracted separately
pages = extract_text_from_pdf(pdf_file_path)
```

#### 2. Chunking
```python
# Pages are grouped into chunks of N pages
chunks = chunk_pages(pages, pages_per_chunk=3)
# Example: 10-page PDF with pages_per_chunk=3
# -> Chunk 1: Pages 1-3
# -> Chunk 2: Pages 4-6
# -> Chunk 3: Pages 7-9
# -> Chunk 4: Page 10
```

#### 3. Embedding Generation
```python
# Text to embed combines metadata + content
text_to_embed = f"{source_name}\n{description}\n\n{chunk_text}"

# Create embedding with OpenAI
response = client.embeddings.create(
    input=text_to_embed,
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding
```

#### 4. Database Storage
```python
# Stored in SQLite with metadata
metadata = {
    "title": source_name,
    "description": description,
    "source_type": "pdf",
    "start_page": 1,
    "end_page": 3,
    "chunk_number": 1,
    "total_chunks": 4
}
```

## Database Schema

Documents are stored in the `documents` table:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| content | TEXT | The chunk text content |
| embedding | TEXT | JSON array of embedding vector |
| metadata | TEXT | JSON object with title, description, pages, etc. |
| created_at | TIMESTAMP | Auto-generated timestamp |

## Embedding Model

- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536
- **Cost**: ~$0.02 per 1M tokens
- **Speed**: Fast, suitable for real-time processing

## Configuration

### Chunking Strategy

The `pages_per_chunk` parameter controls document granularity:

- **Small chunks (1-3 pages)**: Better precision, more chunks to search
- **Large chunks (7-10 pages)**: More context per chunk, fewer total chunks

Recommended: **3 pages** balances precision and context.

### Embedding Text Format

Each chunk embeds: `source_name + description + chunk_text`

This ensures:
1. Source context is included in the embedding
2. Description helps with semantic matching
3. Chunk text provides the actual content

## API Reference

### `pdf_processor.py`

#### `extract_text_from_pdf(pdf_file_path: str) -> List[str]`
Extracts text from PDF, one string per page.

#### `chunk_pages(pages: List[str], pages_per_chunk: int = 3) -> List[Dict]`
Groups pages into chunks with metadata.

#### `create_embedding(text: str) -> List[float]`
Generates OpenAI embedding vector.

#### `store_chunk_in_db(...) -> int`
Stores chunk with embedding in database, returns doc ID.

#### `process_pdf(...) -> Dict[str, Any]`
Main function that orchestrates the entire pipeline.

## Troubleshooting

### PDF Text Extraction Issues
- Some PDFs (scanned images) may not have extractable text
- Consider using OCR for scanned documents
- Complex layouts may have text ordering issues

### OpenAI API Errors
- Verify API key is correct in `config.py`
- Check API quota/billing
- The system falls back to fake embeddings on error (for search only)

### Database Issues
- Ensure `rag_database.db` exists (run `python init_db.py` if needed)
- Check write permissions in the directory

## Future Enhancements

Potential improvements:
- [ ] Support for other file formats (DOCX, TXT, MD)
- [ ] OCR for scanned PDFs
- [ ] Batch upload multiple files
- [ ] Preview extracted text before processing
- [ ] Edit/delete existing documents
- [ ] Advanced chunking strategies (semantic, overlap)
- [ ] Progress bar for large files

## Security Notes

- The OpenAI API key is stored in plain text in `config.py`
- Consider using environment variables for production
- Uploaded files are temporarily stored in system temp directory
- No authentication on upload interface - add auth for production use

## Testing

To test the system:

1. Upload a test PDF
2. Check the processing results
3. Go to the main chat app (port 8000)
4. Ask questions about the PDF content
5. Verify the system retrieves relevant chunks

Example test query:
```
"What information do you have about [topic from your PDF]?"
```

## Support

For issues or questions:
- Check console logs for errors
- Verify all three services are running
- Confirm OpenAI API key is valid
- Check database file exists and has correct permissions

