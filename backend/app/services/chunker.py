"""
Chunking service.

We use a Markdown-aware recursive splitter: it tries to split on
headers and paragraph boundaries first, falling back to sentences,
then words, only if a section is still too large. This avoids cutting
a financial statement or bullet point in half, which plain
fixed-length chunking tends to do.
"""
from dataclasses import dataclass

from langchain_text_splitters import MarkdownTextSplitter


@dataclass
class Chunk:
    text: str
    chunk_index: int


def chunk_markdown(markdown_text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> list[Chunk]:
    """Split Markdown into overlapping chunks suitable for embedding.

    chunk_size / chunk_overlap are in characters. 800/120 is a
    reasonable starting point for dense financial prose — small enough
    that retrieval stays precise, with enough overlap that a fact
    split across a chunk boundary isn't lost entirely.
    """
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    raw_chunks = splitter.split_text(markdown_text)

    # Drop near-empty chunks (e.g., page headers/footers that survived conversion)
    cleaned = [c.strip() for c in raw_chunks if len(c.strip()) > 30]

    return [Chunk(text=text, chunk_index=i) for i, text in enumerate(cleaned)]
