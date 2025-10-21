# Docker Quick Start - TL;DR

## Setup (One-time)

```bash
# 1. Create .env file
cp env.template .env
# Edit .env and add your OpenAI API key

# 2. Start everything
./docker-start.sh
```

## Daily Use

```bash
# Start
docker-compose up

# Stop (Ctrl+C, then)
docker-compose down

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## URLs

- Chat: http://localhost:8000
- Upload: http://localhost:8001/upload

## What Gets Created Automatically?

✅ **Database** (`data/rag_database.db`) - Created on first run by `start_server.py`  
✅ **Chainlit files** (`.files/` directory) - Created in Dockerfile  
✅ **All tables** - Initialized automatically via SQLAlchemy

## Data Persistence

Your data is saved in:
- `./data/` - Database with documents and chunks
- `./chainlit_files/` - Chainlit session storage

These directories persist even when containers are stopped or removed.

## Troubleshooting

```bash
# Reset database
rm -rf data/rag_database.db
docker-compose restart

# Rebuild image
docker-compose up --build

# Clean everything
docker-compose down -v
rm -rf data/ chainlit_files/
```

That's it! 🚀

