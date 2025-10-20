#!/bin/bash

# Setup script for PDF upload feature
echo "🚀 Setting up PDF Upload Feature"
echo "================================="
echo ""

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment found"
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found at .venv"
    echo "   Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo ""
echo "To start the PDF upload feature, you need to run 3 services:"
echo ""
echo "Terminal 1: MCP Server"
echo "  python start_mcp_server.py"
echo ""
echo "Terminal 2: Main Chat"
echo "  chainlit run app.py"
echo ""
echo "Terminal 3: PDF Upload"
echo "  ./start_pdf_upload.sh"
echo ""
echo "Then open:"
echo "  - Main Chat: http://localhost:8000"
echo "  - PDF Upload: http://localhost:8002"
echo ""
echo "📖 For more info, see:"
echo "  - QUICK_START_PDF.md"
echo "  - SETUP_PDF_UPLOAD.md"
echo "  - PDF_FEATURE_SUMMARY.md"
echo ""

