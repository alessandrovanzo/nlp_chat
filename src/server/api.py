"""
FastAPI MCP Server with RAG functionality
"""
import json
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import tempfile
import os
import logging
import traceback

from src.config import OPENAI_API_KEY, DB_PATH
from src.database.models import get_db, process_document
from src.document.embeddings import create_embedding
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
    """Log server startup"""
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


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "RAG MCP Server"}


@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Serve the document upload page"""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "static", "upload.html")
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
            return await search_knowledge_base(
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


async def search_knowledge_base(query: str, top_k: int = 3) -> ToolCallResponse:
    """Search the knowledge base using vector similarity"""
    if not query:
        logger.warning("Empty query received")
        return ToolCallResponse(
            content=[{"type": "text", "text": "Error: Query cannot be empty"}],
            isError=True
        )
    
    logger.info(f"Searching knowledge base for: '{query}' (top_k={top_k})")
    
    # Generate embedding for query using OpenAI
    try:
        query_embedding = create_embedding(query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
    except Exception as e:
        logger.error(f"Failed to create OpenAI embedding: {str(e)}")
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error creating embedding: {str(e)}"}],
            isError=True
        )
    
    # Search database (only active documents)
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.content, c.embedding, c.start_page, c.end_page, 
                       c.chunk_number, c.unit_name,
                       d.id, d.title, d.description, d.source_type, d.total_chunks
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE d.active = 1
            """)
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("No active documents found in database")
                return ToolCallResponse(
                    content=[{"type": "text", "text": "No active documents found in the knowledge base. Please activate some sources in the upload interface."}],
                    isError=False
                )
            
            logger.info(f"Retrieved {len(rows)} chunks from active documents")
            
            # Calculate similarities
            results = []
            for row in rows:
                try:
                    chunk_id = row[0]
                    content = row[1]
                    embedding = json.loads(row[2])
                    start_page = row[3]
                    end_page = row[4]
                    chunk_number = row[5]
                    unit_name = row[6]
                    document_id = row[7]
                    title = row[8]
                    description = row[9]
                    source_type = row[10]
                    total_chunks = row[11]
                    
                    # Build metadata dict for compatibility
                    metadata = {
                        "title": title,
                        "description": description,
                        "source_type": source_type,
                        "start_page": start_page,
                        "end_page": end_page,
                        "chunk_number": chunk_number,
                        "total_chunks": total_chunks,
                        "unit_name": unit_name,
                        "document_id": document_id
                    }
                    
                    # Check embedding dimensions
                    if len(embedding) != len(query_embedding):
                        logger.error(
                            f"Dimension mismatch for chunk {chunk_id} ('{title}'): "
                            f"query={len(query_embedding)}, chunk={len(embedding)}"
                        )
                        continue
                    
                    similarity = cosine_similarity(query_embedding, embedding)
                    results.append({
                        "id": chunk_id,
                        "content": content,
                        "metadata": metadata,
                        "similarity": similarity
                    })
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_id}: {str(e)}")
                    continue
            
            if not results:
                error_msg = "All documents had incompatible embeddings. Database may contain mixed embedding dimensions."
                logger.error(error_msg)
                return ToolCallResponse(
                    content=[{"type": "text", "text": f"Error: {error_msg}"}],
                    isError=True
                )
            
            # Sort by similarity and get top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = results[:top_k]
            
            logger.info(f"Returning top {len(top_results)} results with similarities: {[r['similarity'] for r in top_results]}")
            
            # Format response with structured data
            response_text = f"Found {len(top_results)} relevant document(s):\n\n"
            for i, result in enumerate(top_results, 1):
                response_text += f"{i}. [{result['metadata'].get('title', 'Untitled')}]\n"
                response_text += f"   Relevance: {result['similarity']:.2%}\n"
                response_text += f"   {result['content']}\n\n"
            
            # Add structured data as JSON for the client to parse
            response_text += "\n---SOURCES_JSON---\n"
            response_text += json.dumps(top_results, indent=2)
            
            return ToolCallResponse(
                content=[{"type": "text", "text": response_text}],
                isError=False
            )
    except Exception as e:
        logger.error(f"Error in search_knowledge_base: {str(e)}")
        logger.error(traceback.format_exc())
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error during search: {str(e)}"}],
            isError=True
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
            logger.error(f"{file_type} processing failed: {result.get('error')}")
        
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
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all documents with their chunk counts
            cursor.execute("""
                SELECT 
                    d.id,
                    d.title,
                    d.description,
                    d.source_type,
                    d.total_chunks,
                    d.active,
                    d.created_at
                FROM documents d
                ORDER BY d.created_at DESC
            """)
            
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "source_type": row[3] or "unknown",
                    "chunk_count": row[4],
                    "active": bool(row[5])
                })
            
            logger.info(f"Returning {len(sources)} sources")
            return {"success": True, "sources": sources}
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/sources/toggle")
async def toggle_source(request: dict):
    """Toggle active status of a source (document)"""
    title = request.get("title")
    active = request.get("active", True)
    
    if not title:
        return JSONResponse(
            content={"success": False, "error": "Title is required"},
            status_code=400
        )
    
    logger.info(f"Toggling source '{title}' to active={active}")
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get chunk count first
            cursor.execute("SELECT total_chunks FROM documents WHERE title = ?", (title,))
            result = cursor.fetchone()
            
            if not result:
                return JSONResponse(
                    content={"success": False, "error": "Source not found"},
                    status_code=404
                )
            
            chunk_count = result[0]
            
            # Update document active status
            cursor.execute("""
                UPDATE documents
                SET active = ?
                WHERE title = ?
            """, (1 if active else 0, title))
            
            conn.commit()
            logger.info(f"Updated source '{title}' (affects {chunk_count} chunks)")
            
            return {"success": True, "updated_chunks": chunk_count, "active": active}
    except Exception as e:
        logger.error(f"Error toggling source: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/sources/delete")
async def delete_source(request: dict):
    """Delete a source document and all its chunks (CASCADE)"""
    title = request.get("title")
    
    if not title:
        return JSONResponse(
            content={"success": False, "error": "Title is required"},
            status_code=400
        )
    
    logger.info(f"Deleting source '{title}'")
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get chunk count before deletion
            cursor.execute("""
                SELECT id, total_chunks FROM documents
                WHERE title = ?
            """, (title,))
            
            result = cursor.fetchone()
            
            if not result:
                return JSONResponse(
                    content={"success": False, "error": "Source not found"},
                    status_code=404
                )
            
            doc_id, chunk_count = result
            
            # Delete document (CASCADE will automatically delete all associated chunks)
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            conn.commit()
            logger.info(f"Deleted document '{title}' and {chunk_count} chunks (CASCADE)")
            
            return {"success": True, "deleted_chunks": chunk_count}
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

