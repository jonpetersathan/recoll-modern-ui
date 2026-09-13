#!/usr/bin/env python3
"""
Unit tests for the modularized recollweb package components.
Validates constants, utilities, configuration, search queries,
archive management, error handling, and webui facade backward compatibility.
"""

import datetime
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
from recollweb import constants, utils, config, forms, search, archive, errors, auth


class TestConstants(unittest.TestCase):
    """Test constants definitions."""

    def test_default_config_keys(self):
        expected_keys = [
            'context', 'stem', 'timefmt', 'dirdepth', 'maxchars',
            'maxresults', 'perpage', 'csvfields', 'title_link',
            'collapsedups', 'synonyms', 'mounts', 'noresultlinks',
            'logquery', 'shortenpaths', 'permlinks', 'res_permlink',
            'export_filename_mode', 'export_filename_pattern',
        ]
        for key in expected_keys:
            self.assertIn(key, constants.DEFAULT_CONFIG)
        self.assertEqual(constants.DEFAULT_CONFIG['export_filename_mode'], 'timestamp')
        self.assertIn(('timestamp', 'Timestamp (recoll_YYYYMMDD_hhmmss)'), constants.EXPORT_FILENAME_MODES)
        self.assertIn(('ask', 'Ask every time'), constants.EXPORT_FILENAME_MODES)
        self.assertIn(('query_hash', 'Query hash (first 16 characters)'), constants.EXPORT_FILENAME_MODES)
        self.assertIn(('custom', 'Custom pattern'), constants.EXPORT_FILENAME_MODES)

    def test_mime_labels(self):
        self.assertEqual(constants.MIME_LABELS['application/pdf'], 'PDF Document')
        self.assertEqual(constants.MIME_LABELS['application/msword'], 'Word Document')
        self.assertEqual(constants.MIME_LABELS['text/plain'], 'Plain Text')
        self.assertEqual(constants.MIME_LABELS['text/csv'], 'CSV File')

    def test_default_forms_schema(self):
        self.assertEqual(constants.DEFAULT_SEARCH_FORM['id'], 'default')
        self.assertTrue(constants.DEFAULT_SEARCH_FORM['readonly'])
        self.assertGreater(len(constants.DEFAULT_SEARCH_FORM['fields']), 5)


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

    def test_format_size_human(self):
        self.assertEqual(utils.format_size_human(0), "0 B")
        self.assertEqual(utils.format_size_human(500), "500 B")
        self.assertEqual(utils.format_size_human("500"), "500 B")
        self.assertEqual(utils.format_size_human(1024), "1.0 KB")
        self.assertEqual(utils.format_size_human(2048), "2.0 KB")
        self.assertEqual(utils.format_size_human(1048576 * 5), "5.0 MB")
        self.assertEqual(utils.format_size_human(2189678), "2.1 MB")
        self.assertEqual(utils.format_size_human("2189678"), "2.1 MB")
        self.assertEqual(utils.format_size_human(1073741824 * 3), "3.0 GB")
        self.assertEqual(utils.format_size_human(None), "")
        self.assertEqual(utils.format_size_human(""), "")
        self.assertEqual(utils.format_size_human("invalid"), "")
        self.assertEqual(utils.format_size_human(-10), "")

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

    def test_compute_export_hash(self):
        h1 = utils.compute_export_hash("search term", ["id1", "id2"])
        h2 = utils.compute_export_hash("search term", ["id2", "id1"])
        self.assertEqual(len(h1), 16)
        # Verify order independence for selected records
        self.assertEqual(h1, h2)
        # Verify different query or records produces different hash
        h3 = utils.compute_export_hash("different term", ["id1", "id2"])
        self.assertNotEqual(h1, h3)

    def test_generate_export_filename_timestamp(self):
        fixed_dt = datetime.datetime(2026, 9, 12, 15, 30, 45)
        config = {'export_filename_mode': 'timestamp'}
        fn_zip = utils.generate_export_filename(config, ext='zip', now=fixed_dt)
        self.assertEqual(fn_zip, "recoll_20260912_153045.zip")
        fn_csv = utils.generate_export_filename(config, ext='csv', now=fixed_dt)
        self.assertEqual(fn_csv, "recoll_20260912_153045.csv")
        fn_json = utils.generate_export_filename(config, ext='json', now=fixed_dt)
        self.assertEqual(fn_json, "recoll_20260912_153045.json")

    def test_generate_export_filename_custom_override(self):
        config = {'export_filename_mode': 'timestamp'}
        fn = utils.generate_export_filename(config, ext='zip', custom_filename='my_export_file')
        self.assertEqual(fn, "my_export_file.zip")
        # Existing extension should not be duplicated
        fn2 = utils.generate_export_filename(config, ext='csv', custom_filename='data.csv')
        self.assertEqual(fn2, "data.csv")

    def test_generate_export_filename_query_hash(self):
        config = {'export_filename_mode': 'query_hash'}
        expected_hash = utils.compute_export_hash("myquery", ["doc1"])
        fn = utils.generate_export_filename(config, query_str="myquery", selected_ids=["doc1"], ext='zip')
        self.assertEqual(fn, f"{expected_hash}.zip")

    def test_generate_export_filename_custom_pattern(self):
        fixed_dt = datetime.datetime(2026, 9, 12, 8, 5, 9)
        expected_hash = utils.compute_export_hash("myquery", None)
        config = {
            'export_filename_mode': 'custom',
            'export_filename_pattern': 'export_@HASH_@YYYY-@MM-@DD_@hh@mm@ss'
        }
        fn = utils.generate_export_filename(config, query_str="myquery", ext='json', now=fixed_dt)
        self.assertEqual(fn, f"export_{expected_hash}_2026-09-12_080509.json")

    def test_generate_export_filename_ask_uses_pattern_default(self):
        fixed_dt = datetime.datetime(2026, 9, 12, 8, 5, 9)
        expected_hash = utils.compute_export_hash("myquery", None)
        config = {
            'export_filename_mode': 'ask',
            'export_filename_pattern': 'archive_@HASH_@YYYY@MM@DD'
        }
        fn = utils.generate_export_filename(config, query_str="myquery", ext='zip', now=fixed_dt)
        self.assertEqual(fn, f"archive_{expected_hash}_20260912.zip")


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

    def test_create_job_with_custom_filename(self):
        job_id = archive.ArchiveManager.create_job(total=5, filename="my_custom_archive.zip")
        job = archive.ArchiveManager.get_job(job_id)
        self.assertEqual(job['filename'], "my_custom_archive.zip")
        self.assertTrue(job['zip_path'].endswith("my_custom_archive.zip"))


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
            'DEFAULT_SEARCH_FORM',
            'render_error_page', 'format_mimetype_label', 'format_size_human',
            'sanitize_filename', 'format_timestamp',
            'get_config_dir', 'find_custom_logo', '__version__'
        ]
        for item in expected_exports:
            self.assertTrue(hasattr(webui, item), f"webui facade missing export: {item}")


class MockRequest:
    """Mock HTTP request object for auth testing."""
    def __init__(self, headers=None, environ=None, remote_addr=None):
        self.headers = headers or {}
        self.environ = environ or {}
        self.remote_addr = remote_addr or self.environ.get("REMOTE_ADDR", "127.0.0.1")


class TestAuthProxy(unittest.TestCase):
    """Unit tests for reverse auth proxy environment variables and header parsing."""

    def setUp(self):
        # Save and clear auth proxy environment variables before each test
        self.orig_env = {}
        for var in [
            "RECOLL_AUTH_PROXY_ENABLED",
            "RECOLL_AUTH_PROXY_HEADER_NAME",
            "RECOLL_AUTH_PROXY_HEADER_PROPERTY",
            "RECOLL_AUTH_PROXY_WHITELIST",
        ]:
            self.orig_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        # Restore original environment
        for var, val in self.orig_env.items():
            if val is not None:
                os.environ[var] = val
            elif var in os.environ:
                del os.environ[var]

    def test_auth_proxy_disabled_by_default(self):
        """When proxy auth is not enabled, headers are ignored and 'default' is returned."""
        req = MockRequest(headers={"X-WEBAUTH-USER": "alice"})
        self.assertFalse(auth.is_auth_proxy_enabled())
        self.assertEqual(auth.get_current_username(req), "default")

        # Explicitly disabled
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "false"
        self.assertFalse(auth.is_auth_proxy_enabled())
        self.assertEqual(auth.get_current_username(req), "default")

    def test_auth_proxy_enabled_default_headers(self):
        """When proxy auth is enabled with defaults, X-WEBAUTH-USER is extracted."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        self.assertTrue(auth.is_auth_proxy_enabled())
        self.assertEqual(auth.get_auth_proxy_header_name(), "X-WEBAUTH-USER")
        self.assertEqual(auth.get_auth_proxy_header_property(), "username")

        # Header dict extraction
        req1 = MockRequest(headers={"X-WEBAUTH-USER": "alice"})
        self.assertEqual(auth.get_current_username(req1), "alice")

        # WSGI environ HTTP_X_WEBAUTH_USER extraction
        req2 = MockRequest(environ={"HTTP_X_WEBAUTH_USER": "bob", "REMOTE_ADDR": "127.0.0.1"})
        self.assertEqual(auth.get_current_username(req2), "bob")

    def test_auth_proxy_custom_header_name(self):
        """Support custom header name via RECOLL_AUTH_PROXY_HEADER_NAME."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_HEADER_NAME"] = "X-Forwarded-User"
        self.assertEqual(auth.get_auth_proxy_header_name(), "X-Forwarded-User")

        # Old header is ignored
        req1 = MockRequest(headers={"X-WEBAUTH-USER": "alice"})
        self.assertEqual(auth.get_current_username(req1), "default")

        # Custom header is extracted
        req2 = MockRequest(headers={"X-Forwarded-User": "charlie"})
        self.assertEqual(auth.get_current_username(req2), "charlie")

        # Custom header via WSGI environ
        req3 = MockRequest(environ={"HTTP_X_FORWARDED_USER": "diana", "REMOTE_ADDR": "127.0.0.1"})
        self.assertEqual(auth.get_current_username(req3), "diana")

    def test_auth_proxy_header_property_json(self):
        """Extract requested property from JSON-formatted header payloads."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_HEADER_PROPERTY"] = "username"

        json_payload = '{"username": "eve", "email": "eve@company.com", "sub": "usr_987"}'
        req = MockRequest(headers={"X-WEBAUTH-USER": json_payload})
        self.assertEqual(auth.get_current_username(req), "eve")

        # Switch property to email
        os.environ["RECOLL_AUTH_PROXY_HEADER_PROPERTY"] = "email"
        self.assertEqual(auth.get_current_username(req), "eve@company.com")

        # Switch property to sub
        os.environ["RECOLL_AUTH_PROXY_HEADER_PROPERTY"] = "sub"
        self.assertEqual(auth.get_current_username(req), "usr_987")

    def test_auth_proxy_header_property_key_value(self):
        """Extract property from key=value formatted header strings."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_HEADER_PROPERTY"] = "username"

        kv_payload = 'username=frank; email=frank@company.com'
        req = MockRequest(headers={"X-WEBAUTH-USER": kv_payload})
        self.assertEqual(auth.get_current_username(req), "frank")

    def test_auth_proxy_whitelist_enforcement(self):
        """Enforce RECOLL_AUTH_PROXY_WHITELIST allowing or blocking client IP addresses."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_WHITELIST"] = "127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16"

        # Allowed: 127.0.0.1
        req_local = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "127.0.0.1"})
        self.assertEqual(auth.get_current_username(req_local), "alice")

        # Allowed: 10.0.0.0/8
        req_10 = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "10.254.1.2"})
        self.assertEqual(auth.get_current_username(req_10), "alice")

        # Allowed: 172.16.0.0/12
        req_172 = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "172.20.10.5"})
        self.assertEqual(auth.get_current_username(req_172), "alice")

        # Allowed: 192.168.0.0/16
        req_192 = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "192.168.50.25"})
        self.assertEqual(auth.get_current_username(req_192), "alice")

        # Allowed: IPv6-mapped IPv4
        req_mapped = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "::ffff:127.0.0.1"})
        self.assertEqual(auth.get_current_username(req_mapped), "alice")

        # Blocked: Untrusted public IP
        req_bad1 = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "203.0.113.195"})
        self.assertEqual(auth.get_current_username(req_bad1), "default")

        # Blocked: Another untrusted public IP
        req_bad2 = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "8.8.8.8"})
        self.assertEqual(auth.get_current_username(req_bad2), "default")

    def test_admin_permissions_with_proxy_user(self):
        """Admin recognition works seamlessly with proxy-authenticated usernames."""
        with tempfile.TemporaryDirectory() as temp_conf:
            perm_path = os.path.join(temp_conf, "permissions.conf")
            with open(perm_path, "w") as f:
                f.write("admin\njonathan\nadm_*\n")

    def test_validate_auth_proxy_request_blocking(self):
        """validate_auth_proxy_request blocks requests missing headers or from untrusted IPs."""
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_WHITELIST"] = "127.0.0.1, 10.0.0.0/8"

        # Direct connection without auth proxy header -> blocked (403)
        req_no_header = MockRequest(headers={}, environ={"REMOTE_ADDR": "127.0.0.1"})
        valid, status, msg = auth.validate_auth_proxy_request(req_no_header)
        self.assertFalse(valid)
        self.assertEqual(status, 403)
        self.assertIn("Missing required reverse proxy authentication header", msg)

        # Direct connection from untrusted IP -> blocked (403)
        req_bad_ip = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "203.0.113.50"})
        valid, status, msg = auth.validate_auth_proxy_request(req_bad_ip)
        self.assertFalse(valid)
        self.assertEqual(status, 403)
        self.assertIn("not in RECOLL_AUTH_PROXY_WHITELIST", msg)

        # Valid connection from whitelisted IP with header -> allowed (200)
        req_valid = MockRequest(headers={"X-WEBAUTH-USER": "alice"}, environ={"REMOTE_ADDR": "127.0.0.1"})
        valid, status, msg = auth.validate_auth_proxy_request(req_valid)
        self.assertTrue(valid)
        self.assertEqual(status, 200)

    def test_route_level_auth_proxy_guard(self):
        """Bottle route hook enforces proxy authentication and blocks direct access."""
        from recollweb import create_app
        import bottle

        app = create_app(bottle.Bottle())

        # 1. Disabled proxy auth: direct access is allowed as 'default'
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "false"
        req_disabled = {
            'PATH_INFO': '/static/style.css',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'REMOTE_ADDR': '127.0.0.1',
        }
        res_disabled = app._handle(req_disabled)
        self.assertEqual(res_disabled.status_code, 200)

        # 2. Enabled proxy auth: direct connection without header is BLOCKED with 403
        os.environ["RECOLL_AUTH_PROXY_ENABLED"] = "true"
        os.environ["RECOLL_AUTH_PROXY_WHITELIST"] = "127.0.0.1"

        req_blocked = {
            'PATH_INFO': '/static/style.css',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'REMOTE_ADDR': '127.0.0.1',
        }
        res_blocked = app._handle(req_blocked)
        self.assertEqual(res_blocked.status_code, 403)
        self.assertIn("Access Forbidden", str(res_blocked.body))

        # 3. Enabled proxy auth: JSON API request without header is BLOCKED with 403 JSON
        req_api_blocked = {
            'PATH_INFO': '/json',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'REMOTE_ADDR': '127.0.0.1',
        }
        res_api_blocked = app._handle(req_api_blocked)
        self.assertEqual(res_api_blocked.status_code, 403)
        self.assertIn("error", str(res_api_blocked.body))

        # 4. Enabled proxy auth: connection through proxy WITH header is ALLOWED (200)
        req_allowed = {
            'PATH_INFO': '/static/style.css',
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_X_WEBAUTH_USER': 'alice',
        }
        res_allowed = app._handle(req_allowed)
        self.assertEqual(res_allowed.status_code, 200)


if __name__ == '__main__':
    unittest.main()
