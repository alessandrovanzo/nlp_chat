"""
Chainlit PDF Upload Application
Allows users to upload PDFs and add them to the knowledge base
"""
import chainlit as cl
from pdf_processor import process_pdf
import os
import tempfile


@cl.on_chat_start
async def start():
    """Initialize the PDF upload session"""
    # Set default values
    cl.user_session.set("pages_per_chunk", 3)
    cl.user_session.set("source_name", "")
    cl.user_session.set("description", "")
    
    # Welcome message with instructions
    welcome_msg = """# 📄 PDF Upload to Knowledge Base

Welcome! This tool allows you to upload PDF documents to the knowledge base.

## Instructions:
1. **Upload a PDF file** using the attachment button below
2. I'll ask you for:
   - **Source Name**: A title for your document
   - **Description**: A brief description of the content
   - **Pages per Chunk**: How many pages to group together (1-10)
3. The PDF will be processed, embedded, and added to the knowledge base

Ready to upload your first PDF? Click the attachment button (📎) to get started!
"""
    
    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """Handle messages and file uploads"""
    
    # Check if there's a file attachment
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                # Check if it's a PDF
                if not element.name.lower().endswith('.pdf'):
                    await cl.Message(
                        content="❌ Please upload a PDF file only. The file must have a .pdf extension."
                    ).send()
                    return
                
                # Ask for source name
                await cl.Message(
                    content="📝 Great! I received your PDF. Now, please provide the **source name** (a title for this document):"
                ).send()
                
                # Store the file path temporarily
                cl.user_session.set("pending_pdf_path", element.path)
                cl.user_session.set("pending_pdf_name", element.name)
                cl.user_session.set("step", "awaiting_source_name")
                return
    
    # Handle conversation flow based on current step
    step = cl.user_session.get("step", None)
    
    if step == "awaiting_source_name":
        source_name = message.content.strip()
        if not source_name:
            await cl.Message(content="❌ Source name cannot be empty. Please provide a source name:").send()
            return
        
        cl.user_session.set("source_name", source_name)
        cl.user_session.set("step", "awaiting_description")
        
        await cl.Message(
            content=f"✅ Source name set to: **{source_name}**\n\nNow, please provide a **description** for this document:"
        ).send()
        
    elif step == "awaiting_description":
        description = message.content.strip()
        if not description:
            await cl.Message(content="❌ Description cannot be empty. Please provide a description:").send()
            return
        
        cl.user_session.set("description", description)
        cl.user_session.set("step", "awaiting_pages_per_chunk")
        
        await cl.Message(
            content=f"✅ Description set!\n\nFinally, how many **pages per chunk** would you like? (Enter a number between 1 and 10, default is 3):"
        ).send()
        
    elif step == "awaiting_pages_per_chunk":
        try:
            pages_per_chunk = int(message.content.strip())
            if pages_per_chunk < 1 or pages_per_chunk > 10:
                await cl.Message(content="❌ Please enter a number between 1 and 10:").send()
                return
        except ValueError:
            await cl.Message(content="❌ Please enter a valid number between 1 and 10:").send()
            return
        
        cl.user_session.set("pages_per_chunk", pages_per_chunk)
        cl.user_session.set("step", None)
        
        # Now process the PDF
        await process_and_store_pdf()
        
    else:
        # No active flow, provide help
        await cl.Message(
            content="Please upload a PDF file using the attachment button (📎) to begin."
        ).send()


async def process_and_store_pdf():
    """Process the uploaded PDF and store it in the knowledge base"""
    pdf_path = cl.user_session.get("pending_pdf_path")
    pdf_name = cl.user_session.get("pending_pdf_name")
    source_name = cl.user_session.get("source_name")
    description = cl.user_session.get("description")
    pages_per_chunk = cl.user_session.get("pages_per_chunk")
    
    # Show processing message
    processing_msg = await cl.Message(
        content=f"⏳ Processing PDF **{pdf_name}**...\n\n"
                f"- Source Name: {source_name}\n"
                f"- Description: {description}\n"
                f"- Pages per Chunk: {pages_per_chunk}\n\n"
                f"This may take a few moments..."
    ).send()
    
    # Process the PDF
    result = process_pdf(
        pdf_file_path=pdf_path,
        source_name=source_name,
        description=description,
        pages_per_chunk=pages_per_chunk
    )
    
    # Send results
    if result["success"]:
        success_msg = f"""✅ **PDF Successfully Processed!**

**Document**: {result['source_name']}
**Total Pages**: {result['total_pages']}
**Total Chunks Created**: {result['total_chunks']}
**Pages per Chunk**: {result['pages_per_chunk']}

**Chunks Details**:
"""
        for chunk_info in result['processed_chunks']:
            success_msg += f"\n- Chunk {chunk_info['chunk_number']}: Pages {chunk_info['pages']} (DB ID: {chunk_info['doc_id']})"
        
        success_msg += "\n\n📚 Your document has been added to the knowledge base and can now be searched in the chat interface!"
        success_msg += "\n\n---\n\nWould you like to upload another PDF? Just click the attachment button (📎)!"
        
        await cl.Message(content=success_msg).send()
    else:
        await cl.Message(
            content=f"❌ **Error Processing PDF**\n\n{result['error']}\n\nPlease try again with a different file."
        ).send()
    
    # Clear session
    cl.user_session.set("pending_pdf_path", None)
    cl.user_session.set("pending_pdf_name", None)
    cl.user_session.set("source_name", "")
    cl.user_session.set("description", "")
    cl.user_session.set("pages_per_chunk", 3)
    cl.user_session.set("step", None)

