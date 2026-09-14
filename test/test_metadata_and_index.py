#!/usr/bin/env python3
"""
Unit tests for MetadataRulesManager, IndexManager, and Extractor CLI.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# Ensure src is in sys.path
for candidate in ["/app/src", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from recollweb.indexer import IndexManager
from recollweb.metadata import (
    DEFAULT_EXTRACTOR_PATH,
    MetadataRulesManager,
    evaluate_rules_in_memory,
    matches_glob,
    sanitize_field_name,
)


class TestMetadataRulesManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="recoll_test_meta_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitize_field_name(self):
        self.assertEqual(sanitize_field_name("Project-Name"), "project_name")
        self.assertEqual(sanitize_field_name("DocType 123!"), "doctype_123_")
        self.assertEqual(sanitize_field_name("author"), "author")
        self.assertEqual(sanitize_field_name("date@YYYYMMDD"), "date@YYYYMMDD")
        self.assertEqual(sanitize_field_name("date@year"), "date@year")

    def test_date_directives_delimiter_and_regex(self):
        rules = [
            {
                "id": "r_date_delim",
                "name": "Date Delim",
                "enabled": True,
                "type": "delimiter",
                "delimiter": "_",
                "target": "stem",
                "mappings": [
                    {"index": 0, "field": "doctype"},
                    {"index": 1, "field": "date@YYYYMMDD"},
                    {"index": 2, "field": "title"},
                ],
            }
        ]
        res = evaluate_rules_in_memory(rules, "/data/invoices/INV_20230514_AnnualReport.pdf")
        self.assertEqual(res.get("doctype"), "INV")
        self.assertEqual(res.get("title"), "AnnualReport")
        self.assertEqual(res.get("modificationdate"), "1684022400")
        self.assertNotIn("date@YYYYMMDD", res)

        rules_regex = [
            {
                "id": "r_date_regex",
                "name": "Date Regex",
                "enabled": True,
                "type": "regex",
                "pattern": r".*/invoices/(?P<doctype>[^_]+)_(?P<date_yyyymmdd>\d{8})_(?P<title>[^.]+)\.pdf",
            }
        ]
        res_regex = evaluate_rules_in_memory(rules_regex, "/data/invoices/INV_20230514_AnnualReport.pdf")
        self.assertEqual(res_regex.get("modificationdate"), "1684022400")

    def test_glob_matching(self):
        self.assertTrue(matches_glob("*.pdf", "/data/docs/file.pdf"))
        self.assertTrue(matches_glob("**/*.pdf", "/data/docs/file.pdf"))
        self.assertTrue(matches_glob("/data/projects/**", "/data/projects/alpha/doc.txt"))
        self.assertFalse(matches_glob("/data/invoices/**", "/data/projects/alpha/doc.txt"))
        self.assertTrue(matches_glob("", "/any/path.txt"))

    def test_depth_rule_evaluation(self):
        rules = [
            {
                "id": "r1",
                "name": "Project Depth",
                "enabled": True,
                "type": "depth",
                "depth": 2,  # 0:data, 1:projects, 2:Apollo
                "field": "project",
            },
            {
                "id": "r2",
                "name": "Parent Folder",
                "enabled": True,
                "type": "depth",
                "depth": -2,
                "field": "folder",
            },
        ]
        res = evaluate_rules_in_memory(rules, "/data/projects/Apollo/invoices/doc.pdf")
        self.assertEqual(res.get("project"), "Apollo")
        self.assertEqual(res.get("folder"), "invoices")

    def test_delimiter_rule_evaluation(self):
        rules = [
            {
                "id": "r_delim",
                "name": "Invoice Delim",
                "enabled": True,
                "type": "delimiter",
                "delimiter": "_",
                "target": "stem",
                "mappings": [
                    {"index": 0, "field": "doctype"},
                    {"index": 1, "field": "year"},
                    {"index": 2, "field": "inv_id"},
                ],
            }
        ]
        res = evaluate_rules_in_memory(rules, "/data/invoices/INV_2026_0042.pdf")
        self.assertEqual(res.get("doctype"), "INV")
        self.assertEqual(res.get("year"), "2026")
        self.assertEqual(res.get("inv_id"), "0042")

    def test_regex_rule_evaluation(self):
        rules = [
            {
                "id": "r_regex",
                "name": "Project Regex",
                "enabled": True,
                "type": "regex",
                "pattern": r".*/projects/(?P<project>[^/]+)/(?P<year>\d{4})/(?P<client>[^_]+)_(?P<title>[^.]+)\.pdf",
            }
        ]
        res = evaluate_rules_in_memory(rules, "/data/projects/Titan/2026/Globex_Agreement.pdf")
        self.assertEqual(res.get("project"), "Titan")
        self.assertEqual(res.get("year"), "2026")
        self.assertEqual(res.get("client"), "Globex")
        self.assertEqual(res.get("title"), "Agreement")

    def test_rule_validation(self):
        valid_rules = {
            "rules": [
                {"id": "r1", "type": "depth", "depth": 2, "field": "project"},
                {"id": "r2", "type": "regex", "pattern": r".*/(?P<doc_id>\d+)\.pdf"},
            ]
        }
        errors = MetadataRulesManager.validate_rules(valid_rules)
        self.assertEqual(len(errors), 0)

        invalid_rules = {
            "rules": [
                {"id": "bad1", "type": "depth", "field": ""},
                {"id": "bad2", "type": "regex", "pattern": r"no named groups here"},
                {"id": "bad3", "type": "unknown_type"},
            ]
        }
        errors = MetadataRulesManager.validate_rules(invalid_rules)
        self.assertEqual(len(errors), 3)

    def test_save_and_recoll_sync(self):
        # Create dummy recoll.conf and fields
        recoll_conf = os.path.join(self.temp_dir, "recoll.conf")
        with open(recoll_conf, "w", encoding="utf-8") as f:
            f.write("topdirs = /data\nloglevel = 1\n")

        fields_conf = os.path.join(self.temp_dir, "fields")
        with open(fields_conf, "w", encoding="utf-8") as f:
            f.write("[prefixes]\nauthor = XSFN\n[stored]\nauthor = \n")

        rules_payload = {
            "rules": [
                {"id": "r1", "enabled": True, "type": "depth", "depth": 2, "field": "project"},
                {"id": "r2", "enabled": True, "type": "regex", "pattern": r".*/(?P<department>[^/]+)/.*"},
            ]
        }

        saved = MetadataRulesManager.save_rules(self.temp_dir, rules_payload)
        self.assertIn("rules", saved)

        # Check recoll.conf updated with metadatacmds
        with open(recoll_conf, "r", encoding="utf-8") as f:
            conf_content = f.read()
        self.assertIn("metadatacmds", conf_content)
        self.assertIn("rclmulti1", conf_content)

        # Check fields updated with [prefixes] and [stored]
        with open(fields_conf, "r", encoding="utf-8") as f:
            fields_content = f.read()
        self.assertIn("project = XSFNPROJECT", fields_content)
        self.assertIn("department = XSFNDEPARTMENT", fields_content)
        self.assertIn("project = ", fields_content)
        self.assertIn("department = ", fields_content)

        # Check get_extracted_fields
        fields = MetadataRulesManager.get_extracted_fields(self.temp_dir)
        self.assertIn("project", fields)
        self.assertIn("department", fields)


class TestIndexManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="recoll_test_idx_")
        IndexManager.reset_data_size_cache()

    def tearDown(self):
        IndexManager.reset_data_size_cache()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_bytes(self):
        self.assertEqual(IndexManager._format_bytes(500), "500.0 B")
        self.assertEqual(IndexManager._format_bytes(2048), "2.0 KB")
        self.assertEqual(IndexManager._format_bytes(1048576 * 5), "5.0 MB")

    def test_get_status_idle(self):
        # Create recoll.conf with topdirs
        recoll_conf = os.path.join(self.temp_dir, "recoll.conf")
        with open(recoll_conf, "w", encoding="utf-8") as f:
            f.write("topdirs = /data /custom_docs\n")

        status = IndexManager.get_status(self.temp_dir)
        self.assertIn("status", status)
        self.assertIn("topdirs", status)
        self.assertIn("data_size_human", status)
        self.assertIn("data_size_bytes", status)
        self.assertIn("data_size_calculating", status)
        self.assertEqual(status["topdirs"], ["/data", "/custom_docs"])
        self.assertFalse(status["exists"])

    def test_purge_index(self):
        xapian_dir = os.path.join(self.temp_dir, "xapiandb")
        os.makedirs(xapian_dir, exist_ok=True)
        dummy_file = os.path.join(xapian_dir, "flintlock")
        with open(dummy_file, "w") as f:
            f.write("lock")

        self.assertTrue(os.path.isdir(xapian_dir))
        res = IndexManager.purge_index(self.temp_dir)
        self.assertTrue(res["success"])
        self.assertFalse(os.path.isdir(xapian_dir))

    def test_cached_data_size_sqlite_persistence(self):
        from recollweb.db import set_global_setting
        set_global_setting(self.temp_dir, "cached_data_size_bytes", "10485760")
        set_global_setting(self.temp_dir, "cached_data_size_time", "2026-09-14 12:00")

        size_info = IndexManager.get_cached_data_size(self.temp_dir)
        self.assertEqual(size_info["bytes"], 10485760)
        self.assertEqual(size_info["human"], "10.0 MB")
        self.assertEqual(size_info["updated_at"], "2026-09-14 12:00")
        self.assertFalse(size_info["calculating"])

    def test_async_data_size_calculation_and_caching(self):
        sample_dir = os.path.join(self.temp_dir, "data_sample")
        os.makedirs(sample_dir, exist_ok=True)
        with open(os.path.join(sample_dir, "test.txt"), "wb") as f:
            f.write(b"0" * 4096)

        recoll_conf = os.path.join(self.temp_dir, "recoll.conf")
        with open(recoll_conf, "w", encoding="utf-8") as f:
            f.write(f"topdirs = {sample_dir}\n")

        # Trigger calculation
        started = IndexManager.trigger_data_size_calculation(self.temp_dir, force=True)
        self.assertTrue(started)

        # Worker runs in thread - wait briefly for completion
        import time
        for _ in range(50):
            time.sleep(0.05)
            size_info = IndexManager.get_cached_data_size(self.temp_dir)
            if not size_info["calculating"] and size_info["bytes"] > 0:
                break

        if IndexManager._data_size_thread and IndexManager._data_size_thread.is_alive():
            IndexManager._data_size_thread.join(timeout=2.0)

        size_info = IndexManager.get_cached_data_size(self.temp_dir)
        self.assertGreaterEqual(size_info["bytes"], 4096)
        self.assertFalse(size_info["calculating"])
        self.assertIsNotNone(size_info["updated_at"])

    def test_get_and_update_index_config(self):
        recoll_conf = os.path.join(self.temp_dir, "recoll.conf")
        with open(recoll_conf, "w", encoding="utf-8") as f:
            f.write(
                "topdirs = /data\n"
                "skippedNames = *.bak *.log\n"
                "excludedmimetypes = text/x-log application/octet-stream\n"
                "idxthreads = 3\n"
                "pdfocrmode = auto\n"
                "idxflushmb = 80\n"
            )

        conf = IndexManager.get_index_config(self.temp_dir)
        self.assertEqual(conf["skippedNames"], ["*.bak", "*.log"])
        self.assertEqual(conf["excludedmimetypes"], ["text/x-log", "application/octet-stream"])
        self.assertEqual(conf["idxthreads"], 3)
        self.assertEqual(conf["pdfocrmode"], "auto")
        self.assertEqual(conf["idxflushmb"], 80)
        self.assertTrue(conf["indexallfilenames"])

        # Update config
        updates = {
            "skippedNames": ["*.bak", "*.iso", "*.tmp"],
            "excludedmimetypes": ["text/x-log", "application/pdf", "text/x-log", "image/*"],
            "idxthreads": 6,
            "pdfocrmode": "always",
            "noaspell": True,
            "thrQSlices": "3",
            "idxabsml": 400
        }
        updated = IndexManager.update_index_config(self.temp_dir, updates)
        self.assertEqual(updated["skippedNames"], ["*.bak", "*.iso", "*.tmp"])
        # Deduplication should preserve insertion order and keep slashes
        self.assertEqual(updated["excludedmimetypes"], ["text/x-log", "application/pdf", "image/*"])
        self.assertEqual(updated["idxthreads"], 6)
        self.assertEqual(updated["pdfocrmode"], "always")
        self.assertTrue(updated["noaspell"])
        self.assertEqual(updated["thrQSlices"], "3")
        self.assertEqual(updated["idxabsml"], 400)

        # Re-read to confirm persistence
        persisted = IndexManager.get_index_config(self.temp_dir)
        self.assertEqual(persisted["skippedNames"], ["*.bak", "*.iso", "*.tmp"])
        self.assertEqual(persisted["excludedmimetypes"], ["text/x-log", "application/pdf", "image/*"])
        self.assertEqual(persisted["idxthreads"], 6)
        self.assertEqual(persisted["pdfocrmode"], "always")
        self.assertTrue(persisted["noaspell"])

        # Test invalid excludedmimetypes error
        with self.assertRaises(ValueError):
            IndexManager.update_index_config(self.temp_dir, {"excludedmimetypes": ["text/plain\nmalicious = true"]})


class TestExtractorCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="recoll_test_cli_")
        self.rules_file = os.path.join(self.temp_dir, "metadata_rules.json")
        rules = {
            "rules": [
                {
                    "id": "cli_r1",
                    "enabled": True,
                    "type": "delimiter",
                    "delimiter": "_",
                    "target": "stem",
                    "mappings": [
                        {"index": 0, "field": "doctype"},
                        {"index": 1, "field": "year"},
                    ],
                }
            ]
        }
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(rules, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_cli_cmd(self, extra_args):
        candidates = [
            "/usr/local/bin/recoll-metadata-extractor",
            "/app/src/recollweb/extractor_cli.py",
            os.path.abspath(os.path.join(os.path.dirname(__file__ if '__file__' in globals() else '.'), "..", "src", "recollweb", "extractor_cli.py")),
        ]
        chosen = next((c for c in candidates if os.path.isfile(c)), None)
        if not chosen:
            self.skipTest("No CLI candidate found")
        if chosen.endswith('.py'):
            return [sys.executable, chosen] + extra_args
        return [chosen] + extra_args

    def test_cli_execution_normal(self):
        cmd = self._get_cli_cmd([
            "--config",
            self.rules_file,
            "/data/invoices/DOC_2025_report.pdf",
        ])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip().splitlines()
        self.assertIn("doctype = DOC", output)
        self.assertIn("year = 2025", output)

    def test_cli_execution_test_json(self):
        cmd = self._get_cli_cmd([
            "--config",
            self.rules_file,
            "--test",
            "/data/invoices/DOC_2025_report.pdf",
        ])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout.strip())
        self.assertEqual(data.get("doctype"), "DOC")
        self.assertEqual(data.get("year"), "2025")


if __name__ == "__main__":
    unittest.main()
