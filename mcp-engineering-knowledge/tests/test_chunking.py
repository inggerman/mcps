"""Tests for the markdown chunker."""

from mcp_engineering_knowledge.chunking import chunk_markdown


def test_simple_chunk():
    """A short markdown file produces one chunk."""
    content = "# Title\n\nShort content."
    chunks = chunk_markdown(content, "test.md")
    assert len(chunks) >= 1
    assert "Short content" in chunks[0].text


def test_frontmatter_extraction():
    """Frontmatter is extracted into metadata."""
    content = """---
title: "Test Doc"
type: standard
tags: [test]
---

# Header

Content here."""
    chunks = chunk_markdown(content, "test.md")
    assert len(chunks) >= 1
    assert chunks[0].metadata["title"] == "Test Doc"
    assert chunks[0].metadata["type"] == "standard"


def test_multiple_sections():
    """Multiple H2 headers produce multiple chunks."""
    content = """# Main

## Section A

Content A.

## Section B

Content B."""
    chunks = chunk_markdown(content, "test.md")
    # At least 2 chunks (one per section)
    sections = [c.metadata["section"] for c in chunks]
    assert "Section A" in sections
    assert "Section B" in sections


def test_long_section_split():
    """A section longer than chunk_size gets split."""
    content = """## Long Section

"""
    # Add enough text to exceed chunk_size (800 tokens ~ 3200 chars)
    content += "Lorem ipsum " * 500
    chunks = chunk_markdown(content, "test.md", chunk_size=100, overlap=20)
    assert len(chunks) > 1


def test_empty_content():
    """Empty content produces no chunks."""
    chunks = chunk_markdown("", "empty.md")
    assert len(chunks) == 0


def test_chunk_metadata_has_file_path():
    """Each chunk carries the file_path in metadata."""
    content = "# Title\n\nContent."
    chunks = chunk_markdown(content, "path/to/file.md")
    for chunk in chunks:
        assert chunk.metadata["file_path"] == "path/to/file.md"
