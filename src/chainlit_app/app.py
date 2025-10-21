"""
Chainlit chainlit_app interface with RAG support
"""
import chainlit as cl
from openai import OpenAI
from src.config import OPENAI_API_KEY, MCP_SERVER_URL
import httpx
import json

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


@cl.on_chat_start
async def start():
    """Welcome message when chainlit_app starts"""
    cl.user_session.set("messages", [])
    await cl.Message(
        content="👋 Hello! I'm your AI assistant with access to a knowledge base. I can search for information to help answer your questions!"
    ).send()


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool on the FastAPI backend"""
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(
                f"{MCP_SERVER_URL}/mcp/tools/call",
                json={"name": tool_name, "arguments": arguments},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("isError", False):
                return f"Error calling tool: {result['content'][0]['text']}"
            
            return result["content"][0]["text"]
        except Exception as e:
            return f"Error communicating with MCP server: {str(e)}"


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with RAG support"""
    
    # Get conversation history
    messages = cl.user_session.get("messages", [])
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})
    
    # Define available tools for function calling
    tools = [
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
    
    # System message
    system_message = {
        "role": "system",
        "content": """You are a helpful AI assistant with access to a specialized knowledge base containing curated information about programming, AI, databases, and technical topics.

IMPORTANT: Always use the search_knowledge_base function when users ask about technical topics, even if you think you know the answer. The knowledge base contains specific, curated information that should be used.

Topics that require searching include:
- Programming (Python, FastAPI, async, REST APIs, etc.)
- AI/ML (RAG, embeddings, NLP, machine learning, etc.)
- Databases (SQLite, vector databases, etc.)

After retrieving information, synthesize it into a helpful answer and cite your sources."""
    }
    
    # First API call with function calling
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[system_message] + messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Handle tool calls if any
    if tool_calls:
        # Add assistant's tool call to messages
        messages.append({
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in tool_calls
            ]
        })
        
        # Execute each tool call
        sources_elements = []  # Store source elements for display
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Show user that we're searching
            await cl.Message(
                content=f"🔍 Searching knowledge base for: {function_args.get('query', 'information')}..."
            ).send()
            
            # Call the MCP tool
            function_response = await call_mcp_tool(function_name, function_args)
            
            # Parse sources from response and create expandable elements
            if "---SOURCES_JSON---" in function_response:
                text_part, json_part = function_response.split("---SOURCES_JSON---", 1)
                try:
                    sources = json.loads(json_part.strip())
                    
                    # Create expandable text elements for each source
                    for i, source in enumerate(sources, 1):
                        title = source.get('metadata', {}).get('title', 'Untitled')
                        similarity = source.get('similarity', 0)
                        content = source.get('content', '')
                        
                        # Format content with metadata for better display
                        formatted_content = f"Title: {title}\n"
                        formatted_content += f"Relevance: {similarity:.2%}\n"
                        formatted_content += f"Document ID: {source.get('id', 'N/A')}\n\n"
                        formatted_content += "="*50 + "\n\n"
                        formatted_content += content
                        
                        # Create a text element with the full content (no language for text wrapping)
                        source_element = cl.Text(
                            name=f"Source {i}: {title}",
                            content=formatted_content,
                            display="side"
                        )
                        sources_elements.append(source_element)
                    
                    # Display sources with "view more" links
                    if sources_elements:
                        sources_text = "📚 **Sources Retrieved:**\n\n"
                        for i, source in enumerate(sources, 1):
                            title = source.get('metadata', {}).get('title', 'Untitled')
                            similarity = source.get('similarity', 0)
                            # Show source name and relevance, with reference to expandable element
                            preview = source.get('content', '')[:100] + "..." if len(source.get('content', '')) > 100 else source.get('content', '')
                            sources_text += f"**Source {i}**: {title} (Relevance: {similarity:.0%})\n"
                            sources_text += f"*Preview*: {preview}\n"
                            sources_text += f"👉 *Click 'Source {i}: {title}' in the sidebar to view full text*\n\n"
                        
                        await cl.Message(
                            content=sources_text,
                            elements=sources_elements
                        ).send()
                
                except json.JSONDecodeError:
                    pass  # If parsing fails, continue without source display
            
            # Add tool response to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response
            })
        
        # Second API call with tool results - with streaming
        msg = cl.Message(content="")
        
        stream = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[system_message] + messages,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                await msg.stream_token(content)
        
        await msg.send()
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": full_response})
    else:
        # No tool calls, just stream the response
        msg = cl.Message(content="")
        
        stream = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[system_message] + messages,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                await msg.stream_token(content)
        
        await msg.send()
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": full_response})
    
    # Update session with new messages
    cl.user_session.set("messages", messages)

