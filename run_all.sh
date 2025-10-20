#!/bin/bash
# Script to run both MCP server and Chainlit app

echo "================================================"
echo "Starting NLP Chatbot with RAG"
echo "================================================"
echo ""

# Check if dependencies are installed
if ! python3 -c "import chainlit" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip3 install -r requirements.txt
    echo ""
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $MCP_PID $CHAINLIT_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start MCP server in background
echo "Starting MCP Server on http://localhost:8001..."
python3 start_mcp_server.py &
MCP_PID=$!

# Wait for server to be ready
sleep 3

# Start Chainlit app
echo "Starting Chainlit App on http://localhost:8000..."
echo ""
echo "================================================"
echo "✓ Both services are running!"
echo "  - MCP Server: http://localhost:8001"
echo "  - Chatbot UI: http://localhost:8000"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

chainlit run app.py &
CHAINLIT_PID=$!

# Wait for both processes
wait

