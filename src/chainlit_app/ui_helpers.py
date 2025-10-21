"""
UI helper functions for formatting and displaying sources
"""
import json
import chainlit as cl


def parse_sources_from_response(response: str) -> tuple[str, list]:
    """
    Parse sources JSON from the tool response
    
    Args:
        response: The tool response string
        
    Returns:
        Tuple of (text_part, sources_list)
    """
    if "---SOURCES_JSON---" not in response:
        return response, []
    
    text_part, json_part = response.split("---SOURCES_JSON---", 1)
    try:
        sources = json.loads(json_part.strip())
        return text_part, sources
    except json.JSONDecodeError:
        return response, []


def create_source_elements(sources: list) -> list:
    """
    Create Chainlit Text elements for each source
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        List of Chainlit Text elements
    """
    elements = []
    
    for i, source in enumerate(sources, 1):
        title = source.get('metadata', {}).get('title', 'Untitled')
        similarity = source.get('similarity', 0)
        content = source.get('content', '')
        chunk_number = source.get('metadata', {}).get('chunk_number')
        
        # Format content with metadata for better display
        formatted_content = f"Title: {title}\n"
        formatted_content += f"Relevance: {similarity:.2%}\n"
        if chunk_number is not None:
            formatted_content += f"Chunk: {chunk_number}\n"
        formatted_content += f"Document ID: {source.get('id', 'N/A')}\n\n"
        formatted_content += "="*50 + "\n\n"
        formatted_content += content
        
        # Create a text element with the full content
        source_element = cl.Text(
            name=f"Source {i}: {title}",
            content=formatted_content,
            display="side"
        )
        elements.append(source_element)
    
    return elements


def format_sources_message(sources: list) -> str:
    """
    Format sources into a readable message with previews
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Formatted markdown string
    """
    if not sources:
        return ""
    
    sources_text = "📚 **Sources Retrieved:**\n\n"
    
    for i, source in enumerate(sources, 1):
        title = source.get('metadata', {}).get('title', 'Untitled')
        similarity = source.get('similarity', 0)
        content = source.get('content', '')
        chunk_number = source.get('metadata', {}).get('chunk_number')
        
        # Create preview
        preview = content[:100] + "..." if len(content) > 100 else content
        
        # Build source header with optional chunk info
        source_header = f"**Source {i}**: {title}"
        if chunk_number is not None:
            source_header += f" (Chunk {chunk_number})"
        source_header += f" — Relevance: {similarity:.0%}\n"
        
        sources_text += source_header
        sources_text += f"*Preview*: {preview}\n"
        sources_text += f"👉 *Click 'Source {i}: {title}' in the sidebar to view full text*\n\n"
    
    return sources_text

