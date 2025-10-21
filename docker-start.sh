#!/bin/bash
# Simple helper script to start Docker services with validation

set -e

echo "================================"
echo "NLP Chat Docker Startup"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your OpenAI API key:"
    echo ""
    echo "  cp env.template .env"
    echo "  # Then edit .env with your actual API key"
    echo ""
    exit 1
fi

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  Warning: OPENAI_API_KEY might not be set correctly in .env"
    echo "   Make sure it starts with 'sk-'"
    echo ""
fi

echo "✅ .env file found"
echo ""

# Create directories that will be mounted
mkdir -p data chainlit_files

echo "✅ Data directories ready"
echo ""

echo "Starting Docker services..."
echo "This will:"
echo "  - Build the Docker image (first time only)"
echo "  - Initialize the database (if needed)"
echo "  - Create .files directory for Chainlit (if needed)"
echo "  - Start MCP server on http://localhost:8001"
echo "  - Start Chat interface on http://localhost:8000"
echo ""

docker-compose up --build

