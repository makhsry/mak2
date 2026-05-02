"""
rag.py — Unified RAG Pipeline Script
Consolidates database building and querying into a single CLI tool.

Usage:
  python rag.py --task=build-db   --source-dir=PATH --database-dir=PATH --embedder=MODEL [--size=small|medium|large]
  python rag.py --task=append-db  --source-dir=PATH --database-dir=PATH --embedder=MODEL [--size=small|medium|large]
  python rag.py --task=query      --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --question="..."
  python rag.py --task=query      --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --interactive
  python rag.py --task=query      --database-dir=PATH --embedder=MODEL --ollama-llm=MODEL --prompt-file=FILE
"""

import argparse
import os
import shutil
import sys
import uuid

# Chunk size presets

SIZE_PRESETS = {
    # chunk_size is in characters. bge-large has a 512-token limit (~380 chars
    # of English text on average). These presets stay safely under that ceiling.
    "small":  {"chunk_size": 300, "chunk_overlap": 30, "top_k": 6},
    "medium": {"chunk_size": 380, "chunk_overlap": 40, "top_k": 10},
    "large":  {"chunk_size": 500, "chunk_overlap": 60, "top_k": 14},
}

# Hard character ceiling applied before embedding — catches edge cases like
# dense code or tables where 1 char can represent >1 token.
EMBED_CHAR_LIMIT = 1400  # ~512 tokens with a comfortable safety margin

# Lazy imports (only pulled in when needed)

def _import_db_deps():
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        BSHTMLLoader,
        UnstructuredWordDocumentLoader,   # .docx / .doc
        UnstructuredExcelLoader,          # .xlsx / .xls
        UnstructuredPowerPointLoader,     # .pptx / .ppt
        CSVLoader,                        # .csv
        UnstructuredMarkdownLoader,       # .md
        JSONLoader,                       # .json / .jsonl
        UnstructuredXMLLoader,            # .xml
        UnstructuredEmailLoader,          # .eml
        OutlookMessageLoader,             # .msg
    )
    from langchain_unstructured import UnstructuredLoader
    from tqdm import tqdm
    return (
        Document, 
        RecursiveCharacterTextSplitter, 
        Chroma,
        OllamaEmbeddings,
        PyPDFLoader, 
        TextLoader, 
        BSHTMLLoader,
        UnstructuredWordDocumentLoader, 
        UnstructuredExcelLoader,
        UnstructuredPowerPointLoader, 
        CSVLoader,
        UnstructuredMarkdownLoader, 
        JSONLoader,
        UnstructuredXMLLoader, 
        UnstructuredEmailLoader, 
        OutlookMessageLoader,
        UnstructuredLoader, 
        tqdm
    )

def _import_query_deps():
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings, OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    return Chroma, OllamaEmbeddings, OllamaLLM, ChatPromptTemplate, RunnablePassthrough, StrOutputParser

# Database helpers

# Extensions handled by a dedicated loader (everything else → UnstructuredLoader)
SPECIFIC_LOADER_EXTS = {
    ".pdf", ".html", ".htm", ".txt",
    ".docx", ".doc",
    ".xlsx", ".xls",
    ".pptx", ".ppt",
    ".csv",
    ".md",
    ".json", ".jsonl",
    ".xml",
    ".eml", ".msg",
}


def _get_loader(ext, file_path, loaders: dict):
    """
    Return (loader_instance, loader_class_name) for a given file extension.

    Special cases:
      • .jsonl  — JSONLoader with json_lines=True
      • .json   — JSONLoader with jq_schema="." to extract all content
      • everything else falls back to UnstructuredLoader
    """
    UnstructuredLoader = loaders["UnstructuredLoader"]

    if ext == ".json":
        cls = loaders["JSONLoader"]
        return cls(file_path=file_path, jq_schema=".", text_content=False), cls.__name__

    if ext == ".jsonl":
        cls = loaders["JSONLoader"]
        return cls(file_path=file_path, jq_schema=".", text_content=False, json_lines=True), cls.__name__

    mapping = {
        ".pdf":  loaders["PyPDFLoader"],
        ".html": loaders["BSHTMLLoader"],
        ".htm":  loaders["BSHTMLLoader"],
        ".txt":  loaders["TextLoader"],
        ".docx": loaders["UnstructuredWordDocumentLoader"],
        ".doc":  loaders["UnstructuredWordDocumentLoader"],
        ".xlsx": loaders["UnstructuredExcelLoader"],
        ".xls":  loaders["UnstructuredExcelLoader"],
        ".pptx": loaders["UnstructuredPowerPointLoader"],
        ".ppt":  loaders["UnstructuredPowerPointLoader"],
        ".csv":  loaders["CSVLoader"],
        ".md":   loaders["UnstructuredMarkdownLoader"],
        ".xml":  loaders["UnstructuredXMLLoader"],
        ".eml":  loaders["UnstructuredEmailLoader"],
        ".msg":  loaders["OutlookMessageLoader"],
    }

    cls = mapping.get(ext, UnstructuredLoader)
    return cls(file_path), cls.__name__


def _build_loaders_dict(deps: tuple) -> dict:
    """Map loader names to classes from the _import_db_deps() tuple."""
    (
        Document, RecursiveCharacterTextSplitter, Chroma,
        OllamaEmbeddings,
        PyPDFLoader, TextLoader, BSHTMLLoader,
        UnstructuredWordDocumentLoader, UnstructuredExcelLoader,
        UnstructuredPowerPointLoader, CSVLoader,
        UnstructuredMarkdownLoader, JSONLoader,
        UnstructuredXMLLoader, UnstructuredEmailLoader, OutlookMessageLoader,
        UnstructuredLoader, tqdm
    ) = deps
    return {
        "PyPDFLoader":                    PyPDFLoader,
        "TextLoader":                     TextLoader,
        "BSHTMLLoader":                   BSHTMLLoader,
        "UnstructuredWordDocumentLoader": UnstructuredWordDocumentLoader,
        "UnstructuredExcelLoader":        UnstructuredExcelLoader,
        "UnstructuredPowerPointLoader":   UnstructuredPowerPointLoader,
        "CSVLoader":                      CSVLoader,
        "UnstructuredMarkdownLoader":     UnstructuredMarkdownLoader,
        "JSONLoader":                     JSONLoader,
        "UnstructuredXMLLoader":          UnstructuredXMLLoader,
        "UnstructuredEmailLoader":        UnstructuredEmailLoader,
        "OutlookMessageLoader":           OutlookMessageLoader,
        "UnstructuredLoader":             UnstructuredLoader,
    }


def load_folder(folder_path: str, indexed_sources: set, append_mode: bool, loaders: dict, tqdm) -> list:
    """Walk a folder, load each file, skip already-indexed ones in append mode."""
    docs = []
    folder_path = os.path.abspath(folder_path)
    error_dir = os.path.join(folder_path, ".not_indexed")

    files_to_process = []
    for root, dirs, files in os.walk(folder_path):
        if ".not_indexed" in root:
            continue
        for filename in files:
            files_to_process.append(os.path.join(root, filename))

    for file_path in tqdm(files_to_process, desc=f"Scanning {os.path.basename(folder_path)}", unit="file"):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        if append_mode and file_path in indexed_sources:
            tqdm.write(f"  [Skip] Already indexed: {filename}")
            continue

        loader, loader_name = _get_loader(ext, file_path, loaders)

        try:
            tqdm.write(f"  [Process] Loading: {filename} ({loader_name})")
            docs.extend(loader.load())
        except Exception as exc:
            tqdm.write(f"  [!! Error] Failed to read {filename}: {exc}")
            os.makedirs(error_dir, exist_ok=True)
            try:
                dest = os.path.join(error_dir, filename)
                if os.path.exists(dest):
                    dest = f"{dest}_{uuid.uuid4().hex[:4]}"
                shutil.move(file_path, dest)
                tqdm.write(f"  [Moved] {filename} -> .not_indexed/")
            except Exception as move_exc:
                tqdm.write(f"  [Critical] Could not move file: {move_exc}")

    return docs


def task_build_db(args, preset):
    """Wipe and rebuild the vector database from scratch."""
    deps = _import_db_deps()
    (Document, RecursiveCharacterTextSplitter, Chroma, OllamaEmbeddings, *_, tqdm) = deps
    loaders = _build_loaders_dict(deps)

    source_dir   = os.path.abspath(args.source_dir)
    database_dir = os.path.abspath(args.database_dir)

    if not os.path.isdir(source_dir):
        print(f"[error] Source directory not found: {source_dir}")
        sys.exit(1)

    # Wipe existing DB
    if os.path.exists(database_dir):
        print(f"[db] Wiping existing database at: {database_dir}")
        shutil.rmtree(database_dir)

    embeddings = OllamaEmbeddings(model=args.embedder)

    print(f"[db] Scanning source: {source_dir}")
    docs = load_folder(source_dir, set(), append_mode=False, loaders=loaders, tqdm=tqdm)

    if not docs:
        print("[db] No documents found. Nothing to index.")
        return

    _embed_and_store(docs, embeddings, database_dir, preset, Chroma, RecursiveCharacterTextSplitter, tqdm, rebuild=True)


def task_append_db(args, preset):
    """Add only new files to an existing vector database."""
    deps = _import_db_deps()
    (Document, RecursiveCharacterTextSplitter, Chroma, OllamaEmbeddings, *_, tqdm) = deps
    loaders = _build_loaders_dict(deps)

    source_dir   = os.path.abspath(args.source_dir)
    database_dir = os.path.abspath(args.database_dir)

    if not os.path.isdir(source_dir):
        print(f"[error] Source directory not found: {source_dir}")
        sys.exit(1)

    embeddings      = OllamaEmbeddings(model=args.embedder)
    indexed_sources = set()

    if os.path.exists(database_dir):
        vectorstore     = Chroma(persist_directory=database_dir, embedding_function=embeddings)
        existing_data   = vectorstore.get()
        indexed_sources = {m.get("source") for m in existing_data["metadatas"]}
        print(f"[db] Append mode — {len(indexed_sources)} files already indexed.")
    else:
        print("[db] No existing database found; creating a new one.")

    print(f"[db] Scanning source: {source_dir}")
    docs = load_folder(source_dir, indexed_sources, append_mode=True, loaders=loaders, tqdm=tqdm)

    if not docs:
        print("[db] No new documents to index. Database is up to date.")
        return

    _embed_and_store(docs, embeddings, database_dir, preset, Chroma, RecursiveCharacterTextSplitter, tqdm, rebuild=False)



def _embed_and_store(docs, embeddings, database_dir, preset, Chroma, Splitter, tqdm, rebuild: bool):
    """Shared chunking + embedding logic."""
    chunk_size    = preset["chunk_size"]
    chunk_overlap = preset["chunk_overlap"]
    batch_size    = 50

    print(f"[db] Splitting {len(docs)} documents (chunk_size={chunk_size}, overlap={chunk_overlap})…")
    splitter = Splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks   = splitter.split_documents(docs)

    # Truncate any chunk whose text exceeds the embedding model's token limit.
    # bge-large (and most sentence-transformers) cap at 512 tokens. Dense content
    # like code or tables can produce chunks where 1 char > 1 token, so we apply
    # a hard character ceiling as a safety net even after the splitter runs.
    truncated = 0
    for chunk in chunks:
        if len(chunk.page_content) > EMBED_CHAR_LIMIT:
            chunk.page_content = chunk.page_content[:EMBED_CHAR_LIMIT]
            truncated += 1
    if truncated:
        print(f"[db] WARNING: Truncated {truncated} oversized chunk(s) to {EMBED_CHAR_LIMIT} chars.")

    print(f"[db] Embedding {len(chunks)} chunks…")

    if rebuild or not os.path.exists(database_dir):
        vectorstore = Chroma.from_documents(
            documents=chunks[:batch_size],
            embedding=embeddings,
            persist_directory=database_dir,
        )
        start_idx = batch_size
    else:
        vectorstore = Chroma(persist_directory=database_dir, embedding_function=embeddings)
        start_idx   = 0

    for i in tqdm(range(start_idx, len(chunks), batch_size), desc="Indexing chunks", unit="batch"):
        vectorstore.add_documents(chunks[i : i + batch_size])

    print(f"[db] ✓ Done. {len(chunks)} chunks stored in: {database_dir}")


# Query helpers

def build_rag_chain(database_dir, embedder, llm_model, top_k):
    """Construct and return an LCEL RAG chain."""
    Chroma, OllamaEmbeddings, OllamaLLM, ChatPromptTemplate, RunnablePassthrough, StrOutputParser = _import_query_deps()

    if not os.path.exists(database_dir):
        print(f"[error] Database not found at: {database_dir}")
        print("[error] Run --task=build-db first.")
        sys.exit(1)

    embeddings  = OllamaEmbeddings(model=embedder)
    vectorstore = Chroma(persist_directory=database_dir, embedding_function=embeddings)
    retriever   = vectorstore.as_retriever(search_kwargs={"k": top_k})
    llm         = OllamaLLM(model=llm_model)

    template = (
        "Answer the question based only on the following context:\n"
        "{context}\n\n"
        "Question: {question}"
    )
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def task_query(args, preset):
    """Run a query against the vector database."""
    database_dir = os.path.abspath(args.database_dir)
    top_k        = preset["top_k"]

    if not args.ollama_llm:
        print("[error] --ollama-llm is required for --task=query")
        sys.exit(1)

    chain = build_rag_chain(database_dir, args.embedder, args.ollama_llm, top_k)

    # Modes

    if args.question:
        print(f"[query] Question: {args.question}")
        response = chain.invoke(args.question)
        print(f"\n--- ANSWER ---\n{response}")

    elif args.prompt_file:
        if not os.path.exists(args.prompt_file):
            print(f"[error] Prompt file not found: {args.prompt_file}")
            sys.exit(1)
        with open(args.prompt_file, encoding="utf-8") as fh:
            user_prompt = fh.read().strip()
        print(f"[query] Running prompt from: {args.prompt_file}")
        response = chain.invoke(user_prompt)
        print(f"\n--- ANSWER ---\n{response}")

    elif args.interactive:
        print("\n--- INTERACTIVE MODE ---")
        print("Type 'exit' or 'quit' to end.\n")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                continue
            print("Thinking…")
            response = chain.invoke(user_input)
            print(f"AI: {response}\n")

    else:
        print("[error] Provide --question, --prompt-file, or --interactive for query mode.")
        sys.exit(1)


# CLI

def parse_args():
    parser = argparse.ArgumentParser(
        prog="rag.py",
        description="Unified RAG Pipeline — build a vector DB and query it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build database from scratch
  python rag.py --task=build-db --source-dir=./docs --database-dir=./db --embedder=bge-large:latest --size=medium

  # Append new files to existing database
  python rag.py --task=append-db --source-dir=./docs --database-dir=./db --embedder=bge-large:latest

  # Ask a single question
  python rag.py --task=query --database-dir=./db --embedder=bge-large:latest --ollama-llm=qwen3:4b --question="What is X?"

  # Interactive chat
  python rag.py --task=query --database-dir=./db --embedder=bge-large:latest --ollama-llm=qwen3:4b --interactive

  # Run from a prompt file
  python rag.py --task=query --database-dir=./db --embedder=bge-large:latest --ollama-llm=qwen3:4b --prompt-file=prompt.txt

  # Override individual preset values (can be combined with --size)
  python rag.py --task=build-db --source-dir=./docs --database-dir=./db --embedder=bge-large:latest --chunk-size=450 --chunk-overlap=50
  python rag.py --task=query    --database-dir=./db  --embedder=bge-large:latest --ollama-llm=qwen3:4b --question="..." --top-k=4
        """,
    )

    # Required
    parser.add_argument(
        "--task",
        required=True,
        choices=["build-db", "append-db", "query"],
        metavar="TASK",
        help="Task to run: build-db | append-db | query",
    )
    parser.add_argument(
        "--database-dir",
        required=True,
        metavar="PATH",
        help="Directory for the ChromaDB vector store.",
    )
    parser.add_argument(
        "--embedder",
        required=True,
        metavar="MODEL",
        help="Ollama embedding model name (e.g. bge-large:latest).",
    )

    # DB-only
    parser.add_argument(
        "--source-dir",
        metavar="PATH",
        help="[build-db / append-db] Directory of documents to index.",
    )
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large"],
        default="medium",
        help="[build-db / append-db / query] Named chunking preset (default: medium). "
             "Individual --chunk-size / --chunk-overlap / --top-k override this.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        metavar="N",
        dest="chunk_size",
        help="[build-db / append-db] Characters per chunk. Overrides --size.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        metavar="N",
        dest="chunk_overlap",
        help="[build-db / append-db] Overlap characters between chunks. Overrides --size.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        metavar="N",
        dest="top_k",
        help="[build-db / append-db / query] Number of chunks retrieved per query. Overrides --size.",
    )

    # Query-only
    parser.add_argument(
        "--ollama-llm",
        metavar="MODEL",
        dest="ollama_llm",
        help="[query] Ollama LLM model name (e.g. qwen3:4b).",
    )
    parser.add_argument(
        "--question",
        metavar="TEXT",
        help="[query] A single question to answer.",
    )
    parser.add_argument(
        "--prompt-file",
        metavar="FILE",
        help="[query] Path to a text file containing the prompt.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="[query] Start an interactive chat session.",
    )

    return parser.parse_args()


def validate_args(args):
    """Catch common mistakes early with clear messages."""
    if args.task in ("build-db", "append-db") and not args.source_dir:
        print(f"[error] --source-dir is required for --task={args.task}")
        sys.exit(1)

    if args.task == "query":
        modes = sum([bool(args.question), bool(args.prompt_file), args.interactive])
        if modes == 0:
            print("[error] Provide one of --question, --prompt-file, or --interactive for query mode.")
            sys.exit(1)
        if modes > 1:
            print("[error] Use only one of --question, --prompt-file, or --interactive.")
            sys.exit(1)
        if not args.ollama_llm:
            print("[error] --ollama-llm is required for --task=query")
            sys.exit(1)


# Entry point

def main():
    args   = parse_args()
    validate_args(args)

    # Start from the named preset, then apply any individual overrides.
    preset = dict(SIZE_PRESETS[args.size or "large"])
    if args.chunk_size    is not None: preset["chunk_size"]    = args.chunk_size
    if args.chunk_overlap is not None: preset["chunk_overlap"] = args.chunk_overlap
    if args.top_k         is not None: preset["top_k"]         = args.top_k

    print(f"[rag] Preset: chunk_size={preset['chunk_size']}  "
          f"chunk_overlap={preset['chunk_overlap']}  top_k={preset['top_k']}")

    if args.task == "build-db":
        task_build_db(args, preset)
    elif args.task == "append-db":
        task_append_db(args, preset)
    elif args.task == "query":
        task_query(args, preset)


if __name__ == "__main__":
    main()
