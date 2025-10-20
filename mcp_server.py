"""
FastAPI MCP Server with RAG functionality
"""
import json
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="RAG MCP Server")

# Database path
DB_PATH = "rag_database.db"

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
    """Generate a fake but consistent embedding for text"""
    # Use hash to make it deterministic
    np.random.seed(hash(text) % (2**32))
    embedding = np.random.randn(dim)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.tolist()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "RAG MCP Server"}

@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
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
    return {"tools": [tool.dict() for tool in tools]}

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    """Execute a tool call"""
    try:
        if request.name == "search_knowledge_base":
            return await search_knowledge_base(
                query=request.arguments.get("query", ""),
                top_k=request.arguments.get("top_k", 3)
            )
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{request.name}' not found")
    except Exception as e:
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True
        )

async def search_knowledge_base(query: str, top_k: int = 3) -> ToolCallResponse:
    """Search the knowledge base using vector similarity"""
    if not query:
        return ToolCallResponse(
            content=[{"type": "text", "text": "Error: Query cannot be empty"}],
            isError=True
        )
    
    # Generate embedding for query
    query_embedding = fake_embedding(query)
    
    # Search database
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, embedding, metadata FROM documents")
        rows = cursor.fetchall()
        
        if not rows:
            return ToolCallResponse(
                content=[{"type": "text", "text": "No documents found in the knowledge base."}],
                isError=False
            )
        
        # Calculate similarities
        results = []
        for row in rows:
            doc_id = row[0]
            content = row[1]
            embedding = json.loads(row[2])
            metadata = json.loads(row[3]) if row[3] else {}
            
            similarity = cosine_similarity(query_embedding, embedding)
            results.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
                "similarity": similarity
            })
        
        # Sort by similarity and get top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:top_k]
        
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

@app.post("/initialize")
async def initialize_database():
    """Initialize the database with fake data"""
    from init_db import initialize_db
    try:
        initialize_db()
        return {"status": "success", "message": "Database initialized with sample data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

