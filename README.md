# NLP Chainlit Chatbot with RAG

A sophisticated chatbot built with Chainlit, OpenAI's GPT-3.5, and RAG (Retrieval Augmented Generation) using MCP (Model Context Protocol).

## Architecture

- **Frontend**: Chainlit web interface with streaming responses
- **Backend**: FastAPI MCP server with RAG capabilities
- **Database**: SQLite with vector embeddings for semantic search
- **LLM**: OpenAI GPT-4 Turbo with function calling

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Initialize the database (optional - will auto-initialize on first run):
```bash
python3 init_db.py
```

## Running the App

### Option 1: Run Everything at Once (Recommended)
```bash
./run_all.sh
```
This will start both the MCP server and Chainlit app automatically.

### Option 2: Run Separately

You need to run **both** the MCP server and the Chainlit app:

**Terminal 1: Start MCP Server**
```bash
python3 start_mcp_server.py
```
This will start the FastAPI MCP server on `http://localhost:8001`

**Terminal 2: Start Chainlit App**
```bash
chainlit run app.py
```
This will start the chatbot interface on `http://localhost:8000`

## Features

- 🤖 **Real-time streaming responses** from GPT-4 Turbo
- 🔍 **Semantic search** using vector embeddings
- 📚 **RAG (Retrieval Augmented Generation)** - AI searches knowledge base automatically
- 🛠️ **MCP Protocol** - Standard protocol for tool integration
- 💾 **SQLite vector database** with fake embeddings
- 🎯 **Function calling** - AI decides when to search the knowledge base
- 💬 **Conversation history** - Maintains context across messages

## How It Works

1. User asks a question in the Chainlit interface
2. GPT-4 determines if it needs information from the knowledge base
3. If needed, it calls the `search_knowledge_base` function via MCP
4. FastAPI backend performs vector similarity search in SQLite
5. Relevant documents are retrieved and sent back to GPT-4
6. GPT-4 generates a response using the retrieved context
7. Response is streamed back to the user in real-time

## Knowledge Base

The database comes pre-populated with 10 sample documents covering:
- Python Programming
- Machine Learning
- FastAPI Framework
- Vector Databases
- Natural Language Processing
- SQLite
- REST API Design
- Embeddings and Semantic Search
- Async Programming
- RAG (Retrieval Augmented Generation)

## API Endpoints

### MCP Server (Port 8001)
- `GET /` - Health check
- `GET /mcp/tools` - List available tools
- `POST /mcp/tools/call` - Execute a tool
- `POST /initialize` - Re-initialize database with sample data

## Testing the RAG

Try asking questions like:
- "What is RAG?"
- "Tell me about FastAPI"
- "How do vector databases work?"
- "Explain async programming in Python"

The AI will automatically search the knowledge base and provide informed answers!

