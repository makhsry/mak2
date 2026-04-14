### Local RAG Pipeline — Ollama + ChromaDB + LangChain

This doc describes how to use the `local RAG` pipeline with `Ollama`, `ChromaDB`, and `LangChain`. 

- To **access** scripts [**click here**](Outlets_99999981_localRAG.zip).

#### Workflow reference

| Task | Command |
| :--- | :--- |
| First-time setup database (from folder: `folders.txt`) | `python index.py` |
| Ask a question (from file: `prompt.txt`) | `python prompt.py` |
| Ask on command line | `python prompt.py -q "..."` |
| Interactive chat | `python prompt.py --interactive` |
| Add new documents (update database) | `python update.py` |
| Full rebuild | `python update.py --mode reconstruct` |
| Default question read by `prompt.py` | `prompt.txt` |
| List of document folders to index | `folders.txt` |
| Shared settings (models, paths, chunking). **Edit here.** | `config.py` |

#### Getting Started

```bash
# 1. Install dependencies
pip install langchain langchain-community chromadb ollama pypdf unstructured python-docx

# 2. Edit folders.txt  ← add your document folders (Windows or Unix paths)
# 3. Edit prompt.txt   ← put your question there

# 4. Build the vector store
python index.py

# 5. Ask a question (reads from prompt.txt)
python prompt.py

# 5b. Ask directly on the command line
python prompt.py --question "What is the annual leave policy?"

# 5c. Start an interactive chat loop
python prompt.py --interactive
```

#### `folders.txt` format

Windows and Unix paths are both accepted:

```
# Lines starting with '#' are comments and are ignored.

C:\Users\User\Documents\
D:/Projects/reports
/home/alice/hr_docs
./documents/legal
```

#### Updating the vector store

```bash
# Add only NEW documents (fast — skips already-indexed files)
python update.py
python update.py --mode update            # same thing

# Wipe and rebuild everything from scratch
python update.py --mode reconstruct

# Use a different folders file
python update.py --folders other_folders.txt
```

#### Changing models or settings

Open `config.py` and edit the values at the top:

```python
OLLAMA_MODEL    = "qwen3:4b"   # LLM for answering
EMBEDDING_MODEL = "qwen3:4b"   # Embedding model
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
TOP_K_RESULTS   = 5
```

After changing `EMBEDDING_MODEL` or chunking settings, run:

```bash
python update.py --mode reconstruct
```