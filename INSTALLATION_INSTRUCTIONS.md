# PDF Upload Feature - Installation Instructions

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key (already in `config.py`)
- Terminal access

## 🚀 Quick Install

### Option 1: Automated Setup (Recommended)

```bash
./setup_pdf_feature.sh
```

This will:
- Activate/create virtual environment
- Install all dependencies
- Show next steps

### Option 2: Manual Setup

```bash
# Activate virtual environment (if you have one)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ✅ Verify Installation

Check that new packages are installed:

```bash
python -c "import PyPDF2; print('PyPDF2:', PyPDF2.__version__)"
```

Should show: `PyPDF2: 3.0.1`

## 🎮 Running the System

You need **3 terminal windows/tabs**:

### Terminal 1: MCP Server (Backend)
```bash
cd /Users/alessandrovanzo/nlp_chat
python start_mcp_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2: Main Chat Application
```bash
cd /Users/alessandrovanzo/nlp_chat
chainlit run app.py
```

**Expected output:**
```
2024-XX-XX - Loaded .env file
2024-XX-XX - Your app is available at http://localhost:8000
```

### Terminal 3: PDF Upload Application
```bash
cd /Users/alessandrovanzo/nlp_chat
./start_pdf_upload.sh
```

**Expected output:**
```
🚀 Starting PDF Upload Application...
📌 The application will be available at: http://localhost:8002
2024-XX-XX - Your app is available at http://localhost:8002
```

## 🌐 Access Points

Once all services are running:

| Service | URL | Purpose |
|---------|-----|---------|
| Main Chat | http://localhost:8000 | Ask questions, search knowledge base |
| PDF Upload | http://localhost:8002 | Upload PDFs to knowledge base |
| MCP Server | http://localhost:8001 | Backend API (not for direct use) |

## 🧪 Test Your Installation

### Test 1: Basic Test
1. Open http://localhost:8002
2. You should see: "📄 PDF Upload to Knowledge Base"
3. Success! ✅

### Test 2: Upload a PDF
1. Click the 📎 attachment button
2. Select any PDF file
3. Follow the prompts
4. Should see "✅ PDF Successfully Processed!"

### Test 3: Search the PDF
1. Open http://localhost:8000
2. Ask: "What documents do you have?"
3. Should mention your uploaded PDF
4. Success! ✅

### Test 4: Run Test Script
```bash
python test_pdf_processor.py ~/path/to/sample.pdf
```

Should show:
```
TEST 1: PDF Text Extraction
✅ Successfully extracted N pages

TEST 2: Chunking
✅ Created N chunks

TEST 3: OpenAI Embedding Creation
✅ Successfully created embedding

TEST 4: Full Processing Pipeline
✅ SUCCESS!
```

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'PyPDF2'"

**Solution:**
```bash
pip install PyPDF2==3.0.1
```

### Problem: "Cannot connect to MCP server"

**Solution:**
- Check Terminal 1 is running `start_mcp_server.py`
- Verify you see "Uvicorn running on http://0.0.0.0:8001"
- Check port 8001 is not blocked by firewall

### Problem: "OpenAI API error"

**Solution:**
- Check `config.py` has valid API key
- Verify API key at: https://platform.openai.com/api-keys
- Check you have credits: https://platform.openai.com/usage

### Problem: "PDF has no text"

**Solution:**
- PDF might be scanned images
- Use a PDF with actual text (not images)
- OCR support coming in future version

### Problem: Port already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000  # or :8001, :8002

# Kill the process
kill -9 <PID>

# Or use different port
chainlit run app.py --port 8010
```

### Problem: Permission denied on scripts

**Solution:**
```bash
chmod +x start_pdf_upload.sh
chmod +x setup_pdf_feature.sh
```

## 📦 Package Dependencies

New packages added:

| Package | Version | Purpose |
|---------|---------|---------|
| PyPDF2 | 3.0.1 | PDF text extraction |
| python-multipart | 0.0.6 | File upload support |

Existing packages (already installed):

| Package | Version | Purpose |
|---------|---------|---------|
| chainlit | 1.0.200 | Web interface |
| openai | 1.12.0 | OpenAI API client |
| fastapi | 0.109.0 | Backend server |
| numpy | 1.26.3 | Vector operations |

## 🔍 Verify Services

### Check MCP Server
```bash
curl http://localhost:8001/
```

Should return:
```json
{"status":"ok","service":"RAG MCP Server"}
```

### Check Main Chat
Visit: http://localhost:8000
Should see: "👋 Hello! I'm your AI assistant..."

### Check PDF Upload
Visit: http://localhost:8002
Should see: "📄 PDF Upload to Knowledge Base"

## 🎯 Quick Reference Commands

```bash
# Setup
./setup_pdf_feature.sh

# Run MCP Server
python start_mcp_server.py

# Run Main Chat
chainlit run app.py

# Run PDF Upload
./start_pdf_upload.sh

# Test PDF Processing
python test_pdf_processor.py sample.pdf

# Check Python packages
pip list | grep -E "PyPDF2|chainlit|openai"

# View logs
# (check terminal outputs for any errors)
```

## 📚 Documentation Files

| File | Description |
|------|-------------|
| `INSTALLATION_INSTRUCTIONS.md` | This file |
| `QUICK_START_PDF.md` | Quick start guide |
| `SETUP_PDF_UPLOAD.md` | Detailed technical docs |
| `PDF_FEATURE_SUMMARY.md` | Feature overview |
| `README.md` | Main project README |

## ✨ What You Can Do Now

After successful installation:

1. **Upload PDFs**: Any PDF document
2. **Customize chunking**: 1-10 pages per chunk
3. **Add metadata**: Source names and descriptions
4. **Search content**: Ask questions in main chat
5. **View sources**: See which chunks were retrieved

## 🎓 Next Steps

1. ✅ Install dependencies
2. ✅ Start all 3 services
3. ✅ Upload a test PDF
4. ✅ Search for content
5. 📖 Read QUICK_START_PDF.md for usage tips
6. 🔧 Read SETUP_PDF_UPLOAD.md for technical details

## 💰 Cost Information

**OpenAI text-embedding-3-small pricing**: ~$0.02 per 1M tokens

**Example costs:**
- 10-page PDF: ~$0.0002 (< 1 cent)
- 100-page PDF: ~$0.0013 (< 1 cent)
- 1000-page book: ~$0.013 (1 cent)

Very affordable! 💰

## 🎉 Success!

If you can:
- ✅ Run all 3 services
- ✅ Upload a PDF at http://localhost:8002
- ✅ Search it at http://localhost:8000

**You're all set!** 🚀

For questions or issues, check the troubleshooting section above or review the documentation files.

Happy uploading! 📄✨

