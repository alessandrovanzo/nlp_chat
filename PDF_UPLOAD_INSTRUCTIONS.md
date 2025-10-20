# PDF Upload - Simple Instructions

## 🚀 Quick Start

### 1. Start the MCP Server
```bash
python start_mcp_server.py
```

### 2. Open the Upload Page
Go to: **http://localhost:8001/upload**

### 3. Upload Your PDF
1. Click the file upload area or drag & drop your PDF
2. Fill in:
   - **Source Name**: Title for your document
   - **Description**: Brief description of the content
   - **Pages per Chunk**: Use the slider (1-10, default is 3)
3. Click "Upload & Process PDF"
4. Wait for processing (you'll see a progress bar)
5. Done! Your PDF is now in the knowledge base

### 4. Search Your PDF (Optional)
Start the main chat app to search:
```bash
chainlit run app.py
```
Then go to http://localhost:8000 and ask questions about your PDF!

## 📋 What You Need

- MCP server running (`python start_mcp_server.py`)
- A PDF file to upload
- OpenAI API key (already in config.py)

## 🎯 That's It!

The upload is now a normal web form - no chat interface needed!

Just:
1. Run: `python start_mcp_server.py`
2. Visit: http://localhost:8001/upload
3. Upload your PDF
4. Done! ✅

## 💡 Tips

- **Smaller chunks (1-3)**: Better for precise searches
- **Larger chunks (7-10)**: Better for context
- **Default (3 pages)**: Good for most documents

## 🔍 Example

Let's say you upload a document called "kohavi.pdf":

1. **Source Name**: "Kohavi Research Paper"
2. **Description**: "Research on controlled experiments and A/B testing"
3. **Pages per Chunk**: 3
4. Click upload and wait
5. Success! Now searchable in the chat app

