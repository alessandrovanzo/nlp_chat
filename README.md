# NLP Chat - RAG-based Knowledge Base Chatbot

A sophisticated RAG (Retrieval-Augmented Generation) chatbot with document upload capabilities. Upload PDF, EPUB, and TXT documents to create a searchable knowledge base powered by OpenAI embeddings.

## Features

- **Multi-format Support**: Upload PDF, EPUB, and TXT documents
- **Semantic Search**: Uses OpenAI embeddings for intelligent document retrieval
- **Chat Interface**: Beautiful Chainlit-powered chat UI
- **Web Upload**: Browser-based document upload and management
- **Source Management**: Toggle documents on/off, view metadata, delete sources
- **MCP Protocol**: FastAPI backend implements Model Context Protocol for tool calling

## Project Structure

```
nlp_chat/
├── src/                          # Main application code
│   ├── config.py                 # Configuration (loads from .env)
│   ├── chat/                     # Chainlit chat interface
│   │   └── app.py
│   ├── server/                   # FastAPI backend
│   │   ├── api.py
│   │   └── static/
│   │       └── upload.html       # Document upload interface
│   ├── document/                 # Document processing
│   │   ├── extractors.py         # Extract text from files
│   │   ├── chunker.py            # Chunk text for embedding
│   │   └── embeddings.py         # Generate OpenAI embeddings
│   └── database/                 # Database operations
│       ├── models.py             # DB operations and document processing
│       └── init_db.py            # Database initialization
├── scripts/                      # Utility scripts
│   ├── start_server.py           # Start FastAPI server
│   ├── start_chat.py             # Start Chainlit chat
│   └── inspect_chunk.py          # Debug utility
├── data/                         # Data directory
│   └── rag_database.db           # SQLite database
├── .env                          # Environment variables (create from .env.example)
├── .env.example                  # Template for environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your-openai-api-key-here
MCP_SERVER_URL=http://localhost:8001
```

### 3. Initialize Database (Optional)

The database will be created automatically when you first start the server, but you can initialize it manually:

```bash
python -m src.database.init_db
```

## Usage

### Start the Backend Server

```bash
python scripts/start_server.py
```

The server will start on `http://localhost:8001`

**Upload Interface**: `http://localhost:8001/upload`

### Start the Chat Interface

In a separate terminal:

```bash
python scripts/start_chat.py
```

The chat interface will start on `http://localhost:8000`

### Upload Documents

1. Navigate to `http://localhost:8001/upload`
2. Upload a PDF, EPUB, or TXT file
3. Provide a source name and description
4. Adjust chunking settings (pages per chunk)
5. Submit and wait for processing

### Chat with Your Knowledge Base

1. Navigate to `http://localhost:8000`
2. Ask questions related to your uploaded documents
3. The AI will automatically search the knowledge base and provide answers with sources

## Configuration

### Chunking Settings

- **Pages per Chunk**: Controls how many pages are grouped together (1-10)
  - Smaller chunks: More precise retrieval, cheaper embeddings, less context
  - Larger chunks: More context, more expensive, potentially less precise

- **Prepend Metadata**: Includes document title and description in embeddings
  - Helps with retrieval when searching by document topic
  - Slightly increases embedding costs

### Document Processing

- **PDF**: Uses actual page numbers
- **EPUB**: Converts to virtual pages (300 words = 1 page)
- **TXT**: Converts to virtual pages (300 words = 1 page)

## Database Schema

### `documents` Table
- Stores document metadata
- Tracks active/inactive status
- Maintains chunk count

### `chunks` Table
- Stores document chunks with embeddings
- Links to parent document (CASCADE DELETE)
- Includes page ranges and metadata

## Utility Scripts

### Inspect a Chunk

```bash
python scripts/inspect_chunk.py <chunk_id>
```

Displays detailed information about a specific chunk, including content and metadata.

## Security

- API keys stored in `.env` (excluded from git)
- Never commit `.env` file
- Database excluded from git

## Technology Stack

- **Frontend**: Chainlit (chat UI)
- **Backend**: FastAPI
- **Database**: SQLite with foreign keys
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: GPT-4 Turbo (configurable)
- **Document Processing**: PyPDF2, ebooklib, BeautifulSoup4

## Architecture

```
User Query → Chainlit Chat Interface
              ↓
          OpenAI GPT-4 (with function calling)
              ↓
       [Detects need for knowledge]
              ↓
          FastAPI MCP Server
              ↓
       Generate Query Embedding (OpenAI)
              ↓
       Search Database (Cosine Similarity)
              ↓
       Return Top K Results with Sources
              ↓
          Back to GPT-4 for Answer
              ↓
       Display Answer with Sources
```

## API Endpoints

### FastAPI Server (Port 8001)

- `GET /` - Health check
- `GET /upload` - Upload interface (HTML)
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/tools/call` - Execute MCP tool
- `POST /upload-pdf` - Upload and process document
- `GET /sources` - List all documents
- `POST /sources/toggle` - Toggle document active status
- `POST /sources/delete` - Delete document and chunks

## Troubleshooting

### Database Issues

If you encounter database errors, try reinitializing:

```bash
rm data/rag_database.db
python -m src.database.init_db
```

### Import Errors

Make sure you're running scripts from the project root directory.

### Token Limit Errors

If documents are too large, the system will automatically split chunks. You can also:
- Reduce "pages per chunk" setting
- Turn off "prepend metadata"

## License

This project is provided as-is for educational and personal use.

## Acknowledgments

Built with:
- [Chainlit](https://github.com/Chainlit/chainlit) - Chat UI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [OpenAI](https://openai.com/) - Embeddings and LLM

