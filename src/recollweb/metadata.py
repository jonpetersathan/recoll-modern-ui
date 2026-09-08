"""
Metadata rules management, live pattern testing, and Recoll configuration synchronization.
"""

import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Set, Tuple

from recollweb.constants import METADATA_RULES_FILENAME
from recollweb.logging import logger


DEFAULT_EXTRACTOR_PATH = os.getenv(
    "RECOLL_METADATA_EXTRACTOR",
    "/usr/local/bin/recoll-metadata-extractor",
)


def sanitize_field_name(name: str) -> str:
    """Sanitize field name to alphanumeric and underscores for Recoll compatibility."""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
    return cleaned.lower()


def sanitize_field_value(val: Any) -> str:
    """Strip newlines and carriage returns from field value."""
    if val is None:
        return ""
    return str(val).replace('\r', ' ').replace('\n', ' ').strip()


def matches_glob(pattern: str, path_str: str) -> bool:
    """Fast glob pattern matching for path filtering."""
    pattern = pattern.strip()
    if not pattern or pattern in ("*", "**"):
        return True

    if pattern == path_str:
        return True

    if pattern.startswith("**/*."):
        suffix = pattern[5:]
        return path_str.endswith("." + suffix)

    if pattern.startswith("*."):
        suffix = pattern[2:]
        return path_str.endswith("." + suffix)

    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path_str.startswith(prefix)

    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return path_str.startswith(prefix)

    # Convert basic glob to regex
    regex_str = "^"
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == '*':
            if i + 1 < n and pattern[i + 1] == '*':
                if i + 2 < n and pattern[i + 2] == '/':
                    regex_str += "(?:.*/)?"
                    i += 3
                    continue
                regex_str += ".*"
                i += 2
                continue
            regex_str += "[^/]*"
        elif c == '?':
            regex_str += "[^/]"
        elif c in r".()+|^$@%{}[]":
            regex_str += "\\" + c
        else:
            regex_str += c
        i += 1
    regex_str += "$"

    try:
        return bool(re.match(regex_str, path_str))
    except Exception:
        return False


def evaluate_rules_in_memory(rules: List[Dict[str, Any]], file_path: str) -> Dict[str, str]:
    """
    In-memory evaluation of metadata rules against a target path.
    Matches the exact semantics of the Rust metadata extractor.
    """
    results: Dict[str, str] = {}
    normalized_path = file_path.replace('\\', '/')
    segments = [s for s in normalized_path.split('/') if s]
    filename = os.path.basename(normalized_path)
    stem, _ = os.path.splitext(filename)

    for rule in rules:
        if not rule.get('enabled', True):
            continue

        path_filter = rule.get('path_filter', '').strip()
        if path_filter and not matches_glob(path_filter, normalized_path):
            continue

        rule_type = rule.get('type')

        if rule_type == 'depth':
            try:
                depth = int(rule.get('depth', 0))
            except (ValueError, TypeError):
                continue
            field = sanitize_field_name(rule.get('field', ''))
            if not field or not segments:
                continue

            target_idx = None
            if depth < 0:
                rev = len(segments) + depth
                if 0 <= rev < len(segments):
                    target_idx = rev
            elif 0 <= depth < len(segments):
                target_idx = depth

            if target_idx is not None:
                val = sanitize_field_value(segments[target_idx])
                if val:
                    results[field] = val

        elif rule_type == 'delimiter':
            delimiter = rule.get('delimiter', '')
            if not delimiter:
                continue
            target = rule.get('target', 'filename')
            target_str = normalized_path if target == 'path' else (stem if target == 'stem' else filename)
            tokens = target_str.split(delimiter)
            mappings = rule.get('mappings', [])

            for m in mappings:
                try:
                    idx = int(m.get('index', -1))
                except (ValueError, TypeError):
                    continue
                field = sanitize_field_name(m.get('field', ''))
                if field and 0 <= idx < len(tokens):
                    val = sanitize_field_value(tokens[idx])
                    if val:
                        results[field] = val

        elif rule_type == 'regex':
            pattern = rule.get('pattern', '').strip()
            if not pattern:
                continue
            try:
                match = re.search(pattern, normalized_path)
                if match:
                    groupdict = match.groupdict()
                    for k, v in groupdict.items():
                        if v is not None:
                            clean_k = sanitize_field_name(k)
                            clean_v = sanitize_field_value(v)
                            if clean_k and clean_v:
                                results[clean_k] = clean_v
            except Exception as exc:
                logger.warning("METADATA_REGEX_ERROR in rule '%s': %s", rule.get('name', 'unnamed'), exc)

    return results


class MetadataRulesManager:
    """Manages metadata rules JSON persistence and Recoll index synchronization."""

    @staticmethod
    def get_rules_file_path(conf_dir: str) -> str:
        return os.path.join(conf_dir, METADATA_RULES_FILENAME)

    @classmethod
    def get_rules(cls, conf_dir: str) -> Dict[str, Any]:
        """Load metadata rules from JSON configuration, or return empty schema."""
        file_path = cls.get_rules_file_path(conf_dir)
        if not os.path.isfile(file_path):
            return {
                "rules": [],
                "extractor_path": DEFAULT_EXTRACTOR_PATH,
            }
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {"rules": []}
                data.setdefault("rules", [])
                data.setdefault("extractor_path", DEFAULT_EXTRACTOR_PATH)
                return data
        except Exception as exc:
            logger.error("METADATA_RULES_LOAD_ERROR: %s", exc)
            return {
                "rules": [],
                "extractor_path": DEFAULT_EXTRACTOR_PATH,
                "error": str(exc),
            }

    @classmethod
    def validate_rules(cls, rules_data: Dict[str, Any]) -> List[str]:
        """Validate rule syntax and integrity, returning list of validation error strings."""
        errors: List[str] = []
        rules = rules_data.get('rules')
        if not isinstance(rules, list):
            return ["Invalid schema: 'rules' must be a list."]

        for i, rule in enumerate(rules):
            rule_id = rule.get('id') or f"rule_{i + 1}"
            rule_type = rule.get('type')
            if rule_type not in ('depth', 'delimiter', 'regex'):
                errors.append(f"Rule '{rule_id}': unknown type '{rule_type}'.")
                continue

            if rule_type == 'depth':
                field = rule.get('field', '').strip()
                if not field:
                    errors.append(f"Rule '{rule_id}': field name is required.")
                try:
                    int(rule.get('depth', 0))
                except (ValueError, TypeError):
                    errors.append(f"Rule '{rule_id}': depth must be an integer.")

            elif rule_type == 'delimiter':
                delim = rule.get('delimiter', '')
                if not delim:
                    errors.append(f"Rule '{rule_id}': delimiter character is required.")
                mappings = rule.get('mappings', [])
                if not mappings or not isinstance(mappings, list):
                    errors.append(f"Rule '{rule_id}': at least one field mapping is required.")
                for m in mappings:
                    if not m.get('field', '').strip():
                        errors.append(f"Rule '{rule_id}': field name missing in delimiter mapping.")

            elif rule_type == 'regex':
                pattern = rule.get('pattern', '').strip()
                if not pattern:
                    errors.append(f"Rule '{rule_id}': regex pattern is required.")
                else:
                    try:
                        compiled = re.compile(pattern)
                        if not compiled.groupindex:
                            errors.append(
                                f"Rule '{rule_id}': regex pattern must contain at least one named capture group e.g. (?P<field>...)"
                            )
                    except re.error as reg_err:
                        errors.append(f"Rule '{rule_id}': invalid regex pattern: {reg_err}")

        return errors

    @classmethod
    def save_rules(cls, conf_dir: str, rules_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and save metadata rules to disk, then synchronize Recoll configuration."""
        errors = cls.validate_rules(rules_data)
        if errors:
            raise ValueError("; ".join(errors))

        os.makedirs(conf_dir, exist_ok=True)
        file_path = cls.get_rules_file_path(conf_dir)
        tmp_path = file_path + ".tmp"

        payload = {
            "rules": rules_data.get("rules", []),
            "extractor_path": rules_data.get("extractor_path", DEFAULT_EXTRACTOR_PATH),
        }

        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, file_path)

        # Synchronize Recoll recoll.conf and fields files
        cls.sync_recoll_config(conf_dir, payload)

        return payload

    @classmethod
    def get_extracted_fields(cls, conf_dir: str) -> List[str]:
        """Collect all unique target field names declared across enabled rules."""
        data = cls.get_rules(conf_dir)
        fields: Set[str] = set()
        for rule in data.get('rules', []):
            if not rule.get('enabled', True):
                continue
            rtype = rule.get('type')
            if rtype == 'depth':
                f = sanitize_field_name(rule.get('field', ''))
                if f:
                    fields.add(f)
            elif rtype == 'delimiter':
                for m in rule.get('mappings', []):
                    f = sanitize_field_name(m.get('field', ''))
                    if f:
                        fields.add(f)
            elif rtype == 'regex':
                pattern = rule.get('pattern', '')
                try:
                    c = re.compile(pattern)
                    for k in c.groupindex.keys():
                        clean = sanitize_field_name(k)
                        if clean:
                            fields.add(clean)
                except Exception:
                    pass
        return sorted(fields)

    @classmethod
    def sync_recoll_config(cls, conf_dir: str, payload: Dict[str, Any]):
        """
        Synchronize recoll.conf and fields configuration:
        1. Ensures metadatacmds is registered in recoll.conf
        2. Adds custom fields to [prefixes] and [stored] in fields config
        """
        rules = payload.get('rules', [])
        extractor_path = payload.get('extractor_path', DEFAULT_EXTRACTOR_PATH)
        has_active_rules = any(r.get('enabled', True) for r in rules)

        recoll_conf_path = os.path.join(conf_dir, "recoll.conf")
        fields_path = os.path.join(conf_dir, "fields")

        # 1. Synchronize recoll.conf
        if os.path.isfile(recoll_conf_path):
            try:
                with open(recoll_conf_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                new_lines: List[str] = []
                found_metadatacmds = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("metadatacmds"):
                        found_metadatacmds = True
                        if has_active_rules:
                            new_lines.append(f"metadatacmds = ; rclmulti1 = {extractor_path} %f\n")
                        else:
                            # Keep commented out if no active rules
                            new_lines.append(f"# metadatacmds = ; rclmulti1 = {extractor_path} %f\n")
                    else:
                        new_lines.append(line)

                if not found_metadatacmds and has_active_rules:
                    new_lines.append(f"\n# Metadata extractor command\nmetadatacmds = ; rclmulti1 = {extractor_path} %f\n")

                with open(recoll_conf_path + ".tmp", 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                os.replace(recoll_conf_path + ".tmp", recoll_conf_path)
            except Exception as exc:
                logger.error("METADATA_CONF_SYNC_ERROR: Failed to update recoll.conf: %s", exc)

        # 2. Synchronize fields config
        extracted_fields = cls.get_extracted_fields(conf_dir)
        if extracted_fields:
            cls._sync_fields_file(fields_path, extracted_fields)

    @classmethod
    def _sync_fields_file(cls, fields_path: str, custom_fields: List[str]):
        """
        Ensure custom fields are listed under [prefixes] and [stored] in the fields config.
        """
        try:
            existing_lines: List[str] = []
            if os.path.isfile(fields_path):
                with open(fields_path, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()

            # Parse sections
            sections: Dict[str, List[str]] = {}
            current_section = "global"
            sections[current_section] = []

            for line in existing_lines:
                stripped = line.strip()
                if stripped.startswith('[') and stripped.endswith(']'):
                    current_section = stripped[1:-1].strip().lower()
                    if current_section not in sections:
                        sections[current_section] = []
                else:
                    sections.setdefault(current_section, []).append(line)

            # Ensure [prefixes]
            prefixes = sections.setdefault("prefixes", [])
            existing_prefix_keys = set()
            for line in prefixes:
                if '=' in line and not line.strip().startswith('#'):
                    k = line.split('=', 1)[0].strip().lower()
                    existing_prefix_keys.add(k)

            for f in custom_fields:
                if f not in existing_prefix_keys:
                    # Recoll prefix format: field = XSFNfield
                    prefixes.append(f"{f} = XSFN{f.upper()}\n")

            # Ensure [stored]
            stored = sections.setdefault("stored", [])
            stored_content = "".join(stored)
            for f in custom_fields:
                if f not in stored_content:
                    stored.append(f"{f} = \n")

            # Write back
            with open(fields_path + ".tmp", 'w', encoding='utf-8') as f:
                for sec_name, sec_lines in sections.items():
                    if sec_name != "global":
                        f.write(f"[{sec_name}]\n")
                    f.writelines(sec_lines)
                    if sec_lines and not sec_lines[-1].endswith('\n'):
                        f.write('\n')
            os.replace(fields_path + ".tmp", fields_path)
            logger.info("FIELDS_SYNC: Updated %d custom fields in %s", len(custom_fields), fields_path)
        except Exception as exc:
            logger.error("FIELDS_SYNC_ERROR: Failed to update fields file %s: %s", fields_path, exc)

    @classmethod
    def test_sample_path(cls, sample_path: str, rules: List[Dict[str, Any]]) -> Dict[str, str]:
        """Test candidate rules against sample file path."""
        return evaluate_rules_in_memory(rules, sample_path)
