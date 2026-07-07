"""Markdown chunking for RAG grounding.

Splits Document Intelligence Markdown into section-aware chunks:
  - a new chunk starts at each Markdown heading (`#`/`##`/`###`),
  - oversized sections are further split on paragraph boundaries with overlap,
  - the document title (H1) is prepended to each chunk for standalone context,
  - page numbers are tracked from DI's `<!-- PageNumber=... -->` / PageBreak markers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ~1000 tokens ≈ 4000 chars; keep a small overlap so facts near a split stay linked.
MAX_CHARS = 4000
OVERLAP_CHARS = 250

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_PAGENUM_RE = re.compile(r"<!--\s*PageNumber=[\"']?(\d+)[\"']?\s*-->", re.IGNORECASE)
_PAGEBREAK_RE = re.compile(r"<!--\s*PageBreak\s*-->", re.IGNORECASE)


@dataclass
class Chunk:
    """A retrievable markdown chunk with provenance."""

    content: str
    section: str
    page: int
    ordinal: int


def _split_oversized(text: str) -> list[str]:
    """Split a too-long block on blank lines, then hard-wrap, keeping overlap."""
    if len(text) <= MAX_CHARS:
        return [text]
    parts: list[str] = []
    buffer = ""
    for para in text.split("\n\n"):
        candidate = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(candidate) <= MAX_CHARS:
            buffer = candidate
            continue
        if buffer:
            parts.append(buffer)
            tail = buffer[-OVERLAP_CHARS:]
            buffer = f"{tail}\n\n{para}".strip()
        else:
            # Single paragraph larger than the cap — hard slice.
            for i in range(0, len(para), MAX_CHARS - OVERLAP_CHARS):
                parts.append(para[i : i + MAX_CHARS])
            buffer = ""
    if buffer:
        parts.append(buffer)
    return parts


def chunk_markdown(markdown: str) -> list[Chunk]:
    """Chunk a markdown document into section-aware, size-capped chunks."""
    lines = markdown.splitlines()
    title = ""
    page = 1

    # Group lines into (heading, page, body) sections.
    sections: list[tuple[str, int, list[str]]] = []
    current_heading = ""
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines or current_heading:
            sections.append((current_heading, page, current_lines.copy()))

    for raw in lines:
        if _PAGEBREAK_RE.search(raw):
            page += 1
            continue
        pm = _PAGENUM_RE.search(raw)
        if pm:
            page = int(pm.group(1))
            continue

        heading = _HEADING_RE.match(raw.strip())
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and not title:
                title = text
            flush()
            current_heading = text
            current_lines = [raw]
        else:
            current_lines.append(raw)
    flush()

    chunks: list[Chunk] = []
    ordinal = 0
    for heading, sec_page, body in sections:
        body_text = "\n".join(body).strip()
        if not body_text:
            continue
        prefix = f"# {title}\n\n" if title and heading != title else ""
        for part in _split_oversized(body_text):
            content = f"{prefix}{part}".strip()
            chunks.append(
                Chunk(
                    content=content,
                    section=heading or title,
                    page=sec_page,
                    ordinal=ordinal,
                )
            )
            ordinal += 1
    return chunks
