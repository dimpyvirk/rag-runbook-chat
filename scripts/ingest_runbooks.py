"""Standalone script to ingest runbooks into the vector store."""

import sys
from pathlib import Path

# Add parent directory to path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import ingest_runbooks

if __name__ == "__main__":
    try:
        ingest_runbooks()
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)