"""
Chainlit chat interface with RAG support
"""
import chainlit as cl
from src.config import MCP_SERVER_URL
from src.chainlit_app.llm_service import get_completion_with_tools, get_streaming_completion
from src.chainlit_app.ui_helpers import parse_sources_from_response, create_source_elements, format_sources_message
import httpx
import json


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
    
    # Get completion with function calling enabled
    response_message = get_completion_with_tools(messages)
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
            
            # Parse sources from response and create display elements
            text_part, sources = parse_sources_from_response(function_response)
            
            if sources:
                # Create source elements for sidebar
                sources_elements.extend(create_source_elements(sources))
                
                # Display sources with previews
                sources_text = format_sources_message(sources)
                await cl.Message(
                    content=sources_text,
                    elements=sources_elements
                ).send()
            
            # Add tool response to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response
            })
        
        # Get streaming response with tool results
        msg = cl.Message(content="")
        stream = get_streaming_completion(messages)
        
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
        stream = get_streaming_completion(messages)
        
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

