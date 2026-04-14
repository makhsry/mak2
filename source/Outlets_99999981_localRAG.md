### Local RAG Pipeline — Ollama + ChromaDB + LangChain

This doc describes how to use the `local RAG` pipeline with `Ollama`, `ChromaDB`, and `LangChain`. 

- **Access** scripts [**click here**](Outlets_99999981_localRAG.zip) or see **the scripts below**.

**Workflow reference**

- You must have **`Ollama`** installed and have pulled the required model (for example: `ollama pull gemma4:latest`) for the scripts to work.
- Before running any script, **`Ollama`** must be running in the background: `ollama serve`.
- Use **`--help`** to see all available options for each script.

| Task | Command |
| :--- | :--- |
| Setup **database** (from folder: `folders.txt`) | `python database.py --rebuild` |
| Update **database** (from folder: `folders.txt`) | `python database.py --append` |
| **Ask** a question (uses file: `prompt.txt`) | `python query.py` |
| **Ask** on command line | `python query.py -q "..."` |
| **Ask** in interactive chat | `python query.py --interactive` |
| **Edit** shared settings (models, paths, chunking) | `config.py` |

**Changing models or settings**

Open `config.py` and edit the values:

```python
OLLAMA_MODEL    = "gemma4:latest"   # LLM for answering
EMBEDDING_MODEL = "nomic-embed-text"       # Embedding model
CHUNK_SIZE      = 500                   # Number of characters per chunk
CHUNK_OVERLAP   = 50                    # Number of characters to overlap between chunks
TOP_K_RESULTS   = 5                     # Number of chunks to retrieve
```

**Steps to prepare the WSL environment**

- Update and upgrade: `sudo apt update && sudo apt upgrade -y` 
- Install dependencies: `sudo apt install -y build-essential python3-pip python3-venv curl git libmagic-dev poppler-utils tesseract-ocr`.
- Create a python virtual environment: `python3 -m venv venv` 
- Activate it: `source venv/bin/activate`. 
- Install pip packages: `pip install -r requirements.txt`.
- Install Ollama: `https://ollama.com/download` or `curl -fsSL https://ollama.com/install.sh | sh`.
- Pull the required model: `ollama pull gemma4:latest` and `ollama pull nomic-embed-text`.

The **requirements.txt**:
```bash 
langchain
langchain-community
langchain-core
langchain-ollama
chromadb
python-dotenv
langchain-unstructured
langchain-text-splitters
langchain-community
langchain-core
langchain-ollama
chromadb
python-dotenv
langchain-unstructured
langchain-text-splitters
```

#### Scripts

- **`database.py`**: 

Builds or updates the ChromaDB database from the folders listed in `folders.txt`.

```bash
import argparse
import os
import shutil
import sys
import uuid

# Modern LangChain Imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
#from langchain_community.document_loaders import (
#    PyPDFLoader,
#    TextLoader,
#    BSHTMLLoader,
#    UnstructuredFileLoader,
#)
from langchain_community.document_loaders import PyPDFLoader, TextLoader, BSHTMLLoader
from langchain_unstructured import UnstructuredLoader

import config

# Priority mapping for loaders
SPECIFIC_LOADERS = {
    ".pdf": PyPDFLoader,
    ".html": BSHTMLLoader,
    ".htm": BSHTMLLoader,
    ".txt": TextLoader,
}

# Document loading

def load_folder(folder_path: str, indexed_sources: set, append_mode: bool) -> list[Document]:
    """Smartly loads files, reports actions, and isolates failures."""
    docs: list[Document] = []
    folder_path = os.path.abspath(folder_path)
    error_dir = os.path.join(folder_path, ".not_indexed")

    for root, dirs, files in os.walk(folder_path):
        if ".not_indexed" in root:
            continue
            
        for filename in files:
            file_path = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()

            # Report skipping if in append mode and file is already indexed
            if append_mode and file_path in indexed_sources:
                print(f"  [Skip] Already indexed: {filename}")
                continue

            #loader_cls = SPECIFIC_LOADERS.get(ext, UnstructuredFileLoader)
            loader_cls = SPECIFIC_LOADERS.get(ext, UnstructuredLoader)
            
            try:
                print(f"  [Process] Loading: {filename} ({loader_cls.__name__})")
                loader = loader_cls(file_path)
                docs.extend(loader.load())
            except Exception as exc:
                print(f"  [!! Error] Failed to read {filename}: {exc}")
                if not os.path.exists(error_dir):
                    os.makedirs(error_dir)
                try:
                    dest = os.path.join(error_dir, filename)
                    if os.path.exists(dest):
                        dest = f"{dest}_{uuid.uuid4().hex[:4]}"
                    shutil.move(file_path, dest)
                    print(f"  [Moved] {filename} -> .not_indexed/")
                except Exception as move_exc:
                    print(f"  [Critical] Could not move file: {move_exc}")
    return docs

# Main Logic

def main():
    parser = argparse.ArgumentParser(
        description=(
            "AUREL SYSTEMS: Vector Database Manager\n\n"
            "Manages the ChromaDB store for engineering document analysis.\n"
            "This script tracks which files are indexed to avoid duplicate processing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Usage Examples:\n"
            "  python database.py --append    # Only index new files (Recommended)\n"
            "  python database.py --rebuild   # Wipe and re-index all folders\n"
        )
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rebuild", action="store_true", help="Wipe and rebuild the DB from scratch.")
    group.add_argument("--append", action="store_true", help="Add only new files.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    folders = config.load_folders()
    embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
    indexed_sources = set()

    # 1. Initialize Mode
    if args.rebuild:
        if os.path.exists(config.CHROMA_DB_PATH):
            print(f"[db] Action: Wiping database at {config.CHROMA_DB_PATH}")
            shutil.rmtree(config.CHROMA_DB_PATH)
    elif os.path.exists(config.CHROMA_DB_PATH):
        vectorstore = Chroma(persist_directory=config.CHROMA_DB_PATH, embedding_function=embeddings)
        existing_data = vectorstore.get()
        indexed_sources = set(m.get('source') for m in existing_data['metadatas'])
        print(f"[db] Action: Append mode. Found {len(indexed_sources)} files already in database.")

    # 2. Document Collection
    all_new_docs = []
    for f in folders:
        print(f"\n[db] Scanning Folder: {f}")
        folder_docs = load_folder(f, indexed_sources, args.append)
        all_new_docs.extend(folder_docs)

    if not all_new_docs:
        print("\n[db] Result: No new documents to index. Database is up to date.")
        return

    # 3. Chunking & Embedding
    print(f"\n[db] Splitting {len(all_new_docs)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, 
        chunk_overlap=config.CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(all_new_docs)

    print(f"[db] Embedding {len(chunks)} chunks using '{config.EMBEDDING_MODEL}'...")
    
    if args.rebuild or not os.path.exists(config.CHROMA_DB_PATH):
        Chroma.from_documents(
            documents=chunks, 
            embedding=embeddings, 
            persist_directory=config.CHROMA_DB_PATH
        )
    else:
        vectorstore.add_documents(chunks)
    
    print(f"\n[db] ✓ Success! Added {len(chunks)} new chunks to the vector store.")

if __name__ == "__main__":
    main()
```

- **`query.py`**: 

Queries the database using the prompt in `prompt.txt` or a custom query.

```bash
"""
query.py — Query the ChromaDB vector store with RAG.

Usage
-----
    python query.py

Reads the prompt from prompt.txt, retrieves relevant documents from the
vector store, and generates an answer using Ollama.
"""

import config
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
#from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA

def main():
    # Load the vector store
    embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embeddings,
    )

    # Load the prompt
    prompt = config.load_prompt()

    # Create the RAG chain
    #llm = Ollama(model=config.OLLAMA_MODEL)
    llm = OllamaLLM(model=config.OLLAMA_MODEL)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS}),
    )

    # Run the query
    result = qa_chain.run(prompt)
    print("Answer:")
    print(result)

if __name__ == "__main__":
    main()
```

- **`config.py`**: 

Configuration file for models, paths, and chunking settings

```bash
"""
config.py — Shared configuration for the local RAG pipeline.
All scripts import from here. Edit this file to change models,
paths, chunking, or retrieval settings.
"""

import os
import re
import sys

# Models
OLLAMA_MODEL    = "gemma4:latest"   # LLM used for answering
EMBEDDING_MODEL = "nomic-embed-text"   # Embedding model (can differ from OLLAMA_MODEL)

# Vector store
CHROMA_DB_PATH = "./aurelsystems" # Path to the vector store

# Chunking
CHUNK_SIZE    = 500 # Number of characters per chunk
CHUNK_OVERLAP = 50  # Number of characters to overlap between chunks

# Retrieval
TOP_K_RESULTS = 5 # Number of chunks to retrieve

# Input files
FOLDERS_FILE = "folders.txt"   # one folder path per line
PROMPT_FILE  = "prompt.txt"    # the question / prompt to ask

# Path helpers

def _win_to_wsl(path: str) -> str:
    """
    Convert a Windows-style path to a WSL path.

    Examples
    --------
    C:\\Users\\User\\docs  →  /mnt/c/Users/User/docs
    D:/Projects/reports   →  /mnt/d/Projects/reports
    /home/user/docs      →  (unchanged)
    ./relative            →  (unchanged)
    """
    path = path.strip()
    # Match   C:\...  or  C:/...
    m = re.match(r'^([A-Za-z]):[/\\](.*)$', path)
    if m:
        drive  = m.group(1).lower()
        rest   = m.group(2).replace('\\', '/')
        return f"/mnt/{drive}/{rest}"
    # Already Unix-style (absolute or relative)
    return path.replace('\\', '/')


def load_folders(filepath: str = FOLDERS_FILE) -> list[str]:
    """
    Read folder paths from *filepath*, one per line.

    • Blank lines and lines starting with '#' are ignored.
    • Windows paths (e.g. C:\\Docs) are converted to WSL paths automatically.
    • Trailing slashes are normalised.
    """
    if not os.path.exists(filepath):
        print(f"[config] ERROR: folders file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    folders = []
    with open(filepath, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            unix_path = _win_to_wsl(line)
            # Ensure trailing slash so DirectoryLoader scans the folder
            if not unix_path.endswith("/"):
                unix_path += "/"
            folders.append(unix_path)

    if not folders:
        print(f"[config] ERROR: no folders found in {filepath}", file=sys.stderr)
        sys.exit(1)

    return folders


def load_prompt(filepath: str = PROMPT_FILE) -> str:
    """Read the prompt/question from *filepath* (entire file content, stripped)."""
    if not os.path.exists(filepath):
        print(f"[config] ERROR: prompt file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, encoding="utf-8") as fh:
        return fh.read().strip()

```
