#!/usr/bin/env python3
"""
Unit tests for the modularized recollweb package components.
Validates constants, utilities, configuration, search queries,
archive management, error handling, and webui facade backward compatibility.
"""

import os
import sys
import unittest
import tempfile
import shutil
import time

# Ensure src is in sys.path
for candidate in ["/app/src", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

import recollweb
from recollweb import constants, utils, config, forms, search, archive, errors


class TestConstants(unittest.TestCase):
    """Test constants definitions."""

    def test_default_config_keys(self):
        expected_keys = [
            'context', 'stem', 'timefmt', 'dirdepth', 'maxchars',
            'maxresults', 'perpage', 'csvfields', 'title_link',
            'collapsedups', 'synonyms', 'mounts', 'noresultlinks',
            'logquery', 'shortenpaths', 'permlinks', 'res_permlink'
        ]
        for key in expected_keys:
            self.assertIn(key, constants.DEFAULT_CONFIG)

    def test_mime_labels(self):
        self.assertEqual(constants.MIME_LABELS['application/pdf'], 'PDF Document')
        self.assertEqual(constants.MIME_LABELS['application/msword'], 'Word Document')
        self.assertEqual(constants.MIME_LABELS['text/plain'], 'Plain Text')
        self.assertEqual(constants.MIME_LABELS['text/csv'], 'CSV File')

    def test_default_forms_schema(self):
        self.assertEqual(constants.DEFAULT_SEARCH_FORM['id'], 'default')
        self.assertTrue(constants.DEFAULT_SEARCH_FORM['readonly'])
        self.assertGreater(len(constants.DEFAULT_SEARCH_FORM['fields']), 5)

        self.assertEqual(constants.SAMPLE_CUSTOM_FORM['id'], 'document_types')
        self.assertFalse(constants.SAMPLE_CUSTOM_FORM['readonly'])


class TestUtils(unittest.TestCase):
    """Test helper functions in utils module."""

    def test_format_mimetype_label(self):
        self.assertEqual(utils.format_mimetype_label('application/pdf'), 'PDF Document')
        self.assertEqual(utils.format_mimetype_label('text/csv'), 'CSV File')
        self.assertEqual(utils.format_mimetype_label('audio/mp3'), 'Audio / Media')
        self.assertEqual(utils.format_mimetype_label('video/mp4'), 'Video / Media')
        self.assertEqual(utils.format_mimetype_label('image/jpeg'), 'JPEG Image')
        # Fallback by extension
        self.assertEqual(utils.format_mimetype_label('', filename='test.pdf'), 'PDF Document')
        self.assertEqual(utils.format_mimetype_label('', filename='test.mycustomext'), 'MYCUSTOMEXT File')

    def test_sanitize_filename(self):
        self.assertEqual(utils.sanitize_filename("safe_file-123"), "safe_file-123")
        self.assertEqual(utils.sanitize_filename("bad/file\\name?*.txt"), "bad_file_name___txt")

    def test_format_timestamp(self):
        formatted = utils.format_timestamp("0", "%Y-%m-%d")
        self.assertTrue(formatted.startswith("1970"))
        # Non-numeric string gracefully defaults to 0
        fallback = utils.format_timestamp("invalid", "%Y-%m-%d")
        self.assertTrue(fallback.startswith("1970"))

    def test_extract_common_prefix(self):
        self.assertEqual(utils.extract_common_prefix([]), "")
        self.assertEqual(utils.extract_common_prefix(["/data/docs", "/data/reports"]), "/data/")
        self.assertEqual(utils.extract_common_prefix(["/a/b/c", "/a/b/d"]), "/a/b/")
        self.assertEqual(utils.extract_common_prefix(["/a/b", "/c/d"]), "")


class TestSearchQuery(unittest.TestCase):
    """Test search query formatting."""

    def test_to_recoll_string_basic(self):
        query_data = {'query': 'python tutorial', 'dir': '<all>', 'after': '', 'before': ''}
        qs = search.SearchQuery.to_recoll_string(query_data)
        self.assertEqual(qs, 'python tutorial')

    def test_to_recoll_string_with_dates(self):
        query_data = {'query': 'tax return', 'dir': '<all>', 'after': '2023-01-01', 'before': '2023-12-31'}
        qs = search.SearchQuery.to_recoll_string(query_data)
        self.assertEqual(qs, 'tax return date:2023-01-01/2023-12-31')

    def test_to_recoll_string_with_dir(self):
        query_data = {'query': 'specs', 'dir': 'projects/2024', 'after': '', 'before': ''}
        qs = search.SearchQuery.to_recoll_string(query_data)
        self.assertEqual(qs, 'specs dir:"projects/2024"')


class TestSnippetHighlighter(unittest.TestCase):
    """Test SnippetHighlighter span wrapping."""

    def test_highlight_spans(self):
        highlighter = search.SnippetHighlighter()
        self.assertEqual(highlighter.startMatch(0), '<span class="search-result-highlight">')
        self.assertEqual(highlighter.endMatch(), '</span>')


class TestArchiveManager(unittest.TestCase):
    """Test ArchiveManager job creation, updates, and cancellation."""

    def test_job_lifecycle(self):
        job_id = archive.ArchiveManager.create_job(total=15)
        self.assertIsNotNone(job_id)
        job = archive.ArchiveManager.get_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job['total'], 15)
        self.assertEqual(job['status'], 'zipping')
        self.assertFalse(job['cancelled'])

        # Update job progress
        archive.ArchiveManager.update_job(job_id, processed=5, current_file="file5.pdf")
        updated = archive.ArchiveManager.get_job(job_id)
        self.assertEqual(updated['processed'], 5)
        self.assertEqual(updated['current_file'], "file5.pdf")

        # Cancel job
        archive.ArchiveManager.cancel_job(job_id)
        cancelled = archive.ArchiveManager.get_job(job_id)
        self.assertTrue(cancelled['cancelled'])
        self.assertEqual(cancelled['status'], 'cancelled')


class TestErrorRendering(unittest.TestCase):
    """Test error page template rendering."""

    def test_render_error_page_defaults(self):
        html_404 = errors.render_error_page(code=404)
        self.assertIn("404", html_404)
        self.assertIn("Page Not Found", html_404)

        html_500 = errors.render_error_page(code=500, details="Test DB crash")
        self.assertIn("500", html_500)
        self.assertIn("Internal Server Error", html_500)


class TestWebuiFacade(unittest.TestCase):
    """Test webui facade backward compatibility."""

    def test_facade_exports(self):
        import webui
        expected_exports = [
            'app', 'application', 'bottle', 'logger',
            'ConfigManager', 'SearchFormsManager', 'RecollSearchEngine',
            'SearchQuery', 'SnippetHighlighter', 'ArchiveManager',
            'DEFAULT_CONFIG', 'SORT_OPTIONS', 'DOCUMENT_FIELDS',
            'DEFAULT_SEARCH_FORM', 'SAMPLE_CUSTOM_FORM',
            'render_error_page', 'format_mimetype_label',
            'sanitize_filename', 'format_timestamp',
            'get_config_dir', 'find_custom_logo', '__version__'
        ]
        for item in expected_exports:
            self.assertTrue(hasattr(webui, item), f"webui facade missing export: {item}")


if __name__ == '__main__':
    unittest.main()
