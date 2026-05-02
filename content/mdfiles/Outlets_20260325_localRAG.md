### Local RAG Pipeline — Ollama + ChromaDB + LangChain
 
This is a **`local RAG`** pipeline using `Ollama`, `ChromaDB`, and `LangChain`. 

- **Access** source code from [**here**](tools/local_RAG.py).

**Workflow reference**
 
- You must have **`Ollama`** installed and have **`pulled`** the required models (**`embedding`** and **`LLM`**) (for example: `ollama pull gemma4:latest`) for the scripts to work.
- Before running any script, **`Ollama`** must be running in the background: **`ollama serve`**.
- Use **`--help`** to see all available options for each script.

**Steps to prepare the WSL environment**
 
- Update and upgrade: `sudo apt update && sudo apt upgrade -y` 
- Install dependencies: `sudo apt install -y build-essential python3-pip python3-venv curl git libmagic-dev poppler-utils tesseract-ocr`.
- Create a python virtual environment: `python3 -m venv venv` 
- Activate it: `source venv/bin/activate`. 
- Install pip packages: `pip install -r requirements.txt`.
- Install Ollama: `https://ollama.com/download` or `curl -fsSL https://ollama.com/install.sh | sh`.
- Pull the required model: `ollama pull gemma4:latest` and `ollama pull nomic-embed-text`.

**Required packages** (`requirements.txt`): 
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

**Usage Examples**
```bash 
# Build a new database
python rag.py --task=build-db --source-dir=PATH --database-dir=PATH --embedder=MODEL [--size=small|medium|large]
# Append to existing database
python rag.py --task=append-db --source-dir=PATH --database-dir=PATH --embedder=MODEL [--size=small|medium|large]
# Query the database
python rag.py --task=query --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --question="..."
# Interactive query
python rag.py --task=query --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --interactive
# Query with prompt file
python rag.py --task=query --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --prompt-file=FILE
```