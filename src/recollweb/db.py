"""
SQLite database persistence for Recoll Modern UI (recoll-web.db).
Replaces cookie-based user settings and JSON config files with relational tables
supporting multi-user scoping, global defaults, and per-user form toggles.
"""

import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional

_db_locks: Dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def get_db_path(conf_dir: str) -> str:
    """Return canonical path to recoll-web.db inside conf_dir and ensure symlink."""
    db_path = os.path.join(conf_dir, "recoll-web.db")
    alt_path = os.path.join(conf_dir, "recoll-web")
    # Maintain symlink recoll-web -> recoll-web.db if missing
    try:
        if not os.path.exists(alt_path) and not os.path.islink(alt_path):
            os.symlink("recoll-web.db", alt_path)
    except Exception:
        pass
    return db_path


def get_db_lock(db_path: str) -> threading.Lock:
    """Get thread lock for specific database file."""
    with _locks_lock:
        if db_path not in _db_locks:
            _db_locks[db_path] = threading.Lock()
        return _db_locks[db_path]


def get_db_connection(conf_dir: str) -> sqlite3.Connection:
    """Open SQLite connection with row factory and WAL mode."""
    db_path = get_db_path(conf_dir)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(conf_dir: str) -> None:
    """
    Initialize SQLite database schema and migrate legacy JSON configs if present.
    """
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS global_settings (
                        setting_key TEXT PRIMARY KEY,
                        setting_value TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        username TEXT,
                        setting_key TEXT,
                        setting_value TEXT,
                        PRIMARY KEY (username, setting_key)
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS custom_forms (
                        form_id TEXT PRIMARY KEY,
                        title TEXT,
                        is_global INTEGER DEFAULT 0,
                        owner_user TEXT DEFAULT 'default',
                        form_json TEXT,
                        created_at TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_form_states (
                        username TEXT,
                        form_id TEXT,
                        enabled INTEGER DEFAULT 1,
                        PRIMARY KEY (username, form_id)
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metadata_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_json TEXT,
                        sort_order INTEGER DEFAULT 0
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS extractor_config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """)

            # Run initial migration from legacy json files if database tables are empty
            _migrate_legacy_json_if_needed(conn, conf_dir)
        finally:
            conn.close()


def _migrate_legacy_json_if_needed(conn: sqlite3.Connection, conf_dir: str) -> None:
    """Migrate legacy metadata_rules.json and forms.json into SQLite tables."""
    cur = conn.cursor()
    # 1. Migrate metadata_rules.json
    cur.execute("SELECT setting_value FROM global_settings WHERE setting_key = 'migrated_rules';")
    if not cur.fetchone():
        rules_file = os.path.join(conf_dir, "metadata_rules.json")
        if os.path.isfile(rules_file):
            try:
                with open(rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rules = data.get("rules", [])
                ext_path = data.get("extractor_path")
                with conn:
                    for idx, r in enumerate(rules):
                        r_id = r.get("id") or f"rule_{idx}"
                        conn.execute(
                            "INSERT OR REPLACE INTO metadata_rules (rule_id, rule_json, sort_order) VALUES (?, ?, ?)",
                            (r_id, json.dumps(r), idx)
                        )
                    if ext_path:
                        conn.execute(
                            "INSERT OR REPLACE INTO extractor_config (key, value) VALUES ('extractor_path', ?)",
                            (ext_path,)
                        )
            except Exception:
                pass
        with conn:
            conn.execute("INSERT OR REPLACE INTO global_settings (setting_key, setting_value) VALUES ('migrated_rules', '1');")

    # 2. Migrate forms.json
    cur.execute("SELECT setting_value FROM global_settings WHERE setting_key = 'migrated_forms';")
    if not cur.fetchone():
        forms_file = os.path.join(conf_dir, "forms.json")
        if os.path.isfile(forms_file):
            try:
                with open(forms_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                forms = data if isinstance(data, list) else data.get("forms", [])
                with conn:
                    for f_obj in forms:
                        if not isinstance(f_obj, dict):
                            continue
                        f_id = f_obj.get("id", "")
                        title = f_obj.get("name") or f_obj.get("title") or f_id
                        # Skip sample custom forms
                        if f_id in ("sample", "sample_form") or "sample" in str(f_id).lower():
                            continue
                        if "sample" in str(title).lower():
                            continue
                        conn.execute(
                            "INSERT OR REPLACE INTO custom_forms (form_id, title, is_global, owner_user, form_json, created_at) "
                            "VALUES (?, ?, 1, 'default', ?, datetime('now'))",
                            (f_id, title, json.dumps(f_obj))
                        )
            except Exception:
                pass
        with conn:
            conn.execute("INSERT OR REPLACE INTO global_settings (setting_key, setting_value) VALUES ('migrated_forms', '1');")


# ---------------------------------------------------------------------------
# Settings CRUD
# ---------------------------------------------------------------------------

def get_setting(conf_dir: str, username: str, key: str, default: Any = None) -> Any:
    """Retrieve setting with fallback: user-specific -> global default -> default."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            if username:
                cur.execute(
                    "SELECT setting_value FROM user_settings WHERE username = ? AND setting_key = ?",
                    (username, key)
                )
                row = cur.fetchone()
                if row is not None:
                    return row["setting_value"]

            cur.execute(
                "SELECT setting_value FROM global_settings WHERE setting_key = ?",
                (key,)
            )
            row = cur.fetchone()
            if row is not None:
                return row["setting_value"]

            return default
        finally:
            conn.close()


def get_user_setting(conf_dir: str, username: str, key: str) -> Optional[str]:
    """Retrieve user-specific setting override, or None if not set."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT setting_value FROM user_settings WHERE username = ? AND setting_key = ?",
                (username, key)
            )
            row = cur.fetchone()
            return row["setting_value"] if row else None
        finally:
            conn.close()


def get_global_setting(conf_dir: str, key: str, default: Any = None) -> Any:
    """Retrieve global default setting."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT setting_value FROM global_settings WHERE setting_key = ?",
                (key,)
            )
            row = cur.fetchone()
            return row["setting_value"] if row else default
        finally:
            conn.close()


def set_user_setting(conf_dir: str, username: str, key: str, value: Any) -> None:
    """Store user-specific setting."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_settings (username, setting_key, setting_value) VALUES (?, ?, ?)",
                    (username, key, str(value) if value is not None else "")
                )
        finally:
            conn.close()


def set_global_setting(conf_dir: str, key: str, value: Any) -> None:
    """Store global default setting."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO global_settings (setting_key, setting_value) VALUES (?, ?)",
                    (key, str(value) if value is not None else "")
                )
        finally:
            conn.close()


def delete_user_setting(conf_dir: str, username: str, key: str) -> None:
    """Delete user override, restoring global default."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute(
                    "DELETE FROM user_settings WHERE username = ? AND setting_key = ?",
                    (username, key)
                )
        finally:
            conn.close()


def get_all_settings_bundle(conf_dir: str, username: str, base_defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return active settings map, along with per-field metadata (user override vs default).
    """
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            cur.execute("SELECT setting_key, setting_value FROM global_settings")
            global_map = {r["setting_key"]: r["setting_value"] for r in cur.fetchall()}

            cur.execute("SELECT setting_key, setting_value FROM user_settings WHERE username = ?", (username,))
            user_map = {r["setting_key"]: r["setting_value"] for r in cur.fetchall()}

            active_settings: Dict[str, Any] = dict(base_defaults)
            field_status: Dict[str, Dict[str, Any]] = {}

            all_keys = set(base_defaults.keys()) | set(global_map.keys()) | set(user_map.keys())
            for k in all_keys:
                base_def = base_defaults.get(k)
                glob_val = global_map.get(k, base_def)
                has_user_override = (k in user_map)
                val = user_map[k] if has_user_override else glob_val
                active_settings[k] = val
                field_status[k] = {
                    "value": val,
                    "global_value": glob_val,
                    "has_override": has_user_override,
                    "is_custom": has_user_override and (str(val) != str(glob_val))
                }

            return {
                "settings": active_settings,
                "status": field_status,
                "global_settings": global_map,
                "user_settings": user_map
            }
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Custom Search Forms CRUD
# ---------------------------------------------------------------------------

def get_forms_for_user(conf_dir: str, username: str) -> List[Dict[str, Any]]:
    """
    Return list of forms visible to user (global forms + user-owned forms).
    Applies per-user enabled/disabled state from user_form_states.
    """
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            # Fetch user form states
            cur.execute("SELECT form_id, enabled FROM user_form_states WHERE username = ?", (username,))
            state_map = {r["form_id"]: bool(r["enabled"]) for r in cur.fetchall()}

            # Fetch forms (global or owned by user)
            cur.execute(
                "SELECT form_id, title, is_global, owner_user, form_json FROM custom_forms "
                "WHERE is_global = 1 OR owner_user = ? ORDER BY form_id ASC",
                (username,)
            )
            rows = cur.fetchall()
            forms = []
            for r in rows:
                try:
                    f_dict = json.loads(r["form_json"])
                except Exception:
                    continue
                f_id = r["form_id"]
                is_global = bool(r["is_global"])
                # Merge per-user enable state
                if f_id in state_map:
                    f_dict["enabled"] = state_map[f_id]
                else:
                    # Global forms default to enabled (1)
                    # User forms default to form's own enabled attribute or True
                    f_dict["enabled"] = f_dict.get("enabled", True) if not is_global else True

                f_dict["id"] = f_id
                f_dict["is_global"] = is_global
                f_dict["owner_user"] = r["owner_user"]
                forms.append(f_dict)

            return forms
        finally:
            conn.close()


def save_form(conf_dir: str, form_dict: Dict[str, Any], username: str, is_global: bool = False) -> None:
    """Save or update custom search form."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    form_id = form_dict.get("id")
    if not form_id:
        return
    title = form_dict.get("name") or form_dict.get("title") or form_id
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO custom_forms (form_id, title, is_global, owner_user, form_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, datetime('now'))",
                    (form_id, title, 1 if is_global else 0, username, json.dumps(form_dict))
                )
                # Ensure user's own enable state is recorded
                if "enabled" in form_dict:
                    conn.execute(
                        "INSERT OR REPLACE INTO user_form_states (username, form_id, enabled) VALUES (?, ?, ?)",
                        (username, form_id, 1 if form_dict["enabled"] else 0)
                    )
        finally:
            conn.close()


def delete_form(conf_dir: str, form_id: str, username: str, is_admin: bool = False) -> bool:
    """Delete form if user is owner or admin."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            cur.execute("SELECT owner_user, is_global FROM custom_forms WHERE form_id = ?", (form_id,))
            row = cur.fetchone()
            if not row:
                return False
            if not is_admin and row["owner_user"] != username:
                return False

            with conn:
                conn.execute("DELETE FROM custom_forms WHERE form_id = ?", (form_id,))
                conn.execute("DELETE FROM user_form_states WHERE form_id = ?", (form_id,))
            return True
        finally:
            conn.close()


def set_form_enabled_state(conf_dir: str, username: str, form_id: str, enabled: bool) -> None:
    """Toggle enable/disable state of form for specific user."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO user_form_states (username, form_id, enabled) VALUES (?, ?, ?)",
                    (username, form_id, 1 if enabled else 0)
                )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Metadata Extraction Rules CRUD
# ---------------------------------------------------------------------------

def get_metadata_rules_from_db(conf_dir: str) -> Dict[str, Any]:
    """Retrieve metadata rules and extractor path from SQLite."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            cur = conn.cursor()
            cur.execute("SELECT rule_id, rule_json FROM metadata_rules ORDER BY sort_order ASC, rule_id ASC")
            rules = []
            for r in cur.fetchall():
                try:
                    rules.append(json.loads(r["rule_json"]))
                except Exception:
                    pass

            cur.execute("SELECT value FROM extractor_config WHERE key = 'extractor_path'")
            row = cur.fetchone()
            ext_path = row["value"] if row else "/usr/local/bin/recoll-metadata-extractor"
            return {"rules": rules, "extractor_path": ext_path}
        finally:
            conn.close()


def save_metadata_rules_to_db(conf_dir: str, rules: List[Dict[str, Any]], extractor_path: Optional[str] = None) -> None:
    """Save metadata rules and extractor path to SQLite, and keep JSON on disk synced."""
    init_db(conf_dir)
    db_path = get_db_path(conf_dir)
    lock = get_db_lock(db_path)
    with lock:
        conn = get_db_connection(conf_dir)
        try:
            with conn:
                conn.execute("DELETE FROM metadata_rules")
                for idx, r in enumerate(rules):
                    r_id = r.get("id") or f"rule_{idx}"
                    conn.execute(
                        "INSERT INTO metadata_rules (rule_id, rule_json, sort_order) VALUES (?, ?, ?)",
                        (r_id, json.dumps(r), idx)
                    )
                if extractor_path:
                    conn.execute(
                        "INSERT OR REPLACE INTO extractor_config (key, value) VALUES ('extractor_path', ?)",
                        (extractor_path,)
                    )
        finally:
            conn.close()

    # Also sync metadata_rules.json file on disk so the external CLI extractor can read it
    json_path = os.path.join(conf_dir, "metadata_rules.json")
    try:
        data = {
            "rules": rules,
            "extractor_path": extractor_path or "/usr/local/bin/recoll-metadata-extractor"
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
