"""Markdown chunker — splits docs by headers for semantic indexing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A chunk of a markdown document."""

    text: str
    metadata: dict = field(default_factory=dict)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def _extract_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and return (metadata, body)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_text = parts[1].strip()
    body = parts[2]
    metadata: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata, body


def chunk_markdown(
    content: str,
    file_path: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[Chunk]:
    """Split a markdown file into chunks by H2/H3 headers.

    Each chunk carries metadata: file_path, section (header hierarchy),
    title (from frontmatter or first H1), and type (from frontmatter).
    """
    fm, body = _extract_frontmatter(content)
    title = fm.get("title", "")
    doc_type = fm.get("type", "")
    tags = fm.get("tags", "")

    # Split by headers (## or ###)
    header_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    sections: list[tuple[str, str]] = []  # (header_path, content)
    current_header = ""
    current_content: list[str] = []
    current_level = 0

    for line in body.splitlines(keepends=True):
        match = header_pattern.match(line)
        if match:
            level = len(match.group(1))
            header_text = match.group(2).strip()
            if current_content or current_header:
                sections.append((current_header, "".join(current_content)))
            current_header = header_text
            current_content = [line]
            current_level = level
        else:
            current_content.append(line)

    if current_content:
        sections.append((current_header, "".join(current_content)))

    # Build chunks, splitting long sections further
    chunks: list[Chunk] = []
    for header, section_content in sections:
        if not section_content.strip():
            continue

        tokens = _estimate_tokens(section_content)
        if tokens <= chunk_size:
            chunks.append(
                Chunk(
                    text=section_content.strip(),
                    metadata={
                        "file_path": file_path,
                        "section": header,
                        "title": title,
                        "type": doc_type,
                        "tags": tags,
                    },
                )
            )
        else:
            # Split by paragraphs
            paragraphs = re.split(r"\n\n+", section_content)
            current: list[str] = []
            current_tokens = 0
            for para in paragraphs:
                para_tokens = _estimate_tokens(para)
                if current_tokens + para_tokens > chunk_size and current:
                    chunks.append(
                        Chunk(
                            text="\n\n".join(current).strip(),
                            metadata={
                                "file_path": file_path,
                                "section": header,
                                "title": title,
                                "type": doc_type,
                                "tags": tags,
                            },
                        )
                    )
                    # Keep overlap: last paragraph
                    if overlap > 0 and current:
                        current = [current[-1]]
                        current_tokens = _estimate_tokens(current[-1])
                    else:
                        current = []
                        current_tokens = 0
                current.append(para)
                current_tokens += para_tokens
            if current:
                chunks.append(
                    Chunk(
                        text="\n\n".join(current).strip(),
                        metadata={
                            "file_path": file_path,
                            "section": header,
                            "title": title,
                            "type": doc_type,
                            "tags": tags,
                        },
                    )
                )

    return chunks
