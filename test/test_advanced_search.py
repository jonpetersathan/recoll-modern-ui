#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Search and Custom Search Forms.
Verifies form persistence, read-only protection, field compilation,
REST API endpoints, and container restart survival.
"""

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
        self.assertGreaterEqual(len(forms), 2)
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

    def test_query_compilation(self):
        """Verify query compiler generates correct Recoll query strings."""
        try:
            from webui import SearchFormsManager, DEFAULT_SEARCH_FORM, SAMPLE_CUSTOM_FORM
        except ImportError:
            self.skipTest("webui cannot be imported in host python")

        # Compile default form
        default_values = {
            "all_terms": "system performance",
            "exact_phrase": "neural network",
            "any_terms": "gpu tpu",
            "none_terms": "deprecated draft",
            "proximity_terms": "cache memory",
            "filename": "*.pdf",
            "title": "Quarterly Report",
            "author": "Alice Smith",
            "filetype": "mime:application/pdf",
            "size_min": "10k",
            "size_max": "50m",
            "dir_scope": "/data/reports"
        }
        compiled = SearchFormsManager.compile_query(DEFAULT_SEARCH_FORM, default_values)
        self.assertIn("system performance", compiled)
        self.assertIn('"neural network"', compiled)
        self.assertIn("(gpu OR tpu)", compiled)
        self.assertIn("-deprecated -draft", compiled)
        self.assertIn('"cache memory"p4', compiled)
        self.assertIn("filename:*.pdf", compiled)
        self.assertIn('title:"Quarterly Report"', compiled)
        self.assertIn('author:"Alice Smith"', compiled)
        self.assertIn("mime:application/pdf", compiled)
        self.assertIn("size>10k", compiled)
        self.assertIn("size<50m", compiled)
        self.assertIn('dir:"/data/reports"', compiled)

        # Compile custom form with dropdown
        custom_values = {
            "document_type": "filename:*000*",
            "keywords": "specification",
            "doc_title": "Summary"
        }
        compiled_custom = SearchFormsManager.compile_query(SAMPLE_CUSTOM_FORM, custom_values)
        self.assertEqual(compiled_custom, "filename:*000* specification title:Summary")


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


if __name__ == "__main__":
    unittest.main()
