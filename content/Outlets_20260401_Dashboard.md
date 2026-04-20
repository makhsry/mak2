### An Interactive Local Python Notebook (PyCompute + Puter.js)

This is a lightweight, single-file web application that mimics the **Jupyter Notebook** experience locally. It leverages **Pyodide** to run a full Python environment directly in browser without needing a remote backend. 

- Access the **`.html`** file [**here**](Tools_Dashboard.html).

It also has a sidebar **assistant** powered by **Puter.ai** that sees current code and output to provide debugging help or code suggestions. 

1.  **Navigate to the directory** containing **`.html`** file.
2.  **Start a Python local server** by running the following command in terminal:
    ```bash
    python -m http.server 8000
    ```
3.  **Access the dashboard** by opening browser and navigating to **`http://localhost:8000/FILENAME.html`**.

#### Script

```bash
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Numerical Dashboard with AI Companion</title>
    <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://js.puter.com/v2/"></script>
    <style>
        * { box-sizing: border-box; }
        html, body { height: 100%; overflow: hidden; }
        body { font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 1rem; background: #f8fafc; color: #1e293b; display: flex; gap: 0; height: 100vh; }
        .main-content { flex: 1; background: white; padding: 2rem; border-radius: 12px 0 0 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); min-width: 300px; overflow-y: auto; height: calc(100vh - 2rem); }
        .chat-sidebar { width: 350px; min-width: 250px; max-width: 600px; background: white; padding: 1.5rem; border-radius: 0 12px 12px 0; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: calc(100vh - 2rem); position: sticky; top: 1rem; overflow: hidden; }
        h2 { margin-top: 0; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
        textarea { width: 100%; height: 250px; font-family: 'Cascadia Code', monospace; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; background: #f1f5f9; box-sizing: border-box; }
        button { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 1rem; }
        #output { margin-top: 1.5rem; padding: 12px; background: #0f172a; color: #f8fafc; border-radius: 6px; min-height: 40px; white-space: pre-wrap; font-family: monospace; font-size: 13px; }
        #plot-area { margin-top: 1.5rem; background: white; border: 1px solid #e2e8f0; border-radius: 6px; min-height: 450px; }
        .status-bar { font-size: 0.85rem; padding: 8px 12px; border-radius: 4px; margin-bottom: 1rem; background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
        #chat-history { flex-grow: 1; overflow-y: auto; margin-bottom: 10px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; font-size: 14px; background: #fcfcfc; }
        .chat-input-wrapper { display: flex; gap: 5px; }
        #chat-input { flex-grow: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; }
        .api-label { font-size: 11px; font-weight: bold; color: #64748b; display: block; margin-bottom: 4px; }
        .msg { margin-bottom: 10px; padding: 8px; border-radius: 6px; }
        .user-msg { background: #dbeafe; color: #1e40af; }
        .ai-msg { background: #f1f5f9; color: #334155; }
        .cell { margin-bottom: 1rem; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; }
        .cell-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0; }
        .cell-type { font-size: 12px; font-weight: bold; color: #64748b; }
        .cell-actions { display: flex; gap: 8px; }
        .cell-actions button { padding: 4px 8px; font-size: 11px; margin: 0; }
        .cell-actions .run-btn { background: #16a34a; }
        .cell-actions .delete-btn { background: #dc2626; }
        .cell-actions .add-above-btn, .cell-actions .add-below-btn { background: #64748b; padding: 4px 6px; font-size: 11px; }
        .cell textarea { border: none; border-radius: 0; resize: none; transition: height 0.2s; }
        .cell textarea.collapsed { height: 38px !important; overflow: hidden; }
        .cell textarea.expanded { height: 250px; }
        .cell-output { padding: 12px; background: #0f172a; color: #f8fafc; border-radius: 0; min-height: 30px; font-family: monospace; font-size: 13px; white-space: pre-wrap; }
        .markdown-cell { background: #fafafa; }
        .markdown-cell textarea { background: #fafafa; font-family: -apple-system, system-ui, sans-serif; }
        .markdown-content { padding: 12px; font-family: -apple-system, system-ui, sans-serif; font-size: 14px; line-height: 1.6; }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 { margin-top: 0; color: #0f172a; }
        .markdown-content code { background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-family: 'Cascadia Code', monospace; font-size: 13px; }
        .markdown-content pre { background: #0f172a; color: #f8fafc; padding: 12px; border-radius: 6px; overflow-x: auto; }
        .editable { cursor: pointer; }
        .cell.dragging { opacity: 0.5; border: 2px dashed #3b82f6; }
        .cell.drag-over { border-top: 2px solid #3b82f6; }
        .cell-actions .move-btn { background: #64748b; }
        .cell-expand { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 12px; color: #64748b; padding: 2px 6px; background: #f1f5f9; border-radius: 3px; z-index: 5; }
        .cell-expand:hover { background: #e2e8f0; }
        .add-cell-bar { display: flex; align-items: center; gap: 15px; padding: 8px 20px; margin: 10px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; background: transparent; }
        .add-cell-bar:hover { background: #f8fafc; }
        .add-cell-btn { background: none; border: none; color: #94a3b8; font-size: 12px; cursor: pointer; padding: 4px 10px; border-radius: 4px; }
        .add-cell-btn:hover { background: #e2e8f0; color: #475569; }
        .cell-type-select { padding: 4px 8px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; color: #475569; }
        .resizer { width: 10px; cursor: col-resize; background: #e2e8f0; display: flex; align-items: center; justify-content: center; height: calc(100vh - 2rem); position: sticky; top: 1rem; border-radius: 4px; overflow: hidden; }
        .resizer:hover, .resizer.active { background: #3b82f6; }
        .resizer::before { content: '⋮'; color: #94a3b8; font-size: 16px; writing-mode: vertical-rl; }
        .resizer:hover::before, .resizer.active::before { color: white; }
    </style>
</head>
<body>

<div class="main-content">
    <h2>Numerical Analysis Dashboard</h2>
    <div id="status" class="status-bar">Initializing Pyodide...</div>
    <div style="margin-bottom: 1rem; padding: 1rem; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px;">
        <div style="font-size: 12px; font-weight: bold; color: #64748b; margin-bottom: 8px;">Install Python Packages</div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <input type="text" id="package-input" placeholder="Enter package names (e.g., scipy, matplotlib)" style="flex-grow: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px;">
            <button id="install-btn" onclick="installPackages()" style="margin: 0; padding: 8px 16px; font-size: 13px;">Install</button>
        </div>
        <div id="install-status" style="margin-top: 8px; font-size: 12px; color: #64748b;"></div>
    </div>
    <div id="cells-container"></div>
    <div class="add-cell-bar">
        <button class="add-cell-btn" onclick="addCell('code')" title="Insert code cell below">+ Code</button>
        <button class="add-cell-btn" onclick="addCell('markdown')" title="Insert markdown cell below">+ Markdown</button>
    </div>
    <div id="plot-area"></div>
</div>

<div class="resizer" id="resizer"></div>

<div class="chat-sidebar" id="chat-sidebar">
    <h3>AI Assistant</h3>
    <div id="puter-auth-bar" style="margin-bottom:12px;">
        <div id="puter-status" style="font-size:12px; color:#64748b; margin-bottom:6px;">Not connected to Puter</div>
        <button id="puter-connect-btn" onclick="connectPuter()" style="margin:0; padding:8px 14px; font-size:12px; width:100%;">Connect Puter Account</button>
        <button id="puter-signout-btn" onclick="signOut()" style="display:none; margin-top:6px; padding:8px 14px; font-size:12px; width:100%; background:#ef4444; color:white; border:none; border-radius:6px; cursor:pointer;">Sign Out</button>
    </div>
    <div id="model-bar" style="margin-bottom:12px; display:none;">
        <span class="api-label">MODEL:</span>
        <select id="model-selector" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:4px; font-size:12px; background:#f1f5f9;">
            <option value="">Loading models...</option>
        </select>
    </div>
    <div id="chat-history"></div>
    <div class="chat-input-wrapper">
        <input type="text" id="chat-input" placeholder="Ask a question..." onkeypress="if(event.key==='Enter') sendChat()">
        <button onclick="sendChat()" style="margin:0; padding:8px;">Send</button>
    </div>
</div>

<script>
    let pyodide;

    let directoryHandle = null;
    let isMounting = false;

    async function getDirectoryHandle() {
        if (!directoryHandle) {
            directoryHandle = await window.showDirectoryPicker({
                mode: 'readwrite'
            });
        }
        return directoryHandle;
    }

    async function setupEnvironment() {
        try {
            pyodide = await loadPyodide();
            await pyodide.loadPackage(['micropip']);
            
            pyodide.FS.mkdir('/root');
            
            document.getElementById('status').innerText = "Status: Server Active | Python Ready";
        } catch (err) {
            document.getElementById('status').innerText = "Error: " + err.message;
        }
    }

    const resizer = document.getElementById('resizer');
    const chatSidebar = document.getElementById('chat-sidebar');
    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        resizer.classList.add('active');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 250 && newWidth <= 600) {
            chatSidebar.style.width = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });

    async function installPackages() {
        const input = document.getElementById('package-input');
        const status = document.getElementById('install-status');
        const packages = input.value.trim().split(/[\s,]+/).filter(p => p);

        if (!packages.length) {
            status.innerText = "Please enter at least one package name.";
            status.style.color = "#dc2626";
            return;
        }

        status.innerText = `Installing: ${packages.join(', ')}...`;
        status.style.color = "#1e40af";

        try {
            await pyodide.loadPackage(packages);
            status.innerText = `Successfully installed: ${packages.join(', ')}`;
            status.style.color = "#16a34a";
            input.value = '';
        } catch (err) {
            status.innerText = `Installation failed: ${err.message}`;
            status.style.color = "#dc2626";
        }
    }

    let cellCounter = 0;

    function addCell(type, afterId = null) {
        const container = document.getElementById('cells-container');
        const id = 'cell-' + (++cellCounter);
        const isMarkdown = type === 'markdown';
        
        const cell = document.createElement('div');
        cell.className = 'cell' + (isMarkdown ? ' markdown-cell' : '');
        cell.id = id;
        cell.draggable = true;
        
        cell.innerHTML = `
            <div class="cell-header">
                <span class="cell-type" style="cursor: grab;" title="Drag to reorder">☰ ${isMarkdown ? 'Markdown' : 'Code'}</span>
                <div class="cell-actions">
                    <select id="${id}-type" class="cell-type-select" onchange="updateCellType('${id}', this.value)">
                        <option value="code" ${!isMarkdown ? 'selected' : ''}>Code</option>
                        <option value="markdown" ${isMarkdown ? 'selected' : ''}>Markdown</option>
                    </select>
                    <button class="add-above-btn" onclick="addCellAt('${id}', 'above', 'code')" title="Add code above">↑C</button>
                    <button class="add-above-btn" onclick="addCellAt('${id}', 'above', 'markdown')" title="Add markdown above">↑M</button>
                    <button class="add-below-btn" onclick="addCellAt('${id}', 'below', 'code')" title="Add code below">↓C</button>
                    <button class="add-below-btn" onclick="addCellAt('${id}', 'below', 'markdown')" title="Add markdown below">↓M</button>
                    <button class="run-btn" onclick="runCell('${id}')">Run</button>
                    <button class="delete-btn" onclick="deleteCell('${id}')">Delete</button>
                </div>
            </div>
            <textarea id="${id}-input" class="collapsed" rows="1" placeholder="${isMarkdown ? 'Enter markdown text...' : 'Enter Python code...'}" ${isMarkdown ? 'ondblclick="toggleMarkdownEdit(\'' + id + '\')"' : ''} oninput="autoResize(this)" onclick="expandCell('${id}')">${isMarkdown ? '# Heading\n\nEnter your markdown here...' : '# your code here'}</textarea>
            <span class="cell-expand" onclick="toggleExpand('${id}')" title="Click to expand">⬇</span>
            ${isMarkdown ? `<div id="${id}-rendered" class="markdown-content" style="display:none;" onclick="toggleMarkdownEdit('${id}')"></div>` : ''}
            <div id="${id}-output" class="cell-output" style="display: none;"></div>
        `;
        
        setTimeout(() => {
            const textarea = document.getElementById(id + '-input');
            autoResize(textarea);
        }, 0);
        
        cell.addEventListener('dragstart', (e) => {
            cell.classList.add('dragging');
            e.dataTransfer.setData('text/plain', id);
        });
        
        cell.addEventListener('dragend', () => {
            cell.classList.remove('dragging');
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('drag-over'));
        });
        
        cell.addEventListener('dragover', (e) => {
            e.preventDefault();
            const dragging = document.querySelector('.dragging');
            if (dragging && dragging !== cell) {
                cell.classList.add('drag-over');
            }
        });
        
        cell.addEventListener('dragleave', () => {
            cell.classList.remove('drag-over');
        });
        
        cell.addEventListener('drop', (e) => {
            e.preventDefault();
            const draggedId = e.dataTransfer.getData('text/plain');
            const dragged = document.getElementById(draggedId);
            if (dragged && dragged !== cell) {
                container.insertBefore(dragged, cell);
            }
            cell.classList.remove('drag-over');
        });
        
        if (afterId) {
            const afterCell = document.getElementById(afterId);
            if (afterCell && afterCell.nextSibling) {
                container.insertBefore(cell, afterCell.nextSibling);
            } else {
                container.appendChild(cell);
            }
        } else {
            container.appendChild(cell);
        }
    }

    function createCellElement(type) {
        const container = document.getElementById('cells-container');
        const id = 'cell-' + (++cellCounter);
        const isMarkdown = type === 'markdown';
        
        const cell = document.createElement('div');
        cell.className = 'cell' + (isMarkdown ? ' markdown-cell' : '');
        cell.id = id;
        cell.draggable = true;
        
        cell.innerHTML = `
            <div class="cell-header">
                <span class="cell-type" style="cursor: grab;" title="Drag to reorder">☰ ${isMarkdown ? 'Markdown' : 'Code'}</span>
                <div class="cell-actions">
                    <select id="${id}-type" class="cell-type-select" onchange="updateCellType('${id}', this.value)">
                        <option value="code" ${!isMarkdown ? 'selected' : ''}>Code</option>
                        <option value="markdown" ${isMarkdown ? 'selected' : ''}>Markdown</option>
                    </select>
                    <button class="add-above-btn" onclick="addCellAt('${id}', 'above', 'code')" title="Add code above">↑C</button>
                    <button class="add-above-btn" onclick="addCellAt('${id}', 'above', 'markdown')" title="Add markdown above">↑M</button>
                    <button class="add-below-btn" onclick="addCellAt('${id}', 'below', 'code')" title="Add code below">↓C</button>
                    <button class="add-below-btn" onclick="addCellAt('${id}', 'below', 'markdown')" title="Add markdown below">↓M</button>
                    <button class="run-btn" onclick="runCell('${id}')">Run</button>
                    <button class="delete-btn" onclick="deleteCell('${id}')">Delete</button>
                </div>
            </div>
            <textarea id="${id}-input" class="collapsed" rows="1" placeholder="${isMarkdown ? 'Enter markdown text...' : 'Enter Python code...'}" ${isMarkdown ? 'ondblclick="toggleMarkdownEdit(\'' + id + '\')"' : ''} oninput="autoResize(this)" onclick="expandCell('${id}')">${isMarkdown ? '# Heading\n\nEnter your markdown here...' : '# your code here'}</textarea>
            <span class="cell-expand" onclick="toggleExpand('${id}')" title="Click to expand">⬇</span>
            ${isMarkdown ? `<div id="${id}-rendered" class="markdown-content" style="display:none;" onclick="toggleMarkdownEdit('${id}')"></div>` : ''}
            <div id="${id}-output" class="cell-output" style="display: none;"></div>
        `;
        
        setTimeout(() => {
            const textarea = document.getElementById(id + '-input');
            autoResize(textarea);
        }, 0);
        
        cell.addEventListener('dragstart', (e) => {
            cell.classList.add('dragging');
            e.dataTransfer.setData('text/plain', id);
        });
        
        cell.addEventListener('dragend', () => {
            cell.classList.remove('dragging');
            document.querySelectorAll('.cell').forEach(c => c.classList.remove('drag-over'));
        });
        
        cell.addEventListener('dragover', (e) => {
            e.preventDefault();
            const dragging = document.querySelector('.dragging');
            if (dragging && dragging !== cell) {
                cell.classList.add('drag-over');
            }
        });
        
        cell.addEventListener('dragleave', () => {
            cell.classList.remove('drag-over');
        });
        
        cell.addEventListener('drop', (e) => {
            e.preventDefault();
            const draggedId = e.dataTransfer.getData('text/plain');
            const dragged = document.getElementById(draggedId);
            if (dragged && dragged !== cell) {
                container.insertBefore(dragged, cell);
            }
            cell.classList.remove('drag-over');
        });
        
        return cell;
    }

    function toggleMarkdownEdit(cellId) {
        const input = document.getElementById(cellId + '-input');
        const rendered = document.getElementById(cellId + '-rendered');
        
        if (input.style.display !== 'none') {
            rendered.innerHTML = parseMarkdown(input.value);
            input.style.display = 'none';
            rendered.style.display = 'block';
        } else {
            input.style.display = 'block';
            rendered.style.display = 'none';
        }
    }

    function parseMarkdown(text) {
        let html = text
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
            .replace(/\n/g, '<br>');
        return html;
    }

    async function runCell(cellId) {
        const input = document.getElementById(cellId + '-input');
        const output = document.getElementById(cellId + '-output');
        const rendered = document.getElementById(cellId + '-rendered');
        const cell = document.getElementById(cellId);
        const isMarkdown = cell.classList.contains('markdown-cell');
        
        if (isMarkdown) {
            if (input.style.display !== 'none') {
                rendered.innerHTML = parseMarkdown(input.value);
                input.style.display = 'none';
                rendered.style.display = 'block';
            }
            output.style.display = 'none';
            return;
        }
        
        const code = input.value;
        output.style.display = 'block';
        output.innerText = 'Running...';
        
        try {
            const isMounted = pyodide.FS.mounts.some(m => m.mountpoint === '/root');
            
            if (!isMounted) {
                try {
                    pyodide.FS.unmount('/root');
                } catch (e) {}
                
                try {
                    pyodide.FS.rmdir('/root');
                } catch (e) {}

                pyodide.FS.mkdir('/root');
                const handle = await getDirectoryHandle();
                await pyodide.mountNativeFS('/root', handle);
            }

            output.innerText = '';

            pyodide.setStdout({
                batched: (str) => {
                    output.innerText += str + '\n';
                }
            });

            let result = await pyodide.runPythonAsync(code);
            
            if (result !== undefined && result !== null) {
                const resultStr = result.toString();
                if (output.innerText.trim() !== resultStr.trim()) {
                    output.innerText += resultStr;
                }
            } else if (output.innerText === '') {
                output.innerText = 'Success';
            }
        } catch (err) {
            output.innerText = 'Error: ' + err.message;
        }
    }

    function deleteCell(cellId) {
        document.getElementById(cellId).remove();
    }

    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    function expandCell(cellId) {
        const textarea = document.getElementById(cellId + '-input');
        textarea.classList.remove('collapsed');
        textarea.classList.add('expanded');
        autoResize(textarea);
    }

    function toggleExpand(cellId) {
        const textarea = document.getElementById(cellId + '-input');
        const expandIcon = document.querySelector('#' + cellId + ' .cell-expand');
        
        if (textarea.classList.contains('collapsed')) {
            textarea.classList.remove('collapsed');
            textarea.classList.add('expanded');
            autoResize(textarea);
            expandIcon.innerHTML = '⬆';
        } else {
            textarea.classList.remove('expanded');
            textarea.classList.add('collapsed');
            textarea.style.height = '38px';
            expandIcon.innerHTML = '⬇';
        }
    }

    function addCellAt(cellId, position, type) {
        const container = document.getElementById('cells-container');
        const currentCell = document.getElementById(cellId);
        const cellType = type || 'code';
        
        const newCell = createCellElement(cellType);
        
        if (position === 'above') {
            container.insertBefore(newCell, currentCell);
        } else {
            if (currentCell.nextSibling) {
                container.insertBefore(newCell, currentCell.nextSibling);
            } else {
                container.appendChild(newCell);
            }
        }
    }

    function updateCellType(cellId, type) {
        const cell = document.getElementById(cellId);
        const isMarkdown = type === 'markdown';
        
        if (isMarkdown) {
            cell.classList.add('markdown-cell');
        } else {
            cell.classList.remove('markdown-cell');
        }
        
        const typeLabel = cell.querySelector('.cell-type');
        typeLabel.innerHTML = '☰ ' + (isMarkdown ? 'Markdown' : 'Code');
    }

    async function loadModels() {
        const selector = document.getElementById('model-selector');
        const modelBar = document.getElementById('model-bar');
        modelBar.style.display = 'block';
        try {
            const models = await puter.ai.listModels();
            const priority = ['claude', 'openai', 'google', 'meta', 'mistral', 'deepseek', 'xai'];
            models.sort((a, b) => {
                const ai = priority.findIndex(p => (a.id || '').toLowerCase().includes(p));
                const bi = priority.findIndex(p => (b.id || '').toLowerCase().includes(p));
                return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
            });
            selector.innerHTML = models.map(m => {
                const label = m.name || m.id;
                return `<option value="${m.id}">${label}</option>`;
            }).join('');
            const defaultModel = models.find(m => m.id && m.id.includes('claude-sonnet-4'));
            if (defaultModel) selector.value = defaultModel.id;
        } catch (err) {
            selector.innerHTML = '<option value="">Failed to load models</option>';
        }
    }

    async function connectPuter() {
        const btn = document.getElementById('puter-connect-btn');
        const statusEl = document.getElementById('puter-status');
        const signoutBtn = document.getElementById('puter-signout-btn');
        
        btn.disabled = true;
        btn.innerText = 'Connecting...';
        
        try {
            await puter.auth.signIn({ attempt_temp_user_creation: true });
            const user = await puter.auth.getUser();
            statusEl.innerText = `Connected as: ${user.username}`;
            statusEl.style.color = '#16a34a';
            btn.style.display = 'none';
            signoutBtn.style.display = 'block';
            await loadModels();
        } catch (err) {
            statusEl.innerText = 'Connection failed. Try again.';
            statusEl.style.color = '#dc2626';
            // Explicitly reset button state on failure
            btn.disabled = false;
            btn.innerText = 'Connect Puter Account';
        } finally {
            // Safety check: if sign-in didn't complete, re-enable button
            if (!puter.auth.isSignedIn()) {
                btn.disabled = false;
                btn.innerText = 'Connect Puter Account';
            }
        }
    }

    function signOut() {
        puter.auth.signOut();
        
        const btn = document.getElementById('puter-connect-btn');
        const signoutBtn = document.getElementById('puter-signout-btn');
        
        // Reset the UI elements
        document.getElementById('puter-status').innerText = "Not connected to Puter";
        document.getElementById('puter-status').style.color = '#64748b';
        
        // Force reset the connect button state
        btn.style.display = 'block';
        btn.disabled = false;
        btn.innerText = 'Connect Puter Account';
        
        signoutBtn.style.display = 'none';
        
        // Hide and clear the model selector
        document.getElementById('model-bar').style.display = 'none';
        document.getElementById('model-selector').innerHTML = '<option value="">Loading models...</option>';
        
        // Clear chat history
        document.getElementById('chat-history').innerHTML = '';
    }

    async function sendChat() {
        const input = document.getElementById('chat-input');
        const history = document.getElementById('chat-history');
        const text = input.value.trim();

        if (!text) return;

        if (!puter.auth.isSignedIn()) {
            history.innerHTML += `<div class="msg ai-msg" style="color:#b45309"><b>Note:</b> Please connect your Puter account first.</div>`;
            history.scrollTop = history.scrollHeight;
            return;
        }

        const cells = document.querySelectorAll('.cell');
        let contextData = "Current Dashboard State:\n";
        cells.forEach((c, i) => {
            const cInput = document.getElementById(c.id + '-input')?.value || "";
            const cOutput = document.getElementById(c.id + '-output')?.innerText || "";
            contextData += `[Cell ${i+1} Code]:\n${cInput}\n[Cell ${i+1} Output]:\n${cOutput}\n---\n`;
        });

        const fullPrompt = `Dashboard Context:\n${contextData}\n\nUser Question: ${text}\n\nNote: Local files are at '/root/'. If providing code, use that path.`;

        const model = document.getElementById('model-selector').value;
        history.innerHTML += `<div class="msg user-msg"><b>You:</b> ${text}</div>`;
        input.value = '';

        try {
            const response = await puter.ai.chat(fullPrompt, { model });
            const aiText = response?.message?.content?.[0]?.text || response?.toString() || "Ready.";
            const formattedAiText = parseMarkdown(aiText);
            
            history.innerHTML += `<div class="msg ai-msg"><b>AI:</b><div class="markdown-content">${formattedAiText}</div></div>`;
        } catch (err) {
            history.innerHTML += `<div class="msg ai-msg" style="color:red"><b>Error:</b> ${err.message}</div>`;
        }
        history.scrollTop = history.scrollHeight;
    }

    window.addEventListener('load', () => {
        if (puter.auth.isSignedIn()) {
            puter.auth.getUser().then(user => {
                document.getElementById('puter-status').innerText = `Connected as: ${user.username}`;
                document.getElementById('puter-status').style.color = '#16a34a';
                document.getElementById('puter-connect-btn').style.display = 'none';
                document.getElementById('puter-signout-btn').style.display = 'block';
                loadModels();
            });
        }
    });

    setupEnvironment();
</script>
</body>
</html>
```