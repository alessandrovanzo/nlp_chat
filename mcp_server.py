"""
FastAPI MCP Server with RAG functionality
"""
import json
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
from contextlib import contextmanager
from openai import OpenAI
from config import oai_key
import tempfile
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG MCP Server")

# Database path
DB_PATH = "rag_database.db"

# Initialize OpenAI client
openai_client = OpenAI(api_key=oai_key)

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

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def fake_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate a fake but consistent embedding for text (for backward compatibility)"""
    # Use hash to make it deterministic
    np.random.seed(hash(text) % (2**32))
    embedding = np.random.randn(dim)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()

def create_real_embedding(text: str) -> List[float]:
    """Create embedding using OpenAI's text-embedding-3-small model"""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error creating embedding: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "RAG MCP Server"}

@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Serve the PDF upload page"""
    try:
        with open("upload_form.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Error: upload_form.html not found</h1>",
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
        query_embedding = create_real_embedding(query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
    except Exception as e:
        logger.error(f"Failed to create OpenAI embedding: {str(e)}")
        logger.warning("Falling back to fake embeddings")
        query_embedding = fake_embedding(query)
    
    # Search database (only active documents)
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, embedding, title, description, source_type, 
                       start_page, end_page, chunk_number, total_chunks, unit_name, active
                FROM documents 
                WHERE active = 1
            """)
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("No active documents found in database")
                return ToolCallResponse(
                    content=[{"type": "text", "text": "No active documents found in the knowledge base. Please activate some sources in the upload interface."}],
                    isError=False
                )
            
            logger.info(f"Retrieved {len(rows)} active documents from database")
            
            # Calculate similarities
            results = []
            for row in rows:
                try:
                    doc_id = row[0]
                    content = row[1]
                    embedding = json.loads(row[2])
                    title = row[3]
                    description = row[4]
                    source_type = row[5]
                    start_page = row[6]
                    end_page = row[7]
                    chunk_number = row[8]
                    total_chunks = row[9]
                    unit_name = row[10]
                    active = row[11]
                    
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
                        "active": active
                    }
                    
                    # Check embedding dimensions
                    if len(embedding) != len(query_embedding):
                        logger.error(
                            f"Dimension mismatch for document {doc_id} ('{title}'): "
                            f"query={len(query_embedding)}, doc={len(embedding)}"
                        )
                        continue
                    
                    similarity = cosine_similarity(query_embedding, embedding)
                    results.append({
                        "id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "similarity": similarity
                    })
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {str(e)}")
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
            # Include both human-readable text and structured JSON for parsing
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
async def upload_pdf(
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
        
        # Process the document using pdf_processor (which now handles both types)
        from pdf_processor import process_document
        
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
        logger.error(f"Error in upload_pdf: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": f"Server error: {str(e)}"},
            status_code=500
        )

@app.post("/initialize")
async def initialize_database():
    """Initialize the database with fake data"""
    logger.info("Initializing database with sample data")
    from init_db import initialize_db
    try:
        initialize_db()
        logger.info("Database initialization completed successfully")
        return {"status": "success", "message": "Database initialized with sample data"}
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources")
async def list_sources():
    """Get list of all unique sources with their status"""
    logger.info("Request received: GET /sources - Listing all sources")
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all documents and group by source (title)
            cursor.execute("""
                SELECT 
                    title,
                    description,
                    source_type,
                    COUNT(*) as chunk_count,
                    MIN(id) as first_id,
                    MAX(active) as active
                FROM documents
                GROUP BY title
                ORDER BY MAX(created_at) DESC
            """)
            
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    "title": row[0],
                    "description": row[1],
                    "source_type": row[2] or "unknown",
                    "chunk_count": row[3],
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
    """Toggle active status of a source"""
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
            
            # Update all chunks with this title
            cursor.execute("""
                UPDATE documents
                SET active = ?
                WHERE title = ?
            """, (1 if active else 0, title))
            
            updated_count = cursor.rowcount
            
            if updated_count == 0:
                return JSONResponse(
                    content={"success": False, "error": "Source not found"},
                    status_code=404
                )
            
            conn.commit()
            logger.info(f"Updated {updated_count} chunks for source '{title}'")
            
            return {"success": True, "updated_chunks": updated_count, "active": active}
    except Exception as e:
        logger.error(f"Error toggling source: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/sources/delete")
async def delete_source(request: dict):
    """Delete a source and all its chunks"""
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
            
            # Count chunks before deletion
            cursor.execute("""
                SELECT COUNT(*) FROM documents
                WHERE title = ?
            """, (title,))
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                return JSONResponse(
                    content={"success": False, "error": "Source not found"},
                    status_code=404
                )
            
            # Delete all chunks with this title
            cursor.execute("""
                DELETE FROM documents
                WHERE title = ?
            """, (title,))
            
            conn.commit()
            logger.info(f"Deleted {count} chunks for source '{title}'")
            
            return {"success": True, "deleted_chunks": count}
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

