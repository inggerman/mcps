"""
Tests para las herramientas del módulo markdown_tools.

Cubre: read_markdown, extract_headings, extract_links, extract_code_blocks,
get_toc, markdown_to_html, markdown_to_plain_text, validate_markdown,
search_in_markdown, format_markdown, get_frontmatter, list_markdown_files.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_markdown.config import settings
from mcp_markdown.tools.markdown_tools import (
    extract_code_blocks,
    extract_headings,
    extract_links,
    format_markdown,
    get_frontmatter,
    get_toc,
    list_markdown_files,
    markdown_to_html,
    markdown_to_plain_text,
    read_markdown,
    search_in_markdown,
    validate_markdown,
)

# ===========================================================================
# read_markdown
# ===========================================================================


class TestReadMarkdown:
    def test_allowed_root_blocks_files_outside_root(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        monkeypatch.setattr(settings, "allowed_root", allowed)

        with pytest.raises(PermissionError, match="directorio permitido"):
            read_markdown(str(outside))

    def test_returns_content(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        assert "content" in result
        assert len(result["content"]) > 0

    def test_extracts_frontmatter(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        fm = result["frontmatter"]
        assert fm["title"] == "Test Document"
        assert fm["author"] == "Test Author"
        assert "python" in fm["tags"]

    def test_extracts_title(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        assert result["title"] == "Hello World"

    def test_word_count_positive(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        assert result["word_count"] > 0

    def test_headings_list(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        headings = result["headings"]
        assert len(headings) >= 3
        levels = [h["level"] for h in headings]
        assert 1 in levels
        assert 2 in levels

    def test_links_list(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        links = result["links"]
        urls = [lnk["url"] for lnk in links]
        assert any("python.org" in u for u in urls)

    def test_code_blocks_list(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        blocks = result["code_blocks"]
        assert len(blocks) >= 1
        languages = [b["language"] for b in blocks]
        assert "python" in languages

    def test_images_list(self, simple_md_file: str) -> None:
        result = read_markdown(simple_md_file)
        images = result["images"]
        assert len(images) >= 1
        assert any("logo.png" in img["url"] for img in images)

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_markdown(str(tmp_path / "missing.md"))

    def test_wrong_extension(self, tmp_path: Path) -> None:
        p = tmp_path / "file.txt"
        p.write_text("hello", encoding="utf-8")
        with pytest.raises(ValueError, match="Extensión"):
            read_markdown(str(p))


# ===========================================================================
# extract_headings
# ===========================================================================


class TestExtractHeadings:
    def test_correct_levels(self, simple_md_file: str) -> None:
        headings = extract_headings(simple_md_file)
        levels = {h["level"] for h in headings}
        assert {1, 2, 3}.issubset(levels)

    def test_text_content(self, simple_md_file: str) -> None:
        headings = extract_headings(simple_md_file)
        texts = [h["text"] for h in headings]
        assert "Hello World" in texts
        assert "Section One" in texts

    def test_anchor_generated(self, simple_md_file: str) -> None:
        headings = extract_headings(simple_md_file)
        for h in headings:
            assert "anchor" in h
            assert isinstance(h["anchor"], str)
            assert len(h["anchor"]) > 0

    def test_anchor_slug_format(self, simple_md_file: str) -> None:
        headings = extract_headings(simple_md_file)
        h1 = next(h for h in headings if h["level"] == 1)
        # "Hello World" → "hello-world"
        assert h1["anchor"] == "hello-world"

    def test_empty_returns_list(self, tmp_path: Path) -> None:
        p = tmp_path / "noheadings.md"
        p.write_text("Just some text without any headings.", encoding="utf-8")
        result = extract_headings(str(p))
        assert result == []


# ===========================================================================
# extract_links
# ===========================================================================


class TestExtractLinks:
    def test_external_link_detected(self, simple_md_file: str) -> None:
        links = extract_links(simple_md_file)
        external = [lnk for lnk in links if lnk.get("is_external")]
        assert len(external) >= 1
        assert any("python.org" in lnk["url"] for lnk in external)

    def test_internal_link_detected(self, simple_md_file: str) -> None:
        links = extract_links(simple_md_file)
        internal = [lnk for lnk in links if not lnk.get("is_external") and not lnk.get("is_image")]
        assert len(internal) >= 1

    def test_image_detected_as_link(self, simple_md_file: str) -> None:
        links = extract_links(simple_md_file)
        images = [lnk for lnk in links if lnk.get("is_image")]
        assert len(images) >= 1

    def test_link_fields(self, simple_md_file: str) -> None:
        links = extract_links(simple_md_file)
        for lnk in links:
            assert "text" in lnk
            assert "url" in lnk
            assert "is_external" in lnk
            assert "is_image" in lnk


# ===========================================================================
# extract_code_blocks
# ===========================================================================


class TestExtractCodeBlocks:
    def test_python_block(self, code_blocks_file: str) -> None:
        blocks = extract_code_blocks(code_blocks_file)
        langs = [b["language"] for b in blocks]
        assert "python" in langs

    def test_javascript_block(self, code_blocks_file: str) -> None:
        blocks = extract_code_blocks(code_blocks_file)
        langs = [b["language"] for b in blocks]
        assert "javascript" in langs

    def test_no_language_block(self, code_blocks_file: str) -> None:
        blocks = extract_code_blocks(code_blocks_file)
        no_lang = [b for b in blocks if b["language"] is None]
        assert len(no_lang) >= 1

    def test_code_content(self, code_blocks_file: str) -> None:
        blocks = extract_code_blocks(code_blocks_file)
        py_block = next(b for b in blocks if b["language"] == "python")
        assert "print" in py_block["code"]

    def test_block_fields(self, code_blocks_file: str) -> None:
        blocks = extract_code_blocks(code_blocks_file)
        for b in blocks:
            assert "language" in b
            assert "code" in b
            assert "line_start" in b


# ===========================================================================
# get_toc
# ===========================================================================


class TestGetToc:
    def test_returns_markdown_list(self, simple_md_file: str) -> None:
        toc = get_toc(simple_md_file)
        assert isinstance(toc, str)
        assert "-" in toc

    def test_contains_heading_texts(self, simple_md_file: str) -> None:
        toc = get_toc(simple_md_file)
        assert "Hello World" in toc
        assert "Section One" in toc

    def test_max_depth_respected(self, simple_md_file: str) -> None:
        toc_shallow = get_toc(simple_md_file, max_depth=1)
        toc_deep = get_toc(simple_md_file, max_depth=3)
        # Depth 1 should have fewer entries
        assert len(toc_shallow.splitlines()) < len(toc_deep.splitlines())

    def test_no_headings(self, tmp_path: Path) -> None:
        p = tmp_path / "noheadings.md"
        p.write_text("Just some text.", encoding="utf-8")
        toc = get_toc(str(p))
        assert "No se encontraron" in toc


# ===========================================================================
# markdown_to_html
# ===========================================================================


class TestMarkdownToHtml:
    def test_returns_html_string(self, simple_md_file: str) -> None:
        html = markdown_to_html(simple_md_file)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_body_content(self, simple_md_file: str) -> None:
        html = markdown_to_html(simple_md_file)
        assert "<h1" in html or "<h2" in html

    def test_code_block_rendered(self, code_blocks_file: str) -> None:
        html = markdown_to_html(code_blocks_file)
        assert "<pre>" in html or "<code>" in html

    def test_direct_text_mode(self) -> None:
        md_text = "# Hello\n\nThis is **bold** text."
        html = markdown_to_html(md_text, is_path=False)
        assert "<h1" in html
        assert "<strong>" in html or "<b>" in html

    def test_has_title_tag(self, simple_md_file: str) -> None:
        html = markdown_to_html(simple_md_file)
        assert "<title>" in html


# ===========================================================================
# markdown_to_plain_text
# ===========================================================================


class TestMarkdownToPlainText:
    def test_removes_headings_markup(self, simple_md_file: str) -> None:
        text = markdown_to_plain_text(simple_md_file)
        assert "# " not in text
        assert "## " not in text

    def test_removes_bold_markup(self, simple_md_file: str) -> None:
        text = markdown_to_plain_text(simple_md_file)
        assert "**" not in text

    def test_keeps_text_content(self, simple_md_file: str) -> None:
        text = markdown_to_plain_text(simple_md_file)
        assert "Hello World" in text

    def test_removes_links_markup(self, simple_md_file: str) -> None:
        text = markdown_to_plain_text(simple_md_file)
        assert "](https://" not in text

    def test_direct_text_mode(self) -> None:
        md = "# Title\n\n**Bold** and _italic_ text with [a link](http://example.com)."
        text = markdown_to_plain_text(md, is_path=False)
        assert "Title" in text
        assert "Bold" in text
        assert "italic" in text
        assert "http://example.com" not in text


# ===========================================================================
# validate_markdown
# ===========================================================================


class TestValidateMarkdown:
    def test_valid_document(self, simple_md_file: str) -> None:
        # simple_md_file has proper H1, unique headings, no broken links
        result = validate_markdown(simple_md_file)
        assert isinstance(result["valid"], bool)
        assert "warnings" in result
        assert "broken_links" in result
        assert "duplicate_headings" in result

    def test_detects_duplicate_headings(self, duplicate_headings_file: str) -> None:
        result = validate_markdown(duplicate_headings_file)
        assert len(result["duplicate_headings"]) > 0
        assert result["valid"] is False

    def test_detects_broken_links(self, broken_links_file: str) -> None:
        result = validate_markdown(broken_links_file)
        broken = result["broken_links"]
        assert len(broken) >= 1
        broken_urls = [b["url"] for b in broken]
        assert any("does_not_exist" in u for u in broken_urls)

    def test_returns_required_fields(self, simple_md_file: str) -> None:
        result = validate_markdown(simple_md_file)
        assert "valid" in result
        assert "warnings" in result
        assert "broken_links" in result
        assert "duplicate_headings" in result

    def test_no_h1_adds_warning(self, tmp_path: Path) -> None:
        p = tmp_path / "noh1.md"
        p.write_text("## Section\n\nContent.", encoding="utf-8")
        result = validate_markdown(str(p))
        assert any("H1" in w for w in result["warnings"])


# ===========================================================================
# search_in_markdown
# ===========================================================================


class TestSearchInMarkdown:
    def test_finds_existing_text(self, simple_md_file: str) -> None:
        results = search_in_markdown(simple_md_file, "simple")
        assert len(results) >= 1

    def test_case_insensitive_default(self, simple_md_file: str) -> None:
        lower = search_in_markdown(simple_md_file, "hello world")
        upper = search_in_markdown(simple_md_file, "HELLO WORLD")
        assert len(lower) == len(upper)

    def test_case_sensitive_mode(self, simple_md_file: str) -> None:
        sensitive = search_in_markdown(simple_md_file, "HELLO WORLD", case_sensitive=True)
        insensitive = search_in_markdown(simple_md_file, "HELLO WORLD", case_sensitive=False)
        assert len(sensitive) <= len(insensitive)

    def test_result_fields(self, simple_md_file: str) -> None:
        results = search_in_markdown(simple_md_file, "content")
        for r in results:
            assert "line_number" in r
            assert "context" in r
            assert "heading_context" in r

    def test_not_found_returns_empty(self, simple_md_file: str) -> None:
        results = search_in_markdown(simple_md_file, "XYZZY_NOT_FOUND_12345")
        assert results == []

    def test_heading_context_populated(self, simple_md_file: str) -> None:
        # "content here" appears under "Section One"
        results = search_in_markdown(simple_md_file, "content here")
        assert len(results) >= 1
        assert results[0]["heading_context"] is not None


# ===========================================================================
# format_markdown
# ===========================================================================


class TestFormatMarkdown:
    def test_returns_string(self, simple_md_file: str) -> None:
        formatted = format_markdown(simple_md_file)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_direct_text_mode(self) -> None:
        messy = "#Title\n\n*  item one\n*  item two\n"
        formatted = format_markdown(messy, is_path=False)
        assert isinstance(formatted, str)
        # mdformat normalizes to "# Title"
        assert "Title" in formatted

    def test_idempotent(self, simple_md_file: str) -> None:
        """Formatear dos veces debe dar el mismo resultado."""
        once = format_markdown(simple_md_file)
        twice = format_markdown(once, is_path=False)
        assert once == twice


# ===========================================================================
# get_frontmatter
# ===========================================================================


class TestGetFrontmatter:
    def test_returns_dict(self, simple_md_file: str) -> None:
        fm = get_frontmatter(simple_md_file)
        assert isinstance(fm, dict)

    def test_correct_values(self, simple_md_file: str) -> None:
        fm = get_frontmatter(simple_md_file)
        assert fm["title"] == "Test Document"
        assert fm["author"] == "Test Author"

    def test_empty_when_no_frontmatter(self, empty_md_file: str) -> None:
        fm = get_frontmatter(empty_md_file)
        assert fm == {}


# ===========================================================================
# list_markdown_files
# ===========================================================================


class TestListMarkdownFiles:
    def test_finds_all_files(self, markdown_directory: str) -> None:
        files = list_markdown_files(markdown_directory)
        # 2 root + 1 nested = 3 total
        assert len(files) >= 3

    def test_excludes_non_markdown(self, markdown_directory: str) -> None:
        files = list_markdown_files(markdown_directory)
        paths = [f["path"] for f in files]
        assert not any(p.endswith(".txt") for p in paths)

    def test_non_recursive_excludes_subdirs(self, markdown_directory: str) -> None:
        files = list_markdown_files(markdown_directory, recursive=False)
        relative_paths = [f["relative_path"] for f in files]
        # No nested paths
        assert not any("\\" in rp or "/" in rp for rp in relative_paths)

    def test_file_fields(self, markdown_directory: str) -> None:
        files = list_markdown_files(markdown_directory)
        for f in files:
            assert "path" in f
            assert "relative_path" in f
            assert "title" in f
            assert "word_count" in f
            assert "size_bytes" in f
            assert "frontmatter" in f

    def test_title_extracted(self, markdown_directory: str) -> None:
        files = list_markdown_files(markdown_directory)
        titles = [f["title"] for f in files if f["title"] is not None]
        assert "Document One" in titles or "Document Two" in titles

    def test_directory_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            list_markdown_files(str(tmp_path / "missing_dir"))
