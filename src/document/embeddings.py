"""
Embedding generation using OpenAI
"""
from typing import List
from openai import OpenAI
from src.config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def create_embedding(text: str) -> List[float]:
    """
    Create embedding using OpenAI's text-embedding-3-small model
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list of floats
        
    Raises:
        Exception: If embedding creation fails or token limit is exceeded
    """
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        # Check if it's a token limit error
        error_str = str(e)
        if "maximum context length" in error_str or "8192 tokens" in error_str:
            # This will be caught by the caller to split the chunk
            raise Exception(f"TOKEN_LIMIT_EXCEEDED: {error_str}")
        raise Exception(f"Error creating embedding: {str(e)}")

