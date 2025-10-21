"""
MCP Tools - Definitions and handlers for Model Context Protocol tools
"""
import json
from typing import List, Dict, Any
from pydantic import BaseModel

from src.mcp_server import services


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


# Tool definitions
TOOLS = [
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
    ),
    Tool(
        name="get_available_sources",
        description="Get a list of all available sources/documents in the knowledge base with their metadata. Returns document IDs, titles, descriptions, chunk counts, and active status. Use this to discover what documents are available before searching specific documents.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    Tool(
        name="search_specific_documents",
        description="Search within specific documents by their IDs using semantic search. Use this when you want to restrict your search to particular documents. First call get_available_sources to find the document IDs, then use this tool to search within those specific documents.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information"
                },
                "document_ids": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    },
                    "description": "List of document IDs to search within"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 3)",
                    "default": 3
                }
            },
            "required": ["query", "document_ids"]
        }
    )
]


# Tool handlers
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


async def handle_get_available_sources() -> ToolCallResponse:
    """Handle get available sources tool call - delegates to service layer"""
    success, message, sources = services.get_available_sources()
    
    if not success:
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error: {message}"}],
            isError=True
        )
    
    # No sources but successful
    if not sources:
        return ToolCallResponse(
            content=[{"type": "text", "text": "No sources found in the knowledge base."}],
            isError=False
        )
    
    # Format response with structured data
    response_text = f"{message}:\n\n"
    for source in sources:
        response_text += f"Document ID: {source['document_id']}\n"
        response_text += f"Title: {source['title']}\n"
        response_text += f"Description: {source['description']}\n"
        response_text += f"Type: {source['source_type']}\n"
        response_text += f"Total Chunks: {source['total_chunks']}\n"
        response_text += f"Active: {'Yes' if source['active'] else 'No'}\n"
        response_text += "-" * 50 + "\n\n"
    
    # Add structured data as JSON for easy parsing
    response_text += "\n---SOURCES_JSON---\n"
    response_text += json.dumps(sources, indent=2)
    
    return ToolCallResponse(
        content=[{"type": "text", "text": response_text}],
        isError=False
    )


async def handle_search_specific_documents(
    query: str,
    document_ids: List[int],
    top_k: int = 3
) -> ToolCallResponse:
    """Handle search specific documents tool call - delegates to service layer"""
    success, message, results = services.search_specific_documents(query, document_ids, top_k)
    
    if not success:
        return ToolCallResponse(
            content=[{"type": "text", "text": f"Error: {message}"}],
            isError=True
        )
    
    # No results but successful (e.g., no active chunks in specified documents)
    if not results:
        return ToolCallResponse(
            content=[{"type": "text", "text": message}],
            isError=False
        )
    
    # Format response with structured data
    response_text = f"{message}:\n\n"
    for i, result in enumerate(results, 1):
        response_text += f"{i}. [{result['metadata'].get('title', 'Untitled')}]\n"
        response_text += f"   Document ID: {result['metadata'].get('document_id')}\n"
        response_text += f"   Relevance: {result['similarity']:.2%}\n"
        response_text += f"   {result['content']}\n\n"
    
    # Add structured data as JSON for the client to parse
    response_text += "\n---SOURCES_JSON---\n"
    response_text += json.dumps(results, indent=2)
    
    return ToolCallResponse(
        content=[{"type": "text", "text": response_text}],
        isError=False
    )

