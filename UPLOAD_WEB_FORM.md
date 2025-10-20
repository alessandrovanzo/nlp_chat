# PDF Upload - Web Form Interface

## ✅ Done! The upload is now a normal webpage!

### What Changed?

- ❌ **OLD**: Separate Chainlit chat app on port 8002
- ✅ **NEW**: Built-in web form in the MCP server

### How to Use It

**1. Start the MCP server:**
```bash
python start_mcp_server.py
```

**2. Open the upload page:**
http://localhost:8001/upload

**3. You'll see a beautiful form with:**
- 📎 **File upload area** (drag & drop or click)
- 📝 **Source Name** text box
- 📄 **Description** text area
- 🎚️ **Pages per Chunk** slider (1-10)
- ✅ **Upload button**

**4. Fill it out and click upload!**

The page shows:
- ⏳ Progress bar while processing
- ✅ Success message with details
- ❌ Error messages if something goes wrong

## 📸 What It Looks Like

The form has:
- Modern gradient background (purple)
- White card with rounded corners
- Drag & drop file upload
- Interactive slider for chunk size
- Real-time progress feedback

## 🎯 Usage Example

1. Visit: http://localhost:8001/upload
2. Drag your PDF to the upload area
3. Type source name: "Kohavi Research Paper"
4. Type description: "Controlled experiments in online settings"
5. Move slider to: 3 pages per chunk
6. Click "Upload & Process PDF"
7. Wait ~30 seconds
8. See success message!

## 🔧 No Extra Setup Needed

- No additional terminal window
- No Chainlit dependency for upload
- No extra port (uses MCP server port 8001)
- Cleaner, simpler interface

## 📊 Complete Workflow

```
1. Start MCP server
   python start_mcp_server.py
   
2. Upload PDFs
   http://localhost:8001/upload
   
3. Search them (optional)
   chainlit run app.py
   http://localhost:8000
```

## 🎨 Features

- ✅ Drag & drop support
- ✅ Click to browse files
- ✅ Form validation (required fields)
- ✅ Interactive slider with live value
- ✅ Progress bar during upload
- ✅ Success/error messages
- ✅ Automatic form reset after success
- ✅ Beautiful, modern UI
- ✅ Responsive design
- ✅ No dependencies (pure HTML/CSS/JS)

## 🚀 Quick Commands

```bash
# Start MCP server (includes upload page)
python start_mcp_server.py

# Visit upload page
open http://localhost:8001/upload

# That's it!
```

## 💡 Pro Tips

1. **Drag & drop** is the fastest way to upload
2. **Good descriptions** improve search quality
3. **3 pages per chunk** works well for most documents
4. **Form resets** automatically after successful upload
5. **Progress bar** shows real-time status

## 🔍 Finding Your Uploads

After uploading, your PDFs are immediately searchable:

1. Start chat: `chainlit run app.py`
2. Open: http://localhost:8000
3. Ask: "What documents do you have?"
4. Your uploads will appear in search results!

## 📋 Old vs New

| Feature | Old (Chat) | New (Form) |
|---------|-----------|------------|
| Interface | Chainlit chat | Web form |
| Port | 8002 | 8001 |
| Terminals needed | 3 | 2 |
| File selection | Attachment button | Drag & drop + browse |
| Source name | Chat message | Text input |
| Description | Chat message | Text area |
| Pages/chunk | Chat message | Slider |
| Progress | Chat messages | Progress bar |
| Design | Chat bubbles | Modern form |

## ✨ Benefits

1. **Simpler**: One less service to run
2. **Faster**: Direct form submission
3. **Cleaner**: Purpose-built UI
4. **Better UX**: Drag & drop, sliders, instant feedback
5. **More intuitive**: Standard web form everyone knows

---

**Enjoy your new web form! 🎉**

The old chat-based upload (`pdf_upload_app.py`) is still there if you need it, but the web form is now the recommended way!

