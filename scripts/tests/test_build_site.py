#!/usr/bin/env python3
"""Regression tests for the generated site parser and public file index."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("build_site", REPO / "scripts" / "build-site.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load scripts/build-site.py")
build_site = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_site
SPEC.loader.exec_module(build_site)


class MarkdownRenderingTests(unittest.TestCase):
    def test_inline_html_is_escaped_and_unsafe_links_are_not_rendered(self) -> None:
        rendered = build_site.inline('<script>alert("x")</script> [run](javascript:alert(1))')
        self.assertNotIn("<script>", rendered)
        self.assertNotIn('href="javascript:', rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_link_attribute_characters_are_escaped(self) -> None:
        rendered = build_site.inline('[safe](https://example.com/\"><svg/onload=alert(1))')
        self.assertIn("&quot;", rendered)
        self.assertNotIn("<svg", rendered)
        self.assertIn('rel="noopener noreferrer"', rendered)

    def test_lists_keep_nested_lists_inside_their_parent_item(self) -> None:
        markup, _ = build_site.md_to_html(
            "# Example\n\n1. First\n   - Nested\n   - Also nested\n2. Second\n\n- [ ] Todo\n- [x] Done\n",
            set(),
        )
        self.assertIn(
            "<ol><li>First<ul><li>Nested</li><li>Also nested</li></ul></li><li>Second</li></ol>",
            markup,
        )
        self.assertIn('<li class="task"><input type="checkbox" aria-label="Todo" disabled> Todo</li>', markup)
        self.assertIn('<li class="task"><input type="checkbox" aria-label="Done" disabled checked> Done</li>', markup)
        self.assertNotIn("<ul></ul><ol>", markup)

    def test_search_text_keeps_code_and_table_content(self) -> None:
        text = build_site.plain_markdown(
            "| Flag | Meaning |\n|---|---|\n| `--persist` | Write MASTER.md |\n\n```bash\npython3 search.py --design-system\n```"
        )
        self.assertIn("persist", text)
        self.assertIn("MASTER.md", text)
        self.assertIn("python3 search.py --design-system", text)


class DocumentSearchTests(unittest.TestCase):
    def test_duplicate_formatted_headings_get_their_own_search_anchors(self) -> None:
        markdown = (
            "# Fixture\n\n"
            "## **Repeated** ##\n\nFirst section has enough searchable content.\n\n"
            "## `Repeated`\n\nSecond section has enough searchable content.\n"
        )
        _, headings = build_site.md_to_html(markdown, set())
        entries = build_site.search_entries_for_document("fixture", "Fixture", markdown, headings)
        self.assertEqual([entry["anchor"] for entry in entries], ["repeated", "repeated-2"])


class RepositoryIndexTests(unittest.TestCase):
    def test_index_contains_tracked_text_and_lists_binary_assets(self) -> None:
        manifest, index = build_site.build_repository_file_data()
        files_by_path = {entry["path"]: entry for entry in manifest}
        indexed_paths = {entry["path"] for entry in index["files"]}
        self.assertIn("AGENTS.md", files_by_path)
        self.assertIn("skills/ui-styling/canvas-fonts/WorkSans-Regular.ttf", files_by_path)
        self.assertIn("scripts/build-site.py", indexed_paths)
        self.assertNotIn("repository-files.json", files_by_path)
        self.assertFalse(files_by_path["skills/ui-styling/canvas-fonts/WorkSans-Regular.ttf"]["searchable"])
        self.assertEqual(len(files_by_path), len(manifest))


if __name__ == "__main__":
    unittest.main()
