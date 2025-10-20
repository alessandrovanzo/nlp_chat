# Quick Start: PDF Upload Feature

## Installation

1. **Install new dependencies:**
```bash
pip install -r requirements.txt
```

This adds:
- `PyPDF2` for PDF text extraction
- `python-multipart` for file uploads

## Running All Services

You need **3 services** running:

### Terminal 1: MCP Server
```bash
python start_mcp_server.py
```
✅ Should show: "MCP Server running on http://localhost:8001"

### Terminal 2: Main Chat App
```bash
chainlit run app.py
```
✅ Should show: "Your app is available at http://localhost:8000"

### Terminal 3: PDF Upload App
```bash
./start_pdf_upload.sh
```
✅ Should show: "Your app is available at http://localhost:8002"

## Quick Test

1. **Open PDF Upload Interface**: http://localhost:8002
2. **Click the 📎 attachment button** (bottom left of chat)
3. **Select a PDF file** from your computer
4. **Provide information when prompted:**
   - Source Name: e.g., "Machine Learning Basics"
   - Description: e.g., "Introduction to ML algorithms"
   - Pages per Chunk: e.g., "3" (or any number 1-10)
5. **Wait for processing** - you'll see progress updates
6. **Success!** Your PDF is now in the knowledge base

## Testing the Search

1. **Open Main Chat App**: http://localhost:8000
2. **Ask a question** about your PDF content
3. **Watch the AI search** - it will show "🔍 Searching knowledge base..."
4. **See the results** - sources from your PDF will be displayed

Example queries:
- "What information do you have about [topic from PDF]?"
- "Search for [keyword from PDF]"
- "Tell me about [concept mentioned in PDF]"

## How It Works

```
PDF Upload → Text Extraction → Chunking → OpenAI Embedding → Database Storage
                                                                      ↓
User Query → OpenAI Embedding → Similarity Search → Retrieve Chunks → GPT-4 Answer
```

### Example Flow:

1. **Upload**: 12-page PDF about Python
2. **Chunk**: With 3 pages/chunk → 4 chunks created
3. **Embed**: Each chunk gets a 1536-dim vector from OpenAI
4. **Store**: 4 entries added to SQLite database
5. **Search**: User asks "What's in the Python document?"
6. **Retrieve**: Semantic search finds relevant chunks
7. **Answer**: GPT-4 uses chunks to generate informed response

## Configuration

### Pages per Chunk

- **1-2 pages**: Very precise, many small chunks
  - ✅ Best for: Reference documents, dictionaries
  - ⚠️ May lose context across pages

- **3-5 pages**: Balanced (recommended)
  - ✅ Best for: Most documents, tutorials, guides
  - ✅ Good balance of precision and context

- **7-10 pages**: Large context per chunk
  - ✅ Best for: Books, long-form content
  - ⚠️ May be less precise, fewer total chunks

### Embedding Text

Each chunk embeds:
```
[Source Name]
[Description]

[Chunk Text]
```

This ensures metadata is part of the semantic search!

## Troubleshooting

### "Module not found: PyPDF2"
→ Run: `pip install -r requirements.txt`

### "Cannot connect to MCP server"
→ Make sure Terminal 1 is running the MCP server

### "PDF has no text"
→ PDF might be scanned images (needs OCR, not supported yet)

### "OpenAI API error"
→ Check your API key in `config.py`
→ Verify you have API credits

### Upload interface not loading
→ Make sure you're on http://localhost:8002
→ Check that port 8002 is not in use

## Cost Estimation

**OpenAI text-embedding-3-small pricing**: ~$0.02 per 1M tokens

Example:
- 100-page PDF
- ~500 words per page
- ~50,000 words total
- ~66,000 tokens
- **Cost: ~$0.0013** (less than a penny!)

Very affordable for most use cases.

## What's Next?

After uploading PDFs:
1. Try different chunk sizes to see what works best
2. Upload related documents to build a knowledge domain
3. Experiment with different search queries
4. Check the sidebar in the chat app to see retrieved sources

## Advanced Usage

### Multiple PDFs

Upload multiple related PDFs to create a comprehensive knowledge base:
- User manuals
- Research papers
- Documentation
- Books/chapters

They'll all be searchable together!

### Metadata Strategy

Good source names and descriptions help search:
- ✅ "Python FastAPI Guide - Web API Development Tutorial"
- ❌ "doc1.pdf"

The metadata is embedded with the content, improving semantic search!

## Files Added

New files in your project:
- `pdf_processor.py` - Core PDF processing logic
- `pdf_upload_app.py` - Chainlit upload interface
- `start_pdf_upload.sh` - Startup script
- `SETUP_PDF_UPLOAD.md` - Detailed documentation
- `QUICK_START_PDF.md` - This guide!

Modified files:
- `requirements.txt` - Added PyPDF2 and python-multipart
- `mcp_server.py` - Now uses real OpenAI embeddings
- `README.md` - Updated with PDF feature info

---

**Ready to go!** 🚀

Run the three services and start uploading PDFs!

