# NLP Chat - RAG Chatbot

A conversational AI assistant powered by Retrieval Augmented Generation (RAG) that answers questions using your own document knowledge base.

## Functionality

Upload documents (PDF, EPUB, TXT) and chat with an AI that searches through them to provide accurate, source-cited answers. The system:

- **Document Management**: Upload and process documents with automatic chunking and embedding
- **Semantic Search**: Find relevant information using OpenAI embeddings and vector similarity
- **Intelligent Chat**: LLM automatically decides when to search the knowledge base and synthesizes answers with sources
- **Source Citations**: All answers include references to the original documents

## Technical Overview

**Architecture**: Two-service RAG system with FastAPI backend and Chainlit frontend

**Stack**: 
- `chainlit` - Chat interface with streaming responses
- `fastapi` + `uvicorn` - MCP server for document upload and search tools
- `openai` - Embeddings (text-embedding-3-small) and completions (GPT-4)
- `sqlalchemy` - SQLite database for documents, chunks, and embeddings
- Document processing: PyPDF2, ebooklib, BeautifulSoup

**Structure**:
```
src/
├── chainlit_app/       # Chat UI and LLM integration
├── mcp_server/         # FastAPI server with tool endpoints
├── database/           # SQLAlchemy models and operations
└── document_processing/ # Extractors, chunkers, embeddings

scripts/                # Entry points (start_chat.py, start_server.py)
data/                   # SQLite database
```

**Workflow**: Upload documents → Extract & chunk text → Generate embeddings → Store in database → Chat queries trigger semantic search → LLM synthesizes answers with sources

## Quick Start

```bash
# 1. Set up environment
cp env.template .env
# Add your OpenAI API key to .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start backend server (Terminal 1)
python scripts/start_server.py

# 4. Upload documents
# Open http://localhost:8001/upload

# 5. Start chat interface (Terminal 2)
python scripts/start_chat.py

# 6. Chat with your documents
# Open http://localhost:8000
```

See `QUICKSTART.md` for detailed instructions or `DOCKER_QUICKSTART.md` for Docker setup.

