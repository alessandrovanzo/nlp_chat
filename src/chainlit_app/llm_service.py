"""
OpenAI LLM service for chat completions
"""
from openai import OpenAI
from src.config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System message for the assistant
SYSTEM_MESSAGE = {
    "role": "system",
    "content": """You are a helpful AI assistant with access to a specialized knowledge base containing curated information about programming, AI, databases, and technical topics.

You have THREE tools available:

1. get_available_sources - Lists all documents in the knowledge base with their IDs, titles, descriptions, and chunk counts
2. search_knowledge_base - Searches across ALL documents in the knowledge base
3. search_specific_documents - Searches within SPECIFIC documents by their IDs

WHEN TO USE EACH TOOL:

- Use search_knowledge_base when:
  * Users ask general questions without specifying sources
  * You want to search across all documents

- Use get_available_sources when:
  * Users want to know what's in the knowledge base
  * You need to identify which documents to search in search_specific_documents

- Use search_specific_documents when:
  * You've identified specific document IDs from get_available_sources
  * Users ask about content from specific sources
  * You want to search within a subset of documents
  * Example workflow: User asks "What does Taleb say about Stiglitz?" → Call get_available_sources → Find Taleb-related document IDs → Call search_specific_documents with those IDs and query "Stiglitz"

After retrieving information, synthesize it into a helpful answer and cite your sources."""
}

# Available tools for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the knowledge base for relevant information using semantic search. Use this when the user asks about topics that might be in the knowledge base (programming, AI, databases, etc.).",
            "parameters": {
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
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_sources",
            "description": "Get a list of all available sources/documents in the knowledge base with their metadata. Returns document IDs, titles, descriptions, chunk counts, and active status. Use this to discover what documents are available before searching specific documents.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_specific_documents",
            "description": "Search within specific documents by their IDs using semantic search. Use this when you want to restrict your search to particular documents. First call get_available_sources to find the document IDs, then use this tool to search within those specific documents.",
            "parameters": {
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
        }
    }
]


def get_completion_with_tools(messages: list, model: str = "gpt-4-turbo"):
    """
    Get a completion from OpenAI with function calling enabled
    
    Args:
        messages: List of conversation messages
        model: OpenAI model to use
        
    Returns:
        The response message from OpenAI
    """
    response = client.chat.completions.create(
        model=model,
        messages=[SYSTEM_MESSAGE] + messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    return response.choices[0].message


def get_streaming_completion(messages: list, model: str = "gpt-4-turbo"):
    """
    Get a streaming completion from OpenAI
    
    Args:
        messages: List of conversation messages
        model: OpenAI model to use
        
    Returns:
        A streaming response object
    """
    stream = client.chat.completions.create(
        model=model,
        messages=[SYSTEM_MESSAGE] + messages,
        stream=True
    )
    return stream

