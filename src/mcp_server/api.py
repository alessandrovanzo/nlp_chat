"""
FastAPI MCP Server with RAG functionality
Routes layer - handles HTTP requests/responses only
"""
import json
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import tempfile
import os
import logging
import traceback

from src.config import OPENAI_API_KEY, DB_PATH
from src.document.processor import process_document
from src.server import services
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG MCP Server")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


@app.on_event("startup")
async def startup_event():
    """Log mcp_server startup"""
    logger.info("=" * 60)
    logger.info("RAG MCP Server starting up")
    logger.info(f"Database path: {DB_PATH}")
    logger.info(f"OpenAI client initialized")
    logger.info("=" * 60)


# Pydantic models for MCP protocol
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "RAG MCP Server"}


@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Serve the document upload page"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "document_upload_form", "upload.html")
        with open(html_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: upload.html not found</h1>",
            status_code=500
        )


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    logger.info("Request received: GET /mcp/tools - Listing available tools")
    tools = [
        Tool(
            name="search_knowledge_base",
            description="Search the knowledge base for relevant information using semantic search. Returns the most relevant documents based on the query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        )
    ]
    logger.info(f"Returning {len(tools)} available tool(s)")
    return {"tools": [tool.dict() for tool in tools]}


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    """Execute a tool call"""
    logger.info("=" * 80)
    logger.info("MCP TOOL CALL RECEIVED")
    logger.info(f"Tool Name: {request.name}")
    logger.info(f"Arguments: {json.dumps(request.arguments, indent=2)}")
    logger.info("=" * 80)
    
    try:
        if request.name == "search_knowledge_base":
            return await handle_search_knowledge_base(
                query=request.arguments.get("query", ""),
                top_k=request.arguments.get("top_k", 3)
            )
        else:
            error_msg = f"Tool '{request.name}' not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
    except Exception as e:
        logger.error(f"Error in call_tool: {str(e)}")
        logger.error(traceback.format_exc())
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True
        )


async def handle_search_knowledge_base(query: str, top_k: int = 3) -> ToolCallResponse:
    """Handle search knowledge base tool call - delegates to service layer"""
    success, message, results = services.search_knowledge_base(query, top_k)
    
    if not success:
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error: {message}"}],
            isError=True
        )
    
    # No results but successful (e.g., no active documents)
    if not results:
        return ToolCallResponse(
            content=[{"type": "text", "text": message}],
            isError=False
        )
    
    # Format response with structured data
    response_text = f"{message}:\n\n"
    for i, result in enumerate(results, 1):
        response_text += f"{i}. [{result['metadata'].get('title', 'Untitled')}]\n"
        response_text += f"   Relevance: {result['similarity']:.2%}\n"
        response_text += f"   {result['content']}\n\n"
    
    # Add structured data as JSON for the client to parse
    response_text += "\n---SOURCES_JSON---\n"
    response_text += json.dumps(results, indent=2)
    
    return ToolCallResponse(
        content=[{"type": "text", "text": response_text}],
        isError=False
    )


@app.post("/upload-pdf")
async def upload_document(
    pdf_file: UploadFile = File(...),
    source_name: str = Form(...),
    description: str = Form(...),
    pages_per_chunk: int = Form(3),
    prepend_metadata: bool = Form(True)
):
    """Handle document upload and processing (PDF, EPUB, or TXT)"""
    logger.info(f"Received document upload: '{pdf_file.filename}' for '{source_name}' (pages_per_chunk={pages_per_chunk}, prepend_metadata={prepend_metadata})")
    
    try:
        # Validate file extension
        filename = pdf_file.filename.lower()
        if filename.endswith('.pdf'):
            suffix = '.pdf'
            file_type = 'PDF'
        elif filename.endswith('.epub'):
            suffix = '.epub'
            file_type = 'EPUB'
        elif filename.endswith('.txt'):
            suffix = '.txt'
            file_type = 'TXT'
        else:
            logger.warning(f"Unsupported file type: {filename}")
            return JSONResponse(
                content={"success": False, "error": "Unsupported file format. Please upload a PDF, EPUB, or TXT file."},
                status_code=400
            )
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await pdf_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Saved temporary {file_type} file: {tmp_file_path}")
        
        # Process the document
        result = process_document(
            file_path=tmp_file_path,
            source_name=source_name,
            description=description,
            pages_per_chunk=pages_per_chunk,
            prepend_metadata=prepend_metadata
        )
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        logger.info(f"Cleaned up temporary file: {tmp_file_path}")
        
        if result.get("success"):
            logger.info(f"Successfully processed {file_type}: {result.get('total_chunks')} chunks created")
        else:
            error_msg = result.get('error', '')
            logger.error(f"{file_type} processing failed: {error_msg}")
            
            # Check if it's a duplicate title error
            if "already exists" in error_msg:
                return JSONResponse(
                    content=result,
                    status_code=409  # Conflict status code
                )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error in upload_document: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": f"Server error: {str(e)}"},
            status_code=500
        )


@app.get("/sources")
async def list_sources():
    """Get list of all unique sources with their status"""
    logger.info("Request received: GET /sources - Listing all sources")
    
    success, message, sources = services.list_all_sources()
    
    if not success:
        return JSONResponse(
            content={"success": False, "error": message},
            status_code=500
        )
    
    return {"success": True, "sources": sources}


@app.post("/sources/toggle")
async def toggle_source(request: dict):
    """Toggle active status of a source (document)"""
    title = request.get("title")
    active = request.get("active", True)
    
    logger.info(f"Request received: POST /sources/toggle - title='{title}', active={active}")
    
    success, message, data = services.toggle_source_active(title, active)
    
    if not success:
        if "not found" in message.lower():
            status_code = 404
        elif "required" in message.lower():
            status_code = 400
        else:
            status_code = 500
        
        return JSONResponse(
            content={"success": False, "error": message},
            status_code=status_code
        )
    
    return {"success": True, **data}


@app.post("/sources/delete")
async def delete_source_route(request: dict):
    """Delete a source document and all its chunks (CASCADE)"""
    title = request.get("title")
    
    logger.info(f"Request received: POST /sources/delete - title='{title}'")
    
    success, message, data = services.delete_source(title)
    
    if not success:
        if "not found" in message.lower():
            status_code = 404
        elif "required" in message.lower():
            status_code = 400
        else:
            status_code = 500
        
        return JSONResponse(
            content={"success": False, "error": message},
            status_code=status_code
        )
    
    return {"success": True, **data}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

