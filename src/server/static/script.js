const fileUpload = document.getElementById('fileUpload');
const fileInput = document.getElementById('pdfFile');
const fileName = document.getElementById('fileName');
const slider = document.getElementById('pagesPerChunk');
const sliderValue = document.getElementById('sliderValue');
const form = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const progress = document.getElementById('progress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const message = document.getElementById('message');

// File upload interactions
fileUpload.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileName.textContent = e.target.files[0].name;
    }
});

// Drag and drop
fileUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUpload.classList.add('dragover');
});

fileUpload.addEventListener('dragleave', () => {
    fileUpload.classList.remove('dragover');
});

fileUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        const validTypes = ['application/pdf', 'application/epub+zip', 'text/plain'];
        const validExtensions = ['.pdf', '.epub', '.txt'];
        const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (validTypes.includes(file.type) || validExtensions.includes(fileExt)) {
            fileInput.files = e.dataTransfer.files;
            fileName.textContent = file.name;
        } else {
            alert('Please upload a PDF, EPUB, or TXT file');
        }
    }
});

// Slider
slider.addEventListener('input', (e) => {
    sliderValue.textContent = e.target.value;
});

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('pdf_file', fileInput.files[0]);
    formData.append('source_name', document.getElementById('sourceName').value);
    formData.append('description', document.getElementById('description').value);
    formData.append('pages_per_chunk', slider.value);
    formData.append('prepend_metadata', document.getElementById('prependMetadata').checked);
    
    // Show progress
    submitBtn.disabled = true;
    progress.style.display = 'block';
    message.style.display = 'none';
    progressFill.style.width = '30%';
    progressText.textContent = 'Uploading document...';
    
    try {
        const response = await fetch('/upload-pdf', {
            method: 'POST',
            body: formData
        });
        
        progressFill.style.width = '70%';
        progressText.textContent = 'Processing and creating embeddings...';
        
        const result = await response.json();
        
        progressFill.style.width = '100%';
        
        if (result.success) {
            const fileType = result.file_type ? result.file_type.toUpperCase() : 'Document';
            const unitName = result.unit_name || 'pages';
            
            message.className = 'message success';
            let htmlContent = `
                <strong>Success!</strong> ${fileType} processed successfully.
                <div class="result-details">
                    <strong>Document:</strong> ${result.source_name}<br>
                    <strong>Total ${unitName.charAt(0).toUpperCase() + unitName.slice(1)}s:</strong> ${result.total_pages}<br>
                    <strong>Chunks Created:</strong> ${result.total_chunks}<br>
                    <strong>Successful Chunks:</strong> ${result.successful_chunks || result.total_chunks}<br>
                    <strong>${unitName.charAt(0).toUpperCase() + unitName.slice(1)}s per Chunk:</strong> ${result.pages_per_chunk}
            `;
            
            // Add note about splits if any
            if (result.note) {
                htmlContent += `<br><strong>Note:</strong> ${result.note}`;
            }
            
            // Add warning about failed chunks if any
            if (result.failed_chunks && result.failed_chunks.length > 0) {
                htmlContent += `<br><br><strong style="color: #ff9800;">⚠️ Failed Chunks:</strong>`;
                result.failed_chunks.forEach(fc => {
                    htmlContent += `<br>• Chunk ${fc.chunk_number} (${unitName}s ${fc.pages}): ${fc.error}`;
                });
            }
            
            htmlContent += '</div>';
            message.innerHTML = htmlContent;
            message.style.display = 'block';
            
            // Reset form
            form.reset();
            fileName.textContent = '';
            sliderValue.textContent = '3';
            
            // Reload sources after successful upload
            setTimeout(() => {
                loadSources();
            }, 1500);
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        message.className = 'message error';
        message.innerHTML = `<strong>Error:</strong> ${error.message}`;
        message.style.display = 'block';
    } finally {
        setTimeout(() => {
            progress.style.display = 'none';
            progressFill.style.width = '0%';
            submitBtn.disabled = false;
        }, 1000);
    }
});

// Sources Management
const loadingSources = document.getElementById('loadingSources');
const sourcesList = document.getElementById('sourcesList');

async function loadSources() {
    try {
        loadingSources.style.display = 'block';
        sourcesList.innerHTML = '';
        
        const response = await fetch('/sources');
        const data = await response.json();
        
        loadingSources.style.display = 'none';
        
        if (data.success && data.sources.length > 0) {
            renderSources(data.sources);
        } else {
            sourcesList.innerHTML = '<div class="no-sources">No sources yet. Upload your first document above!</div>';
        }
    } catch (error) {
        loadingSources.style.display = 'none';
        sourcesList.innerHTML = '<div class="no-sources" style="color: #dc3545;">Error loading sources: ' + error.message + '</div>';
    }
}

function renderSources(sources) {
    sourcesList.innerHTML = '';
    
    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item' + (source.active ? '' : ' inactive');
        
        const sourceType = (source.source_type || 'unknown').toUpperCase();
        
        sourceItem.innerHTML = `
            <div class="source-info">
                <div class="source-title ${source.active ? '' : 'inactive'}">${source.title}</div>
                <div class="source-meta">
                    <strong>Type:</strong> ${sourceType} | 
                    <strong>Chunks:</strong> ${source.chunk_count} | 
                    <strong>Status:</strong> ${source.active ? '✅ Active for MCP' : '⭕ Inactive'}
                    <br>
                    <strong>Description:</strong> ${source.description || 'No description'}
                </div>
            </div>
            <div class="source-actions">
                <label class="toggle-switch">
                    <input type="checkbox" ${source.active ? 'checked' : ''} 
                           onchange="toggleSource('${source.title.replace(/'/g, "\\'")}', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
                <button class="delete-btn" onclick="deleteSource('${source.title.replace(/'/g, "\\'")}')">
                    Delete
                </button>
            </div>
        `;
        
        sourcesList.appendChild(sourceItem);
    });
}

async function toggleSource(title, active) {
    try {
        const response = await fetch('/sources/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, active })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Reload sources to reflect changes
            await loadSources();
        } else {
            alert('Error toggling source: ' + result.error);
            // Reload to revert the toggle
            await loadSources();
        }
    } catch (error) {
        alert('Error toggling source: ' + error.message);
        await loadSources();
    }
}

async function deleteSource(title) {
    if (!confirm(`Are you sure you want to delete "${title}" and all its chunks from the database? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch('/sources/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully deleted "${title}" (${result.deleted_chunks} chunks removed)`);
            await loadSources();
        } else {
            alert('Error deleting source: ' + result.error);
        }
    } catch (error) {
        alert('Error deleting source: ' + error.message);
    }
}

// Load sources when page loads
loadSources();

