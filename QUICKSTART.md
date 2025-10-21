# Quick Start Guide

Get your RAG chatbot running in 3 minutes!

## Step 1: Verify Environment

Check that your `.env` file exists and has your OpenAI API key:

```bash
cat .env
```

Should show:
```
OPENAI_API_KEY=sk-proj-...
MCP_SERVER_URL=http://localhost:8001
```

## Step 2: Start the Backend Server

Open a terminal and run:

```bash
python scripts/start_server.py
```

You should see:
```
============================================================
Starting MCP FastAPI Server on http://localhost:8001
Upload Interface: http://localhost:8001/upload
============================================================
```

**Keep this terminal open!**

## Step 3: Upload a Document

Open your browser and go to:
```
http://localhost:8001/upload
```

1. Click "Choose File" or drag & drop a PDF/EPUB/TXT
2. Fill in:
   - **Source Name**: e.g., "Python Tutorial"
   - **Description**: e.g., "Introduction to Python programming"
   - **Pages per Chunk**: 3 (default is good)
3. Click **"Upload & Process Document"**
4. Wait for processing to complete (you'll see a success message)

## Step 4: Start the Chat Interface

Open a **new terminal** (keep the first one running!) and run:

```bash
python scripts/start_chat.py
```

You should see:
```
============================================================
Starting Chainlit Chat Interface on http://localhost:8000
============================================================
```

## Step 5: Chat with Your Knowledge Base

Open your browser and go to:
```
http://localhost:8000
```

Ask questions like:
- "What is in the Python tutorial?"
- "Explain loops from the documentation"
- "Summarize the key concepts"

The AI will automatically search your uploaded documents and provide answers with sources!

## Summary

You now have a fully functional RAG chatbot with:
- Document upload (PDF/EPUB/TXT)
- Semantic search
- AI-powered answers
- Source citations

## Common Tasks

### Add More Documents
Just go back to `http://localhost:8001/upload` and upload more files!

### Manage Documents
On the upload page, scroll down to see all your documents. You can:
- Toggle documents on/off (affects search)
- Delete documents
- View metadata

### Debug a Chunk
```bash
python scripts/inspect_chunk.py <chunk_id>
```

### Stop the Servers
Press `Ctrl+C` in each terminal window.

## Troubleshooting

**Import errors?**
Make sure you're in the project directory:
```bash
cd /Users/alessandrovanzo/nlp_chat
```

**Database not found?**
It will be created automatically on first run.

**Port already in use?**
Kill existing processes:
```bash
lsof -ti:8001 | xargs kill  # Kill mcp_server
lsof -ti:8000 | xargs kill  # Kill chainlit_app
```

## Additional Information

For more details, see `README.md`.

