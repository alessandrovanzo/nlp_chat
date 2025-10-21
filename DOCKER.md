# Docker Setup Guide

Run your RAG chatbot with Docker in 3 simple steps!

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

## Quick Start

### 1. Create your `.env` file

```bash
cat > .env << EOL
OPENAI_API_KEY=sk-proj-your-api-key-here
MCP_SERVER_URL=http://mcp-server:8001
EOL
```

Or copy from the example:
```bash
cp .env.example .env
# Then edit .env with your API key
```

### 2. Start the services

**Option A: Using the helper script (recommended)**
```bash
./docker-start.sh
```

**Option B: Direct docker-compose**
```bash
docker-compose up --build
```

That's it! The system will:
- ✅ Build the Docker image
- ✅ Create the database automatically (if it doesn't exist)
- ✅ Create the `.files` directory for Chainlit (if it doesn't exist)
- ✅ Start both services

### First Run Initialization

On the **first run**, the system automatically:

1. **Creates `data/` directory** - for the SQLite database
2. **Initializes the database** - creates all necessary tables (handled by `start_server.py`)
3. **Creates `.files/` directory** - for Chainlit session storage (created in Dockerfile)
4. **Mounts volumes** - so your data persists between container restarts

You'll see this in the logs:
```
Database not found. Initializing...
✓ Database initialized at: /app/data/rag_database.db
```

All subsequent runs will skip initialization and use the existing database.

### 3. Access the application

- **Chat Interface**: http://localhost:8000
- **Upload Documents**: http://localhost:8001/upload
- **API Health Check**: http://localhost:8001

## Usage

### Upload Documents

1. Go to http://localhost:8001/upload
2. Upload a PDF, EPUB, or TXT file
3. Fill in the source name and description
4. Click "Upload & Process Document"

### Chat with Your Documents

1. Go to http://localhost:8000
2. Start asking questions!
3. The AI will search your uploaded documents and provide answers with sources

## Docker Commands

### Start in background (detached mode)
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### View logs for a specific service
```bash
docker-compose logs -f chat-interface
docker-compose logs -f mcp-server
```

### Stop the services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up --build
```

### Remove everything (including volumes/data)
```bash
docker-compose down -v
```

## Data Persistence

The following directories are persisted using Docker volumes:
- `./data/` - Database storage (documents and chunks)
- `./chainlit_files/` - Chainlit configuration and session data

Even if you stop or remove containers, your data will be preserved.

## Development Mode

The docker-compose.yml includes volume mounts for the `src/` directory, so you can edit code and see changes immediately (with auto-reload).

To disable this (for production), remove these lines from `docker-compose.yml`:
```yaml
- ./src:/app/src  # Remove this line
```

## Troubleshooting

### Port already in use
If ports 8000 or 8001 are already in use, you can change them in `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"  # Change 9000 to any available port
```

### Database issues
If you encounter database issues, you can reset it:
```bash
rm -rf data/rag_database.db
docker-compose restart
```

### View container status
```bash
docker-compose ps
```

### Enter a running container (for debugging)
```bash
docker-compose exec chat-interface bash
docker-compose exec mcp-server bash
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | None |
| `MCP_SERVER_URL` | URL of the MCP server | `http://mcp-server:8001` |

## Architecture

The Docker setup consists of two services:

1. **mcp-server** (port 8001)
   - FastAPI server
   - Handles document processing
   - Provides search API
   - Database operations

2. **chat-interface** (port 8000)
   - Chainlit web UI
   - User-facing chat interface
   - Communicates with mcp-server

Both services share the same Docker image but run different commands.

## Production Deployment

For production use:

1. Remove the development volume mounts from `docker-compose.yml`
2. Remove the `--reload` flag from `start_server.py`
3. Consider using a reverse proxy (nginx/traefik) for HTTPS
4. Use Docker secrets or a proper secret management system for the API key
5. Set up proper logging and monitoring

## Need Help?

See the main [README.md](README.md) for more information about the application itself.

