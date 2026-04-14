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
from langchain_community.document_loaders import PyPDFLoader, TextLoader, BSHTMLLoader
from langchain_unstructured import UnstructuredLoader

import config
from tqdm import tqdm

# Priority mapping for loaders
SPECIFIC_LOADERS = {
    ".pdf": PyPDFLoader,
    ".html": BSHTMLLoader,
    ".htm": BSHTMLLoader,
    ".txt": TextLoader,
}

# Document loading

def load_folder(folder_path: str, indexed_sources: set, append_mode: bool) -> list[Document]:
    """Smartly loads files, reports actions via tqdm.write, and isolates failures."""
    docs: list[Document] = []
    folder_path = os.path.abspath(folder_path)
    error_dir = os.path.join(folder_path, ".not_indexed")

    # Gather all files first for accurate progress
    files_to_process = []
    for root, dirs, files in os.walk(folder_path):
        if ".not_indexed" in root:
            continue
        for filename in files:
            files_to_process.append(os.path.join(root, filename))

    # tqdm.write() ensures "echoing" doesn't break the progress bar
    for file_path in tqdm(files_to_process, desc=f"Scanning {os.path.basename(folder_path)}", unit="file"):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        if append_mode and file_path in indexed_sources:
            tqdm.write(f"  [Skip] Already indexed: {filename}")
            continue

        loader_cls = SPECIFIC_LOADERS.get(ext, UnstructuredLoader)
        
        try:
            tqdm.write(f"  [Process] Loading: {filename} ({loader_cls.__name__})")
            loader = loader_cls(file_path)
            docs.extend(loader.load())
        except Exception as exc:
            tqdm.write(f"  [!! Error] Failed to read {filename}: {exc}")
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
            try:
                dest = os.path.join(error_dir, filename)
                if os.path.exists(dest):
                    dest = f"{dest}_{uuid.uuid4().hex[:4]}"
                shutil.move(file_path, dest)
                tqdm.write(f"  [Moved] {filename} -> .not_indexed/")
            except Exception as move_exc:
                tqdm.write(f"  [Critical] Could not move file: {move_exc}")
    return docs

# Main Logic

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Vector Database Manager\n\n"
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
        # Keeping the folder header print
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
    
    # Batch processing for the progress bar
    batch_size = 50 
    
    if args.rebuild or not os.path.exists(config.CHROMA_DB_PATH):
        # Initial chunk to create the store
        vectorstore = Chroma.from_documents(
            documents=chunks[:batch_size], 
            embedding=embeddings, 
            persist_directory=config.CHROMA_DB_PATH
        )
        start_idx = batch_size
    else:
        start_idx = 0

    # Indexing Progress Bar
    for i in tqdm(range(start_idx, len(chunks), batch_size), desc="Indexing Chunks", unit="batch"):
        batch = chunks[i : i + batch_size]
        vectorstore.add_documents(batch)
    
    print(f"\n[db] ✓ Success! Added {len(chunks)} new chunks to the vector store.")

if __name__ == "__main__":
    main()
```
 
- **`query.py`**: 
 
Queries the database using the prompt in `prompt.txt` or a custom query.
 
```bash
import argparse
import sys
import os
import config

# Modern Imports matching database.py
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def get_rag_chain():
    """Helper to initialize the RAG chain using LCEL."""
    if not os.path.exists(config.CHROMA_DB_PATH):
        print(f"[error] Database not found at {config.CHROMA_DB_PATH}. Run 'python database.py --rebuild' first.")
        sys.exit(1)

    # Setup Retrieval
    embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS})

    # Setup LLM
    llm = OllamaLLM(model=config.OLLAMA_MODEL)

    # Define the Prompt Template
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    # Create the Chain (LCEL style)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain

def main():
    parser = argparse.ArgumentParser(
        description="RAG Query Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python query.py --file          # Run using prompt.txt\n"
            "  python query.py --question \"...\" # Ask a specific question\n"
            "  python query.py --interactive   # Start a live chat"
        )
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--interactive", action="store_true", help="Start an interactive chat session.")
    group.add_argument("--question", type=str, metavar="STR", help="Ask a single specific question.")
    group.add_argument("--file", action="store_true", help="Use content in prompt.txt.")

    args = parser.parse_args()
    rag_chain = get_rag_chain()

    if args.file:
        user_prompt = config.load_prompt()
        print(f"[query] Running batch prompt from {config.PROMPT_FILE}...")
        response = rag_chain.invoke(user_prompt)
        print(f"\n--- ANSWER ---\n{response}")

    elif args.question:
        print(f"[query] Processing: {args.question}")
        response = rag_chain.invoke(args.question)
        print(f"\n--- ANSWER ---\n{response}")

    elif args.interactive:
        print("\n--- INTERACTIVE MODE ---")
        print("Type 'exit' or 'quit' to end.\n")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input: continue
            
            print("Thinking...")
            response = rag_chain.invoke(user_input)
            print(f"AI: {response}\n")

if __name__ == "__main__":
    main()
```
 
- **`config.py`**: 
 
Configuration file for models, paths, and chunking settings
 
```bash
"""
config.py — Shared configuration for RAG pipeline.
This file manages models, paths, and environment-specific path conversions.
"""

import os
import re
import sys
import argparse

# --- Models ---
OLLAMA_MODEL    = "gemma4:latest"      # LLM used for answering
EMBEDDING_MODEL = "nomic-embed-text"   # Embedding model for vectorization

# --- Vector Store ---
CHROMA_DB_PATH = "./aurelsystems"      # Directory for the Chroma database

# --- Chunking & Retrieval ---
CHUNK_SIZE    = 500                    # Characters per chunk
CHUNK_OVERLAP = 50                     # Overlap between chunks
TOP_K_RESULTS = 5                      # Number of chunks to retrieve per query

# --- Input Files ---
FOLDERS_FILE = "folders.txt"           # File containing paths to scan
PROMPT_FILE  = "prompt.txt"            # File containing the main prompt/question

# --- Path Helpers ---

def _win_to_wsl(path: str) -> str:
    """
    Automatically converts Windows paths to WSL paths.
    C:\\Users\\Docs -> /mnt/c/Users/Docs
    """
    path = path.strip()
    # Match C:\... or C:/...
    m = re.match(r'^([A-Za-z]):[/\\\\](.*)', path)
    if m:
        drive, rest = m.groups()
        rest = rest.replace('\\', '/')
        return f"/mnt/{drive.lower()}/{rest}"
    # If already Unix-style or relative, just fix slashes
    return path.replace('\\', '/')

def load_folders(filepath: str = FOLDERS_FILE) -> list[str]:
    """Reads and normalizes folder paths from the folders file."""
    if not os.path.exists(filepath):
        return []
    
    folders = []
    with open(filepath, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            
            unix_path = _win_to_wsl(line)
            # Ensure the directory exists before adding
            if os.path.isdir(unix_path):
                folders.append(unix_path)
            else:
                print(f"[config] WARNING: Folder not found: {unix_path}")
                
    return folders

def load_prompt(filepath: str = PROMPT_FILE) -> str:
    """Reads the content of the prompt file."""
    if not os.path.exists(filepath):
        return "No prompt found. Please check prompt.txt."
    with open(filepath, encoding="utf-8") as fh:
        return fh.read().strip()

# --- Help & Verification ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Configuration & Path Verifier",
        epilog="Run this script to verify your WSL mount points and model settings."
    )
    # Parse to allow --help but we don't need actual arguments
    _ = parser.parse_known_args()

    print("="*40)
    print("Configuration Check")
    print("="*40)
    print(f"LLM Model:       {OLLAMA_MODEL}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Database Path:   {os.path.abspath(CHROMA_DB_PATH)}")
    
    print("\n--- Folder Path Verification ---")
    active_folders = load_folders()
    if not active_folders:
        print("  [!] No valid folders found. Check your folders.txt file.")
    else:
        for f in active_folders:
            print(f"  [✓] Detected: {f}")
    
    print("\n--- Prompt Preview ---")
    p_content = load_prompt()
    preview = (p_content[:75] + '...') if len(p_content) > 75 else p_content
    print(f"  Content: {preview}")
    print("="*40)
```