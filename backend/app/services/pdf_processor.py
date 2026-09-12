"""
PDF -> Markdown conversion.

We convert to Markdown before chunking (rather than chunking raw
extracted text) because Markdown preserves structural signals —
headings, tables, lists — that make semantic chunking far more
reliable on financial reports, which are heavily sectioned.
"""
import hashlib
from pathlib import Path

import pymupdf4llm


def compute_content_hash(file_bytes: bytes) -> str:
    """SHA-256 hash of raw file bytes — used for ingestion idempotency.
    Re-uploading the same PDF produces the same hash, so we can detect
    and skip duplicate ingestion instead of silently re-processing."""
    return hashlib.sha256(file_bytes).hexdigest()


def pdf_to_markdown(pdf_path: str | Path) -> str:
    """Convert a PDF file on disk to a single Markdown string."""
    return pymupdf4llm.to_markdown(str(pdf_path))
