"""Ingest runbook markdown files into a persistent Chroma vector store."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBED_MODEL,
    OLLAMA_BASE_URL,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "runbooks"
MANIFEST_FILE = "ingest_manifest.json"


def _load_markdown_files() -> list:
    """Load all markdown runbooks from DATA_DIR."""
    paths = sorted(DATA_DIR.glob("**/*.md"))
    if not paths:
        raise FileNotFoundError(f"No markdown files found in {DATA_DIR}")

    documents = []
    for path in paths:
        try:
            loader = TextLoader(str(path), encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = str(path.relative_to(DATA_DIR))
            documents.extend(docs)
        except OSError as exc:
            logger.error("Failed to load %s: %s", path, exc)
            raise

    return documents


def _chunk_documents(documents: list):
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def _compute_fingerprint() -> str:
    """Hash runbook paths and contents to detect changes."""
    hasher = hashlib.sha256()
    for path in sorted(DATA_DIR.glob("**/*.md")):
        hasher.update(str(path.relative_to(DATA_DIR)).encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _manifest_path() -> Path:
    return CHROMA_DIR / MANIFEST_FILE


def _read_manifest() -> dict | None:
    path = _manifest_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read ingest manifest: %s", exc)
        return None


def _write_manifest(fingerprint: str, vector_count: int) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"fingerprint": fingerprint, "vector_count": vector_count}
    _manifest_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _is_already_ingested(fingerprint: str) -> bool:
    """Return True when the vector store matches the current runbooks."""
    manifest = _read_manifest()
    if manifest is None or manifest.get("fingerprint") != fingerprint:
        return False
    if manifest.get("vector_count", 0) <= 0:
        return False
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def _clear_vector_store() -> None:
    """Remove an existing Chroma store before re-ingesting."""
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)


def ingest_runbooks(*, force: bool = False) -> None:
    """
    Load runbooks, embed them with Ollama, and persist vectors in Chroma.

    Safe to run multiple times: skips work when runbook content is unchanged.
    Pass force=True to rebuild the vector store even when nothing changed.
    """
    fingerprint = _compute_fingerprint()

    if not force and _is_already_ingested(fingerprint):
        manifest = _read_manifest()
        vector_count = manifest.get("vector_count", 0) if manifest else 0
        file_count = len(list(DATA_DIR.glob("**/*.md")))
        print(
            f"Ingestion skipped (already up to date): "
            f"{file_count} files, {vector_count} vectors in store"
        )
        return

    if force or _read_manifest() is not None:
        _clear_vector_store()

    try:
        documents = _load_markdown_files()
        file_count = len({doc.metadata.get("source") for doc in documents})

        chunks = _chunk_documents(documents)
        chunk_count = len(chunks)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=str(CHROMA_DIR),
        )

        _write_manifest(fingerprint, chunk_count)

        print(
            f"Ingestion complete: {file_count} files loaded, "
            f"{chunk_count} chunks created, {chunk_count} vectors stored"
        )
    except Exception as exc:
        logger.exception("Ingestion failed")
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR, ignore_errors=True)
        raise RuntimeError(f"Runbook ingestion failed: {exc}") from exc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_runbooks()
