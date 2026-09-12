#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Search and Custom Search Forms.
Verifies form persistence, read-only protection, field compilation,
REST API endpoints, and container restart survival.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import unittest
import zipfile


BASE_URL = os.environ.get("RECOLL_TEST_URL", "http://127.0.0.1:8080")


class TestSearchFormsManager(unittest.TestCase):
    """Unit tests for SearchFormsManager persistence and query compilation."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="recoll_test_forms_")
        for candidate in ["/app/src", os.path.abspath(os.path.join(os.getcwd(), "src"))]:
            if os.path.isdir(candidate) and candidate not in sys.path:
                sys.path.insert(0, candidate)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_form_initialization_and_readonly(self):
        """Verify Default form is generated with readonly=True and full Recoll language support."""
        try:
            from webui import SearchFormsManager, DEFAULT_SEARCH_FORM
        except ImportError:
            self.skipTest("webui cannot be imported in host python (missing C recoll bindings)")

        forms = SearchFormsManager.get_forms(self.test_dir)
        self.assertGreaterEqual(len(forms), 1)
        default_form = forms[0]
        self.assertEqual(default_form["id"], "default")
        self.assertTrue(default_form["readonly"])

        # Verify all Recoll query language capabilities are represented in default form fields
        field_ids = [f["id"] for f in default_form["fields"]]
        expected_ids = [
            "all_terms", "exact_phrase", "any_terms", "none_terms",
            "proximity_terms", "filename", "title", "author",
            "filetype", "size_min", "size_max", "dir_scope"
        ]
        for eid in expected_ids:
            self.assertIn(eid, field_ids, f"Default form missing Recoll operator field: {eid}")

        # Verify CSV and Email (MSG and EML) support in filetype dropdown options
        filetype_field = next(f for f in default_form["fields"] if f["id"] == "filetype")
        opt_labels = [o["label"] for o in filetype_field["options"]]
        opt_queries = [o["query"] for o in filetype_field["options"]]
        self.assertIn("CSV File (ext:csv)", opt_labels)
        self.assertIn("ext:csv", opt_queries)
        self.assertIn("Email (ext:eml OR ext:msg)", opt_labels)
        self.assertIn("ext:eml OR ext:msg", opt_queries)

    def test_readonly_protection(self):
        """Verify that default form cannot be edited or deleted."""
        try:
            from webui import SearchFormsManager
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        with self.assertRaises(ValueError):
            SearchFormsManager.save_custom_form(self.test_dir, {"id": "default", "name": "Hacked", "fields": []})

        with self.assertRaises(ValueError):
            SearchFormsManager.delete_custom_form(self.test_dir, "default")

    def test_create_and_update_custom_form(self):
        """Verify creating, persisting to JSON, updating, and reading custom forms."""
        try:
            from webui import SearchFormsManager
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        new_form_data = {
            "name": "Invoice Classifier",
            "description": "Searches invoice and accounting records",
            "fields": [
                {
                    "id": "doc_type",
                    "label": "Document Type",
                    "type": "select",
                    "helper": "Select invoice category",
                    "options": [
                        {"label": "Paid Invoices", "query": "filename:*PAID*"},
                        {"label": "Pending Invoices", "query": "filename:*PENDING*"}
                    ]
                },
                {
                    "id": "amount",
                    "label": "Keyword",
                    "type": "text",
                    "query_format": "{value}"
                }
            ]
        }

        saved = SearchFormsManager.save_custom_form(self.test_dir, new_form_data)
        self.assertIn("id", saved)
        self.assertFalse(saved["readonly"])
        form_id = saved["id"]

        # Check file exists on disk
        forms_file = os.path.join(self.test_dir, "forms.json")
        self.assertTrue(os.path.isfile(forms_file))

        # Reload from disk
        loaded_forms = SearchFormsManager.get_forms(self.test_dir)
        found = next((f for f in loaded_forms if f["id"] == form_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Invoice Classifier")
        self.assertEqual(len(found["fields"]), 2)
        self.assertEqual(found["fields"][0]["options"][0]["query"], "filename:*PAID*")

        # Update form
        found["name"] = "Updated Invoice Classifier"
        SearchFormsManager.save_custom_form(self.test_dir, found)
        reloaded = SearchFormsManager.get_forms(self.test_dir)
        updated_form = next(f for f in reloaded if f["id"] == form_id)
        self.assertEqual(updated_form["name"], "Updated Invoice Classifier")

        # Delete form
        SearchFormsManager.delete_custom_form(self.test_dir, form_id)
        after_delete = SearchFormsManager.get_forms(self.test_dir)
        self.assertIsNone(next((f for f in after_delete if f["id"] == form_id), None))


    def test_static_query_field_lifecycle(self):
        """Verify custom search form with Static Query field persists correctly."""
        try:
            from webui import SearchFormsManager
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        form_data = {
            "name": "PDFs Only Form",
            "description": "Form with static query restriction",
            "fields": [
                {
                    "id": "sq_pdf",
                    "label": "PDF Filter",
                    "type": "static_query",
                    "query": "mime:application/pdf"
                },
                {
                    "id": "sq_dir",
                    "label": "Archive Dir",
                    "type": "static",
                    "query": "dir:/data"
                },
                {
                    "id": "search_term",
                    "label": "Keyword",
                    "type": "text",
                    "query_format": "{value}"
                }
            ]
        }

        saved = SearchFormsManager.save_custom_form(self.test_dir, form_data)
        self.assertIn("id", saved)
        form_id = saved["id"]

        # Reload from disk
        loaded_forms = SearchFormsManager.get_forms(self.test_dir)
        found = next((f for f in loaded_forms if f["id"] == form_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(len(found["fields"]), 3)
        self.assertEqual(found["fields"][0]["type"], "static_query")
        self.assertEqual(found["fields"][0]["query"], "mime:application/pdf")
        self.assertEqual(found["fields"][1]["type"], "static")
        self.assertEqual(found["fields"][1]["query"], "dir:/data")

        # Clean up
        SearchFormsManager.delete_custom_form(self.test_dir, form_id)

    def test_toggle_filter_field_lifecycle(self):
        """Verify custom search form with Toggle Filter field persists correctly."""
        try:
            from webui import SearchFormsManager
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        form_data = {
            "name": "Toggle Filter Test Form",
            "description": "Form with toggle switches",
            "fields": [
                {
                    "id": "pdf_only",
                    "label": "PDFs Only",
                    "type": "toggle",
                    "query": "mime:application/pdf"
                },
                {
                    "id": "legacy_check",
                    "label": "Legacy Checkbox",
                    "type": "checkbox",
                    "query": "filename:*archive*"
                },
                {
                    "id": "kw",
                    "label": "Keywords",
                    "type": "text",
                    "query_format": "{value}"
                }
            ]
        }

        saved = SearchFormsManager.save_custom_form(self.test_dir, form_data)
        self.assertIn("id", saved)
        form_id = saved["id"]

        # Reload from disk
        loaded_forms = SearchFormsManager.get_forms(self.test_dir)
        found = next((f for f in loaded_forms if f["id"] == form_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(len(found["fields"]), 3)
        self.assertEqual(found["fields"][0]["type"], "toggle")
        self.assertEqual(found["fields"][0]["query"], "mime:application/pdf")
        # Legacy checkbox is normalized to toggle
        self.assertEqual(found["fields"][1]["type"], "toggle")

        # Clean up
        SearchFormsManager.delete_custom_form(self.test_dir, form_id)

    def test_form_fields_enable_disable_persistence(self):
        """Verify saving and retrieving forms with enabled and disabled fields."""
        try:
            from webui import SearchFormsManager
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        form_data = {
            "name": "Field Toggle Test Form",
            "description": "Form with enabled and disabled fields",
            "fields": [
                {
                    "id": "f_active",
                    "label": "Active Keyword",
                    "type": "text",
                    "enabled": True,
                    "query_format": "keyword:{value}"
                },
                {
                    "id": "f_inactive",
                    "label": "Disabled Tag",
                    "type": "text",
                    "enabled": False,
                    "query_format": "tag:{value}"
                }
            ]
        }

        saved = SearchFormsManager.save_custom_form(self.test_dir, form_data)
        self.assertTrue(saved["fields"][0]["enabled"])
        self.assertFalse(saved["fields"][1]["enabled"])

        # Reload from disk
        loaded = SearchFormsManager.get_forms(self.test_dir)
        match = next(f for f in loaded if f["id"] == saved["id"])
        self.assertTrue(match["fields"][0]["enabled"])
        self.assertFalse(match["fields"][1]["enabled"])

        # Clean up
        SearchFormsManager.delete_custom_form(self.test_dir, saved["id"])


class TestContainerEndpoints(unittest.TestCase):
    """Integration tests running against active container."""

    def _http_request(self, path: str, method: str = "GET", data: dict = None) -> tuple:
        url = f"{BASE_URL}{path}"
        headers = {}
        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                content = resp.read().decode("utf-8")
                return status, content
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8")

    def _raw_request(self, path: str, method: str = "GET", headers: dict = None) -> tuple:
        url = f"{BASE_URL}{path}"
        req = urllib.request.Request(url, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as err:
            return err.code, err.read(), dict(err.headers)

    def test_search_page_has_advanced_button_and_panel(self):
        """Verify root page has Advanced button and panel, and settings button replaced in button row."""
        status, html = self._http_request("/")
        self.assertEqual(status, 200)
        self.assertIn('id="btn-toggle-advanced"', html)
        self.assertIn('Advanced</span>', html)
        self.assertIn('id="advanced-search-panel"', html)
        self.assertIn('id="active-form-selector"', html)
        self.assertIn('id="recoll-search-forms-data"', html)

    def test_settings_page_has_custom_forms_section(self):
        """Verify settings page contains custom search forms section and modals."""
        status, html = self._http_request("/settings")
        self.assertEqual(status, 200)
        self.assertIn('id="custom-forms-section"', html)
        self.assertIn('Custom Search Forms</span>', html)
        self.assertIn('id="btn-create-form"', html)
        self.assertIn('id="form-builder-overlay"', html)
        self.assertIn('id="schema-viewer-overlay"', html)

    def test_api_get_forms(self):
        """Verify GET /api/forms returns JSON forms list."""
        status, content = self._http_request("/api/forms")
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertIn("forms", data)
        self.assertGreaterEqual(len(data["forms"]), 2)
        default_form = data["forms"][0]
        self.assertEqual(default_form["id"], "default")
        self.assertTrue(default_form["readonly"])

        # Check that filetype options contain CSV and Email
        filetype_field = next(f for f in default_form["fields"] if f["id"] == "filetype")
        opt_queries = [o["query"] for o in filetype_field["options"]]
        self.assertIn("ext:csv", opt_queries)
        self.assertIn("ext:eml OR ext:msg", opt_queries)

    def test_api_form_crud_lifecycle(self):
        """Verify complete CRUD lifecycle through /api/forms and /api/forms/delete."""
        # 1. Create a custom search form with Document Type dropdown
        new_form = {
            "name": "Integration Test Form",
            "description": "Created by automated integration test",
            "fields": [
                {
                    "id": "doc_type",
                    "label": "Document Type",
                    "type": "select",
                    "helper": "Filter documents by type",
                    "options": [
                        {"label": "All", "query": ""},
                        {"label": "000 Files", "query": "filename:*000*"}
                    ]
                },
                {
                    "id": "search_word",
                    "label": "Search Word",
                    "type": "text",
                    "query_format": "{value}"
                }
            ]
        }
        status, content = self._http_request("/api/forms", method="POST", data=new_form)
        self.assertEqual(status, 200)
        res = json.loads(content)
        self.assertTrue(res.get("success"))
        created_form = res["form"]
        form_id = created_form["id"]
        self.assertFalse(created_form["readonly"])

        # 2. Verify form is present in GET /api/forms
        status, content = self._http_request("/api/forms")
        data = json.loads(content)
        found = next((f for f in data["forms"] if f["id"] == form_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Integration Test Form")

        # 3. Verify read-only enforcement on default form
        status, content = self._http_request("/api/forms", method="POST", data={"id": "default", "name": "Bad"})
        self.assertEqual(status, 400)
        err_res = json.loads(content)
        self.assertFalse(err_res.get("success"))

        status, content = self._http_request("/api/forms/delete", method="POST", data={"id": "default"})
        self.assertEqual(status, 400)
        err_del = json.loads(content)
        self.assertFalse(err_del.get("success"))

        # 4. Search execution with query from this custom form
        status, search_res = self._http_request("/results?query=" + urllib.parse.quote("filename:*000*"))
        self.assertEqual(status, 200)
        self.assertIn("000345.pdf", search_res)

        # 5. Delete the custom form
        status, del_content = self._http_request("/api/forms/delete", method="POST", data={"id": form_id})
        self.assertEqual(status, 200)
        del_res = json.loads(del_content)
        self.assertTrue(del_res.get("success"))

        # 6. Verify deleted
        status, content_after = self._http_request("/api/forms")
        data_after = json.loads(content_after)
        self.assertIsNone(next((f for f in data_after["forms"] if f["id"] == form_id), None))

    def test_api_static_query_field_form(self):
        """Verify creating custom form with Static Query via REST API and embedding in UI."""
        form_payload = {
            "name": "PDF Reports Static Search",
            "description": "Restricted search form with static PDF filter",
            "fields": [
                {
                    "id": "sq_pdf_clause",
                    "label": "PDF Constraint",
                    "type": "static_query",
                    "query": "mime:application/pdf"
                },
                {
                    "id": "query_text",
                    "label": "Search Terms",
                    "type": "text",
                    "query_format": "{value}"
                }
            ]
        }

        # 1. Create form via API
        status, content = self._http_request("/api/forms", method="POST", data=form_payload)
        self.assertEqual(status, 200)
        res = json.loads(content)
        self.assertTrue(res.get("success"))
        created = res["form"]
        form_id = created["id"]
        self.assertEqual(len(created["fields"]), 2)
        self.assertEqual(created["fields"][0]["type"], "static_query")
        self.assertEqual(created["fields"][0]["query"], "mime:application/pdf")

        # 2. Retrieve all forms and check
        status, get_content = self._http_request("/api/forms")
        self.assertEqual(status, 200)
        all_forms = json.loads(get_content)["forms"]
        match = next((f for f in all_forms if f["id"] == form_id), None)
        self.assertIsNotNone(match)
        self.assertEqual(match["name"], "PDF Reports Static Search")
        self.assertEqual(match["fields"][0]["type"], "static_query")

        # 3. Check that root page embeds this form in recoll-search-forms-data
        status, html = self._http_request("/")
        self.assertEqual(status, 200)
        self.assertIn("PDF Reports Static Search", html)
        self.assertIn("sq_pdf_clause", html)
        self.assertIn("static_query", html)

        # 4. Clean up
        status, del_content = self._http_request("/api/forms/delete", method="POST", data={"id": form_id})
        self.assertEqual(status, 200)

    def test_container_restart_survival(self):
        """Verify custom forms written to disk persist across container restart."""
        # Create a persistent test form
        persistent_form = {
            "name": "Restart Survival Test Form",
            "description": "Must persist across container restart",
            "fields": [
                {
                    "id": "persisted_field",
                    "label": "Persisted Document Filter",
                    "type": "select",
                    "options": [
                        {"label": "001 Files", "query": "filename:*001*"}
                    ]
                }
            ]
        }
        status, content = self._http_request("/api/forms", method="POST", data=persistent_form)
        self.assertEqual(status, 200)
        form_id = json.loads(content)["form"]["id"]

        # Restart container
        os.system("podman restart recoll >/dev/null 2>&1")
        # Wait for service readiness
        for _ in range(25):
            time.sleep(0.5)
            try:
                s, _ = self._http_request("/")
                if s == 200:
                    break
            except Exception:
                pass

        # Verify form is still present after restart
        status, content = self._http_request("/api/forms")
        self.assertEqual(status, 200)
        data = json.loads(content)
        found = next((f for f in data["forms"] if f["id"] == form_id), None)
        self.assertIsNotNone(found, "Custom form was lost after container restart!")
        self.assertEqual(found["name"], "Restart Survival Test Form")

        # Clean up
        self._http_request("/api/forms/delete", method="POST", data={"id": form_id})

    def test_results_page_has_files_button_and_modal(self):
        """Verify results page renders the FILES download button and zipping modal markup."""
        status, html = self._http_request("/results?query=" + urllib.parse.quote("filename:000994.ppt"))
        self.assertEqual(status, 200)
        self.assertIn('id="btn-download-files"', html)
        self.assertIn('<span>FILES</span>', html)
        self.assertIn('id="archive-modal"', html)
        self.assertIn('id="archive-progress-bar"', html)

    def test_archive_single_file_shortcut(self):
        """Verify 1 search result returns single_file=true with direct download link (no zipping)."""
        status, content = self._http_request("/api/archive/start?query=" + urllib.parse.quote("filename:000994.ppt"))
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertTrue(data.get("single_file"))
        self.assertEqual(data.get("total"), 1)
        self.assertIn("download/0", data.get("download_url", ""))

        # Verify downloading from the provided URL serves the single file directly
        dl_status, dl_bytes, dl_headers = self._raw_request(data["download_url"].lstrip("."))
        self.assertEqual(dl_status, 200)
        disp = dl_headers.get("Content-Disposition") or dl_headers.get("content-disposition", "")
        self.assertIn("000994.ppt", disp)

    def test_archive_multi_files_zipping_and_download(self):
        """Verify multiple search results start a zipping job, update progress, and provide search_TIMESTAMP.zip."""
        status, content = self._http_request("/api/archive/start?query=" + urllib.parse.quote("filename:00099*"))
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertFalse(data.get("single_file"))
        self.assertEqual(data.get("total"), 10)
        job_id = data.get("job_id")
        self.assertIsNotNone(job_id)

        # Poll status until ready
        ready = False
        final_status_data = None
        for _ in range(30):
            time.sleep(0.3)
            s_status, s_content = self._http_request(f"/api/archive/status/{job_id}")
            self.assertEqual(s_status, 200)
            status_data = json.loads(s_content)
            if status_data.get("status") == "ready":
                ready = True
                final_status_data = status_data
                break
            elif status_data.get("status") == "error":
                self.fail(f"Archive zipping failed with error: {status_data.get('error')}")

        self.assertTrue(ready, "Archive zipping did not complete in time")
        self.assertEqual(final_status_data.get("percent"), 100)
        download_url = final_status_data.get("download_url")
        self.assertIsNotNone(download_url)

        # Verify downloading the zip
        dl_status, dl_bytes, dl_headers = self._raw_request(download_url)
        self.assertEqual(dl_status, 200)
        content_type = dl_headers.get("Content-Type") or dl_headers.get("content-type", "")
        self.assertIn("application/zip", content_type)
        disp = dl_headers.get("Content-Disposition") or dl_headers.get("content-disposition", "")
        self.assertIn("search_", disp)
        self.assertIn(".zip", disp)

        # Verify zip validity and contents
        with zipfile.ZipFile(io.BytesIO(dl_bytes)) as zf:
            namelist = zf.namelist()
            self.assertGreaterEqual(len(namelist), 5)
            self.assertTrue(any("000994" in name for name in namelist))
            self.assertTrue(any("000995" in name for name in namelist))

    def test_archive_cancel(self):
        """Verify archive job can be cancelled."""
        status, content = self._http_request("/api/archive/start?query=" + urllib.parse.quote("filename:*000*"))
        self.assertEqual(status, 200)
        data = json.loads(content)
        job_id = data.get("job_id")
        self.assertIsNotNone(job_id)

        # Cancel job
        c_status, c_content = self._http_request(f"/api/archive/cancel/{job_id}", method="POST")
        self.assertEqual(c_status, 200)
        c_data = json.loads(c_content)
        self.assertTrue(c_data.get("cancelled"))

        # Check status reflects cancelled
        s_status, s_content = self._http_request(f"/api/archive/status/{job_id}")
        self.assertEqual(s_status, 200)
        s_data = json.loads(s_content)
        self.assertEqual(s_data.get("status"), "cancelled")

    def test_custom_logo_replacement(self):
        """Verify custom logo replacement with logo.png, logo.jpg, and logo.svg in config dir."""
        conf_dir = os.environ.get("RECOLL_CONFDIR", "/root/.recoll")
        self.assertTrue(os.path.isdir(conf_dir), f"Config dir {conf_dir} not found")

        # 1. Verify default logo is served when no custom logo is in config folder
        req = urllib.request.Request(f"{BASE_URL}/logo")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("image/svg+xml", resp.headers.get("Content-Type", ""))
            default_content = resp.read()
            self.assertIn(b"<svg", default_content)

        # 2. Test logo.png replacement
        png_path = os.path.join(conf_dir, "logo.png")
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
        try:
            with open(png_path, "wb") as f:
                f.write(dummy_png)

            with urllib.request.urlopen(f"{BASE_URL}/logo") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("image/png", resp.headers.get("Content-Type", ""))
                self.assertEqual(resp.read(), dummy_png)

            with urllib.request.urlopen(f"{BASE_URL}/favicon.ico") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("image/png", resp.headers.get("Content-Type", ""))
                self.assertEqual(resp.read(), dummy_png)

            with urllib.request.urlopen(f"{BASE_URL}/static/logo.svg") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("image/png", resp.headers.get("Content-Type", ""))
                self.assertEqual(resp.read(), dummy_png)
        finally:
            if os.path.exists(png_path):
                os.remove(png_path)

        # 3. Test logo.jpg replacement
        jpg_path = os.path.join(conf_dir, "logo.jpg")
        dummy_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\xff\xd9"
        try:
            with open(jpg_path, "wb") as f:
                f.write(dummy_jpg)

            with urllib.request.urlopen(f"{BASE_URL}/logo") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("image/jpeg", resp.headers.get("Content-Type", ""))
                self.assertEqual(resp.read(), dummy_jpg)
        finally:
            if os.path.exists(jpg_path):
                os.remove(jpg_path)

        # 4. Test logo.svg replacement
        svg_path = os.path.join(conf_dir, "logo.svg")
        custom_svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="purple"/></svg>'
        try:
            with open(svg_path, "wb") as f:
                f.write(custom_svg)

            with urllib.request.urlopen(f"{BASE_URL}/logo") as resp:
                self.assertEqual(resp.status, 200)
                self.assertIn("image/svg+xml", resp.headers.get("Content-Type", ""))
                self.assertEqual(resp.read(), custom_svg)
        finally:
            if os.path.exists(svg_path):
                os.remove(svg_path)

        # 5. Verify fallback restored after removal
        with urllib.request.urlopen(f"{BASE_URL}/logo") as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("image/svg+xml", resp.headers.get("Content-Type", ""))
            self.assertEqual(resp.read(), default_content)

    def test_settings_page_omits_data_mount_option(self):
        """Verify settings page does not show /data mount option or section when only /data is present."""
        status, html = self._http_request("/settings")
        self.assertEqual(status, 200)
        self.assertNotIn('name="mount_/data"', html)
        self.assertNotIn('name="mount_data"', html)
        self.assertNotIn('Directory Mounts &amp; Remote URLs', html)

    def test_folder_scope_starts_with_contained_folders(self):
        """Verify Folder Scope selector starts directly with folders in /data and omits /data/."""
        status, html = self._http_request("/")
        self.assertEqual(status, 200)
        self.assertIn('id="folders"', html)
        self.assertIn('value="&lt;all&gt;"', html)
        self.assertIn('value="000">000</option>', html)
        self.assertNotIn('value="data"', html)
        self.assertNotIn('value="/data"', html)

    def test_folder_scope_search_execution(self):
        """Verify searches scoped with dir=000 execute successfully without /data/."""
        status, html = self._http_request("/results?query=pdf&dir=000")
        self.assertEqual(status, 200)
        self.assertIn('dir:&quot;000&quot;', html)
        self.assertIn('000979.doc', html)
        self.assertNotIn('No matching database for search directory', html)

    def test_search_results_omit_data_path(self):
        """Verify search results, JSON export, and CSV export omit /data/ path."""
        # 1. HTML search results for subfolder file
        status, html = self._http_request("/results?query=" + urllib.parse.quote("filename:000979.doc"))
        self.assertEqual(status, 200)
        self.assertIn('title="file:///000/000979.doc">000</a>', html)
        self.assertNotIn('/data/000', html)

        # 2. HTML search results for root file in /data
        status_root, html_root = self._http_request("/results?query=" + urllib.parse.quote("filename:000.pdf"))
        self.assertEqual(status_root, 200)
        self.assertIn('title="file:///000.pdf">/</a>', html_root)
        self.assertNotIn('/data/000.pdf', html_root)

        # 3. JSON export
        status_json, content_json = self._http_request("/json?query=" + urllib.parse.quote("filename:000979.doc"))
        self.assertEqual(status_json, 200)
        json_data = json.loads(content_json)
        self.assertEqual(len(json_data["results"]), 1)
        self.assertEqual(json_data["results"][0]["url"], "file:///000/000979.doc")

        # 4. CSV export
        status_csv, content_csv = self._http_request("/csv?query=" + urllib.parse.quote("filename:000979.doc"))
        self.assertEqual(status_csv, 200)
        self.assertIn("file:///000/000979.doc", content_csv)
        self.assertNotIn("file:///data/000/000979.doc", content_csv)

    def test_search_results_filename_and_mime_labels(self):
        """Verify search results display full filename and descriptive filetype labels without raw mimetype."""
        # 1. Test Word Document (.doc)
        status_doc, html_doc = self._http_request("/results?query=" + urllib.parse.quote("filename:000979.doc"))
        self.assertEqual(status_doc, 200)
        self.assertIn('class="result-label result-label-filename"', html_doc)
        self.assertIn('>000979.doc<', html_doc)
        self.assertIn('class="result-label result-label-mtype"', html_doc)
        self.assertIn('>Word Document<', html_doc)
        self.assertNotIn('>Word Document (mime:application/msword)<', html_doc)

        # 2. Test PDF Document (.pdf)
        status_pdf, html_pdf = self._http_request("/results?query=" + urllib.parse.quote("filename:000.pdf"))
        self.assertEqual(status_pdf, 200)
        self.assertIn('class="result-label result-label-filename"', html_pdf)
        self.assertIn('>000.pdf<', html_pdf)
        self.assertIn('class="result-label result-label-mtype"', html_pdf)
        self.assertIn('>PDF Document<', html_pdf)
        self.assertNotIn('>PDF Document (mime:application/pdf)<', html_pdf)

        # 3. Test JSON search endpoint exposes mtype_label
        status_json, content_json = self._http_request("/json?query=" + urllib.parse.quote("filename:000979.doc"))
        self.assertEqual(status_json, 200)
        res_json = json.loads(content_json)
        self.assertEqual(len(res_json["results"]), 1)
        self.assertEqual(res_json["results"][0]["filename"], "000979.doc")
        self.assertEqual(res_json["results"][0]["mtype_label"], "Word Document")
        self.assertIn("size_human", res_json["results"][0])

    def test_size_label_rendered_after_filetype_and_no_pcbytes_tag(self):
        """Verify human-readable size is shown as a label after filetype and pcbytes is not shown as a tag."""
        status_html, html = self._http_request("/results?query=" + urllib.parse.quote("000"))
        self.assertEqual(status_html, 200)
        # Verify size label is rendered
        self.assertIn('class="result-label result-label-size"', html)
        # Verify order: result-label-mtype comes before result-label-size
        idx_mtype = html.find('class="result-label result-label-mtype"')
        idx_size = html.find('class="result-label result-label-size"')
        self.assertNotEqual(idx_mtype, -1)
        self.assertNotEqual(idx_size, -1)
        self.assertLess(idx_mtype, idx_size)
        # Verify pcbytes is not shown as a badge/tag under file preview
        self.assertNotIn('>pcbytes<', html)
        self.assertNotIn('Field: pcbytes', html)

        # Verify JSON search endpoint exposes size_human and excludes pcbytes from custom_metadata
        status_json, content_json = self._http_request("/json?query=" + urllib.parse.quote("000"))
        self.assertEqual(status_json, 200)
        res_json = json.loads(content_json)
        self.assertGreater(len(res_json["results"]), 0)
        first_res = res_json["results"][0]
        self.assertIn("size_human", first_res)
        self.assertTrue(len(first_res["size_human"]) > 0)
        self.assertNotIn("pcbytes", first_res.get("custom_metadata", {}))

        # Verify CSS contains .result-label-size rules
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".result-label-size", content_css)

    def test_query_fields_preserve_blue_color_on_focus(self):
        """Verify CSS preserves blue text color (#38bdf8) when editing query fields in form."""
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        # Verify base query field has blue text color
        self.assertIn(".form-control-query", content_css)
        self.assertIn("color: #38bdf8 !important;", content_css)
        # Verify focus state retains blue text color and does not change to #f8fafc
        self.assertNotIn("color: #f8fafc !important;", content_css)

    def test_static_form_collapses_empty_section_and_divider(self):
        """Verify CSS and JS collapse empty fields section and remove duplicate divider for static-only forms."""
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".advanced-search-panel.has-no-user-fields .advanced-fields-grid", content_css)
        self.assertIn("display: none !important;", content_css)
        self.assertIn(".advanced-search-panel.has-no-user-fields .advanced-bottom-bar", content_css)
        self.assertIn("border-top: none !important;", content_css)

        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("has-no-user-fields", content_js)

    def test_form_fields_enable_disable(self):
        """Verify enable/disable option for form fields and removal of Apple-style terminal dots."""
        form_data = {
            "name": "Field Toggle API Test Form",
            "description": "Form with enabled and disabled fields",
            "fields": [
                {
                    "id": "f_active",
                    "label": "Active Keyword",
                    "type": "text",
                    "enabled": True,
                    "query_format": "keyword:{value}"
                },
                {
                    "id": "f_inactive",
                    "label": "Disabled Tag",
                    "type": "text",
                    "enabled": False,
                    "query_format": "tag:{value}"
                }
            ]
        }

        # Test POST /api/forms saves enabled state
        status, content = self._http_request("/api/forms", method="POST", data=form_data)
        self.assertEqual(status, 200)
        resp = json.loads(content)
        self.assertTrue(resp.get("success"))
        saved = resp.get("form", {})
        self.assertTrue(saved["fields"][0]["enabled"])
        self.assertFalse(saved["fields"][1]["enabled"])
        created_id = saved.get("id")

        # Test GET /api/forms returns enabled state
        status, content_forms = self._http_request("/api/forms", method="GET")
        self.assertEqual(status, 200)
        forms_data = json.loads(content_forms)
        forms = forms_data.get("forms", forms_data) if isinstance(forms_data, dict) else forms_data
        match = next(f for f in forms if f["id"] == created_id)
        self.assertTrue(match["fields"][0]["enabled"])
        self.assertFalse(match["fields"][1]["enabled"])

        # Check CSS contains disabled card style and switch layout
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".builder-field-card.is-disabled", content_css)
        self.assertIn(".builder-field-header-left", content_css)
        self.assertIn(".terminal-body::-webkit-scrollbar", content_css)
        self.assertIn(".terminal-body::-webkit-scrollbar-thumb", content_css)

        # Check JS contains toggle handling and enabled checks
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("field-enabled-toggle", content_js)
        self.assertIn("field.enabled === false", content_js)

        # Check index_manager HTML removes Apple-style window decorations (terminal-controls / terminal-dot)
        status_im, content_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertNotIn("terminal-controls", content_im)
        self.assertNotIn("terminal-dot", content_im)

        # Clean up
        self._http_request("/api/forms/delete", method="POST", data={"id": created_id})

    def test_keyword_aliases_and_removed_keywords_suggestions(self):
        """Verify fn, cfn, and fileextension are removed from TOP_LEVEL_KEYWORDS but their canonical keywords match aliases."""
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)

        # Extract TOP_LEVEL_KEYWORDS block
        self.assertIn("const TOP_LEVEL_KEYWORDS = [", content_js)
        start_idx = content_js.index("const TOP_LEVEL_KEYWORDS = [")
        end_idx = content_js.index("];", start_idx)
        top_kw_block = content_js[start_idx:end_idx]

        # 1. fn:, cfn:, fileextension:, mimetype:, contenttype:, mtype: must NOT be standalone entries in TOP_LEVEL_KEYWORDS
        self.assertNotIn("prefix: 'fn:'", top_kw_block)
        self.assertNotIn("prefix: 'cfn:'", top_kw_block)
        self.assertNotIn("prefix: 'fileextension:'", top_kw_block)
        self.assertNotIn("prefix: 'mimetype:'", top_kw_block)
        self.assertNotIn("prefix: 'contenttype:'", top_kw_block)
        self.assertNotIn("prefix: 'mtype:'", top_kw_block)

        # 2. Canonical keywords must have aliases mapped
        self.assertIn("prefix: 'filename:'", top_kw_block)
        self.assertIn("aliases: ['fn']", top_kw_block)

        self.assertIn("prefix: 'containerfilename:'", top_kw_block)
        self.assertIn("aliases: ['cfn']", top_kw_block)

        self.assertIn("prefix: 'ext:'", top_kw_block)
        self.assertIn("aliases: ['fileextension']", top_kw_block)

        self.assertIn("prefix: 'mime:'", top_kw_block)
        self.assertIn("aliases: ['mimetype', 'mtype', 'contenttype']", top_kw_block)

        self.assertIn("prefix: 'filetype:'", top_kw_block)
        self.assertIn("aliases: ['mimetype', 'mtype', 'contenttype']", top_kw_block)

        # 3. scoreKeywordItem must handle aliases
        self.assertIn("item.aliases", content_js)
        self.assertIn("alias === cleanQ", content_js)

        # 4. Secondary mimePrefixes must recognize mimetype, mtype, contenttype
        self.assertIn("const mimePrefixes = ['mime:', 'filetype:', 'mimetype:', 'mtype:', 'contenttype:'];", content_js)

    def test_full_form_enable_disable_toggle(self):
        """Verify full form enable/disable toggle API, persistence, CSS matching index page, and JS."""
        # 1. Create a custom form to toggle
        form_payload = {
            "name": "Toggle Form Test",
            "description": "Form for testing full form enable/disable toggle",
            "fields": [
                {
                    "id": "f1",
                    "label": "Topic",
                    "type": "text",
                    "query_format": "subject:{value}"
                }
            ]
        }
        status, content = self._http_request("/api/forms", method="POST", data=form_payload)
        self.assertEqual(status, 200)
        resp = json.loads(content)
        self.assertTrue(resp.get("success"))
        created_id = resp["form"]["id"]

        # 2. Toggle form to disabled via POST /api/forms/toggle
        status, content_toggle = self._http_request("/api/forms/toggle", method="POST", data={"id": created_id, "enabled": False})
        self.assertEqual(status, 200)
        resp_toggle = json.loads(content_toggle)
        self.assertTrue(resp_toggle.get("success"))
        self.assertFalse(resp_toggle["form"]["enabled"])

        # Verify /api/forms returns it as disabled
        status, content_get = self._http_request("/api/forms", method="GET")
        self.assertEqual(status, 200)
        forms = json.loads(content_get).get("forms", [])
        matched = next(f for f in forms if f["id"] == created_id)
        self.assertFalse(matched["enabled"])

        # 3. Toggle form back to enabled
        status, content_toggle_on = self._http_request("/api/forms/toggle", method="POST", data={"id": created_id, "enabled": True})
        self.assertEqual(status, 200)
        resp_toggle_on = json.loads(content_toggle_on)
        self.assertTrue(resp_toggle_on.get("success"))
        self.assertTrue(resp_toggle_on["form"]["enabled"])

        # 4. Verify CSS styling matches exact look & feel from index page
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".form-manage-card.is-disabled", content_css)
        self.assertIn(".form-card-identity", content_css)
        self.assertIn("opacity: 0.55;", content_css)
        self.assertIn("filter: grayscale(0.5);", content_css)

        # 5. Verify JS contains form toggle handler and API call
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("form-enabled-toggle", content_js)
        self.assertIn("/api/forms/toggle", content_js)

        # Clean up
        self._http_request("/api/forms/delete", method="POST", data={"id": created_id})

    def test_footer_index_status_and_themed_dialogs(self):
        """Verify footer index badge reflecting actual status and themed dialog modal markup."""
        # 1. Root page has footer badge and app dialog overlay
        status_root, html_root = self._http_request("/")
        self.assertEqual(status_root, 200)
        self.assertIn('id="footer-index-badge"', html_root)
        self.assertIn('id="app-dialog-overlay"', html_root)
        self.assertIn('id="app-dialog-title"', html_root)
        self.assertIn('id="app-dialog-message"', html_root)
        self.assertIn('id="btn-confirm-app-dialog"', html_root)
        self.assertIn('id="btn-cancel-app-dialog"', html_root)

        # 2. Index manager page also has footer badge and app dialog overlay
        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertIn('id="footer-index-badge"', html_im)
        self.assertIn('id="app-dialog-overlay"', html_im)

        # 3. Settings page also has footer badge and app dialog overlay
        status_set, html_set = self._http_request("/settings")
        self.assertEqual(status_set, 200)
        self.assertIn('id="footer-index-badge"', html_set)
        self.assertIn('id="app-dialog-overlay"', html_set)

        # 4. Verify CSS styling contains status variants and dialog styles
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".security-badge.status-ready", content_css)
        self.assertIn(".security-badge.status-indexing", content_css)
        self.assertIn(".security-badge.status-empty", content_css)
        self.assertIn(".security-badge.status-error", content_css)
        self.assertIn(".confirm-modal-dialog", content_css)
        self.assertIn(".btn-danger", content_css)

        # 5. Verify JS contains modal dialog functions and footer status updater
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("window.showConfirmModal", content_js)
        self.assertIn("window.showAlertModal", content_js)
        self.assertIn("window.updateFooterIndexBadge", content_js)
        self.assertIn("initFooterIndexStatus", content_js)

        # 6. Verify index_manager.tpl uses custom modals instead of native confirm/alert
        self.assertIn("window.showConfirmModal", html_im)
        self.assertNotIn("confirm(", html_im)

    def test_form_field_value_wildcard_suggestions(self):
        """Verify form field suggestions provide *{value}* along with {value} for all keywords."""
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)

        # Check TEXT_SNIPPET_PATTERNS contains both {value} and *{value}*
        self.assertIn("const TEXT_SNIPPET_PATTERNS = [", content_js)
        self.assertIn("prefix: '{value}'", content_js)
        self.assertIn("prefix: '*{value}*'", content_js)

        # Verify keyword pairs exist for exact and wildcard partial matching
        keyword_pairs = [
            ("filename:{value}", "filename:*{value}*"),
            ("title:{value}", "title:*{value}*"),
            ("author:{value}", "author:*{value}*"),
            ("subject:{value}", "subject:*{value}*"),
            ("ext:{value}", "ext:*{value}*"),
            ("mime:{value}", "mime:*{value}*"),
            ("filetype:{value}", "filetype:*{value}*"),
            ("tag:{value}", "tag:*{value}*"),
            ("keyword:{value}", "keyword:*{value}*"),
            ("from:{value}", "from:*{value}*"),
            ("to:{value}", "to:*{value}*"),
            ("recipient:{value}", "recipient:*{value}*"),
        ]
        for exact_kw, wild_kw in keyword_pairs:
            self.assertIn(f"prefix: '{exact_kw}'", content_js)
            self.assertIn(f"prefix: '{wild_kw}'", content_js)

        # Verify highlightQuerySyntax handles *{value}* with {value} placeholder and separate wildcard operator coloring
        self.assertIn("(\\{value\\})", content_js)

    def test_bugfixes_search_proximity_and_sandbox_persistence(self):
        """Verify the 4 reported bugfixes:
        1. User editing search field collapses advanced search on submit
        2. Wildcards around {value} are styled as operators
        3. Proximity operator is pN with N placeholder
        4. Sandbox sample path is saved across session
        """
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)

        # 1. Advanced search collapses when main query was edited
        self.assertIn("userEditedMainQuery", content_js)
        self.assertIn("recoll_adv_open", content_js)

        # 2. Syntax highlighting separates {value} from wildcards
        self.assertIn("(\\{value\\})", content_js)

        # 3. Proximity search is pN and oN with N colored as placeholder
        self.assertIn("prefix: 'pN'", content_js)
        self.assertIn("placeholder: 'N'", content_js)
        self.assertIn("prefix: '\"{value}\"pN'", content_js)
        self.assertIn("prefix: 'oN'", content_js)
        self.assertIn("prefix: '\"{value}\"oN'", content_js)
        self.assertIn('<span class="param-placeholder">N</span>', content_js)

        # 4. Sandbox session persistence in index-manager
        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertIn("recoll_sandbox_sample_path", html_im)
        self.assertIn("safeSessionGet", html_im)
        self.assertIn("safeSessionSet", html_im)

    def test_four_index_status_states_and_colors(self):
        """Verify the 4 required index status labels and their respective color styling:
        - No index (red)
        - Creating Index (orange)
        - Updating Index (blue)
        - Index Ready (green)
        """
        # 1. Check style.css contains class definitions and color rules for all 4 states
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)

        # Red styling for No index
        self.assertIn(".index-status-pill.is-no-index", content_css)
        self.assertIn(".security-badge.status-no-index", content_css)

        # Orange styling for Creating Index
        self.assertIn(".index-status-pill.is-creating", content_css)
        self.assertIn(".security-badge.status-creating", content_css)
        self.assertIn("pulseGlowOrange", content_css)

        # Blue styling for Updating Index
        self.assertIn(".index-status-pill.is-updating", content_css)
        self.assertIn(".security-badge.status-updating", content_css)

        # Green styling for Index Ready
        self.assertIn(".index-status-pill.is-ready", content_css)
        self.assertIn(".security-badge.status-ready", content_css)

        # 2. Check extra.js handles all 4 states with exact labels
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("'No index'", content_js)
        self.assertIn("'Creating Index'", content_js)
        self.assertIn("'Updating Index'", content_js)
        self.assertIn("'Index Ready'", content_js)

        # 3. Check index_manager.tpl renders and updates with the 4 status labels
        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertIn("Creating Index", html_im)
        self.assertIn("Updating Index", html_im)
        self.assertIn("No index", html_im)
        self.assertIn("Index Ready", html_im)

    def test_dynamic_index_action_button(self):
        """Verify the dynamic index action button:
        - Replaces separate incremental and full buttons with single button
        - Titled 'Create Index' when no index exists, 'Update Index' when index exists
        - Disabled while creating or updating
        """
        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)

        # 1. Old buttons removed, new dynamic button present
        self.assertNotIn("btn-incremental-index", html_im)
        self.assertNotIn("btn-full-reindex", html_im)
        self.assertIn('id="btn-index-action"', html_im)
        self.assertIn("triggerIndexAction()", html_im)

        # 2. Check CSS contains disabled styling for buttons
        status_css, content_css = self._http_request("/static/style.css")
        self.assertEqual(status_css, 200)
        self.assertIn(".btn:disabled", content_css)

        # 3. Check client-side fetchIndexStatus toggles 'Create Index' vs 'Update Index' and disabled state
        self.assertIn("btnText.innerText = 'Create Index'", html_im)
        self.assertIn("btnText.innerText = 'Update Index'", html_im)
        self.assertIn("btnAction.disabled = isRunning", html_im)

        # 4. Refresh button and old toolbar removed, buttons aligned next to Database Metrics
        self.assertNotIn("btn-icon-spin", html_im)
        self.assertNotIn("Refresh</span>", html_im)
        self.assertIn('class="section-title-actions"', html_im)

    def test_webui_startup_and_availability_without_index(self):
        """Verify Web UI and endpoints are available without an index, and entrypoint does not block."""
        # 1. Verify entrypoint.sh does not run blocking recollindex
        if os.path.exists("entrypoint.sh"):
            with open("entrypoint.sh", "r", encoding="utf-8") as f:
                entrypoint_content = f.read()
            self.assertNotIn("recollindex -z", entrypoint_content)
            self.assertIn("No search index found", entrypoint_content)
        elif os.path.exists("/app/entrypoint.sh"):
            with open("/app/entrypoint.sh", "r", encoding="utf-8") as f:
                entrypoint_content = f.read()
            self.assertNotIn("recollindex -z", entrypoint_content)
            self.assertIn("No search index found", entrypoint_content)

        # 2. Verify root page and index manager load with 200 OK
        status_root, html_root = self._http_request("/")
        self.assertEqual(status_root, 200)
        self.assertIn("Recoll", html_root)

        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertIn("Index Management", html_im)

    def test_uniform_save_and_leave_guard(self):
        """Verify uniform save behavior, no inline green messages, bottom-right toast, and leave guard save button."""
        # 1. Verify Save & Leave button in app dialog footer across pages
        for path in ["/", "/index-manager", "/settings"]:
            status, html = self._http_request(path)
            self.assertEqual(status, 200)
            self.assertIn('id="btn-save-app-dialog"', html)

        # 2. Verify /set endpoint supports AJAX JSON response
        post_data = urllib.parse.urlencode({"stem": "1", "perpage": "25", "ajax": "1"}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/set",
            data=post_data,
            headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(body.get("success"))

        # 3. Verify static/extra.js contains dirty checking and save preferences functions
        status_js, content_js = self._http_request("/static/extra.js")
        self.assertEqual(status_js, 200)
        self.assertIn("window.saveSettingsPreferences", content_js)
        self.assertIn("window.checkSettingsDirty", content_js)
        self.assertIn("window.checkIndexConfigDirty", content_js)
        self.assertIn("btn-save-app-dialog", content_js)
        self.assertIn("saveText || 'Save & Leave'", content_js)
        self.assertIn("showSaveButton", content_js)
        self.assertIn("showToast('Preferences saved successfully!'", content_js)

        # 4. Verify index_manager.tpl removes inline green success messages and shows toast
        status_im, html_im = self._http_request("/index-manager")
        self.assertEqual(status_im, 200)
        self.assertNotIn("statusMsg.innerText = 'Configuration and rules saved successfully!'", html_im)
        self.assertIn("showToast('Configuration and rules saved successfully!'", html_im)
        self.assertIn("window.updateRulesDirtyState", html_im)


if __name__ == "__main__":
    unittest.main()

