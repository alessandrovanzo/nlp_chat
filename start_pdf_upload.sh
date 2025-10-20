#!/bin/bash

# Start PDF Upload Application
# This runs the PDF upload interface on port 8002

echo "🚀 Starting PDF Upload Application..."
echo "📌 The application will be available at: http://localhost:8002"
echo ""

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the PDF upload app
chainlit run pdf_upload_app.py --port 8002

