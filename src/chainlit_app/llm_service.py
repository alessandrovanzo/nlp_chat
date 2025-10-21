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

IMPORTANT: Always use the search_knowledge_base function when users ask about technical topics, even if you think you know the answer. The knowledge base contains specific, curated information that should be used.

Topics that require searching include:
- Programming (Python, FastAPI, async, REST APIs, etc.)
- AI/ML (RAG, embeddings, NLP, machine learning, etc.)
- Databases (SQLite, vector databases, etc.)

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

