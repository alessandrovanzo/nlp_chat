"""
Chainlit Document Upload Application
Allows users to upload PDFs and EPUBs and add them to the knowledge base
"""
import chainlit as cl
from pdf_processor import process_document, get_file_type
import os
import tempfile


@cl.on_chat_start
async def start():
    """Initialize the document upload session"""
    # Set default values
    cl.user_session.set("pages_per_chunk", 3)
    cl.user_session.set("source_name", "")
    cl.user_session.set("description", "")
    
    # Welcome message with instructions
    welcome_msg = """# 📄 Document Upload to Knowledge Base

Welcome! This tool allows you to upload PDF and EPUB documents to the knowledge base.

## Instructions:
1. **Upload a PDF or EPUB file** using the attachment button below
2. I'll ask you for:
   - **Source Name**: A title for your document
   - **Description**: A brief description of the content
   - **Units per Chunk**: How many pages/chapters to group together (1-10)
3. The document will be processed, embedded, and added to the knowledge base

Ready to upload your first document? Click the attachment button (📎) to get started!
"""
    
    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def handle_message(message: cl.Message):
    """Handle messages and file uploads"""
    
    # Check if there's a file attachment
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                # Check if it's a supported file type
                filename_lower = element.name.lower()
                if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.epub')):
                    await cl.Message(
                        content="❌ Unsupported file format. Please upload a PDF or EPUB file only."
                    ).send()
                    return
                
                # Determine file type
                file_type = get_file_type(element.path)
                if file_type == 'unsupported':
                    await cl.Message(
                        content="❌ Unsupported file format. Please upload a PDF or EPUB file."
                    ).send()
                    return
                
                # Ask for source name
                file_type_display = file_type.upper()
                await cl.Message(
                    content=f"📝 Great! I received your {file_type_display}. Now, please provide the **source name** (a title for this document):"
                ).send()
                
                # Store the file path temporarily
                cl.user_session.set("pending_pdf_path", element.path)
                cl.user_session.set("pending_pdf_name", element.name)
                cl.user_session.set("file_type", file_type)
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
        
        file_type = cl.user_session.get("file_type", "pdf")
        unit_name = "chapters" if file_type == "epub" else "pages"
        
        await cl.Message(
            content=f"✅ Description set!\n\nFinally, how many **{unit_name} per chunk** would you like? (Enter a number between 1 and 10, default is 3):"
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
            content="Please upload a PDF or EPUB file using the attachment button (📎) to begin."
        ).send()


async def process_and_store_pdf():
    """Process the uploaded document and store it in the knowledge base"""
    pdf_path = cl.user_session.get("pending_pdf_path")
    pdf_name = cl.user_session.get("pending_pdf_name")
    source_name = cl.user_session.get("source_name")
    description = cl.user_session.get("description")
    pages_per_chunk = cl.user_session.get("pages_per_chunk")
    file_type = cl.user_session.get("file_type", "pdf")
    
    file_type_display = file_type.upper()
    unit_name = "chapters" if file_type == "epub" else "pages"
    
    # Show processing message
    processing_msg = await cl.Message(
        content=f"⏳ Processing {file_type_display} **{pdf_name}**...\n\n"
                f"- Source Name: {source_name}\n"
                f"- Description: {description}\n"
                f"- {unit_name.capitalize()} per Chunk: {pages_per_chunk}\n\n"
                f"This may take a few moments..."
    ).send()
    
    # Process the document
    result = process_document(
        file_path=pdf_path,
        source_name=source_name,
        description=description,
        pages_per_chunk=pages_per_chunk
    )
    
    # Send results
    if result["success"]:
        result_file_type = result.get('file_type', file_type).upper()
        result_unit_name = result.get('unit_name', unit_name)
        
        success_msg = f"""✅ **{result_file_type} Successfully Processed!**

**Document**: {result['source_name']}
**Total {result_unit_name.capitalize()}**: {result['total_pages']}
**Total Chunks Created**: {result['total_chunks']}
**{result_unit_name.capitalize()} per Chunk**: {result['pages_per_chunk']}
"""
        
        # Add note about splits if any
        if result.get('note'):
            success_msg += f"\n⚠️ **Note**: {result['note']}\n"
        
        success_msg += "\n**Chunks Details**:\n"
        
        for chunk_info in result['processed_chunks']:
            success_msg += f"\n- Chunk {chunk_info['chunk_number']}: {result_unit_name.capitalize()} {chunk_info['pages']} (DB ID: {chunk_info['doc_id']})"
        
        success_msg += "\n\n📚 Your document has been added to the knowledge base and can now be searched in the chat interface!"
        success_msg += "\n\n---\n\nWould you like to upload another document? Just click the attachment button (📎)!"
        
        await cl.Message(content=success_msg).send()
    else:
        await cl.Message(
            content=f"❌ **Error Processing {file_type_display}**\n\n{result['error']}\n\nPlease try again with a different file or check if the file is corrupted."
        ).send()
    
    # Clear session
    cl.user_session.set("pending_pdf_path", None)
    cl.user_session.set("pending_pdf_name", None)
    cl.user_session.set("source_name", "")
    cl.user_session.set("description", "")
    cl.user_session.set("pages_per_chunk", 3)
    cl.user_session.set("file_type", None)
    cl.user_session.set("step", None)

