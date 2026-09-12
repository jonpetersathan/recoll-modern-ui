"""
Metadata rules management, live pattern testing, and Recoll configuration synchronization.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from recollweb.constants import METADATA_RULES_FILENAME
from recollweb.logging import logger


DEFAULT_EXTRACTOR_PATH = os.getenv(
    "RECOLL_METADATA_EXTRACTOR",
    "/usr/local/bin/recoll-metadata-extractor",
)


STANDARD_DOCUMENT_FIELDS: Set[str] = {
    "title",
    "dmtime",
    "mtime",
}

MONTH_NAMES: Dict[str, int] = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}


def sanitize_field_name(name: str) -> str:
    """Sanitize field name to alphanumeric and underscores for Recoll compatibility, preserving dmtime@ directives."""
    name_stripped = name.strip()
    lower_name = name_stripped.lower()
    if lower_name.startswith("dmtime@"):
        suffix = re.sub(r'[^a-zA-Z0-9_]', '', name_stripped[7:])
        return f"dmtime@{suffix}"
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name_stripped)
    return cleaned.lower()


def parse_month_value(val: Any) -> Optional[int]:
    """Parse month value as numeric (1-12, e.g. '2', '02') or English name (e.g. 'Feb', 'February')."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s.isdigit():
        m = int(s)
        return m if 1 <= m <= 12 else None
    return MONTH_NAMES.get(s)


def parse_day_value(val: Any) -> Optional[int]:
    """Parse day value as integer between 1 and 31."""
    if val is None:
        return None
    s = str(val).strip()
    if s.isdigit():
        d = int(s)
        return d if 1 <= d <= 31 else None
    return None


def parse_year_value(val: Any) -> Optional[int]:
    """Parse year value as integer."""
    if val is None:
        return None
    s = str(val).strip()
    if s.isdigit():
        y = int(s)
        if y < 100:
            y += 2000 if y < 70 else 1900
        return y if y > 0 else None
    return None


def date_to_utc_epoch(year: int, month: int, day: int) -> Optional[int]:
    """Convert year, month, day to Unix epoch timestamp at 00:00:00 UTC."""
    try:
        dt = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def parse_formatted_date(val: str, fmt: str) -> Optional[int]:
    """Parse date strings according to specified directive format (YYYYMMDD, DDMMYYYY, MMDDYYYY)."""
    val = val.strip()
    if not val:
        return None

    fmt_lower = fmt.lower()
    parts = [p for p in re.split(r'[-/._\s]+', val) if p]
    if len(parts) == 3:
        if fmt_lower == 'yyyymmdd':
            y, m, d = parse_year_value(parts[0]), parse_month_value(parts[1]), parse_day_value(parts[2])
        elif fmt_lower == 'ddmmyyyy':
            d, m, y = parse_day_value(parts[0]), parse_month_value(parts[1]), parse_year_value(parts[2])
        elif fmt_lower == 'mmddyyyy':
            m, d, y = parse_month_value(parts[0]), parse_day_value(parts[1]), parse_year_value(parts[2])
        else:
            return None
        if y is not None and m is not None and d is not None:
            return date_to_utc_epoch(y, m, d)

    clean_digits = re.sub(r'\D', '', val)
    if len(clean_digits) == 8:
        if fmt_lower == 'yyyymmdd':
            y = int(clean_digits[0:4])
            m = int(clean_digits[4:6])
            d = int(clean_digits[6:8])
        elif fmt_lower == 'ddmmyyyy':
            d = int(clean_digits[0:2])
            m = int(clean_digits[2:4])
            y = int(clean_digits[4:8])
        elif fmt_lower == 'mmddyyyy':
            m = int(clean_digits[0:2])
            d = int(clean_digits[2:4])
            y = int(clean_digits[4:8])
        else:
            return None
        if 1 <= m <= 12 and 1 <= d <= 31 and y > 0:
            return date_to_utc_epoch(y, m, d)

    return None


def process_date_directives(results: Dict[str, str]) -> Dict[str, str]:
    """
    Detect dmtime date directives, convert them to a Unix timestamp at 00:00:00 UTC,
    set the 'dmtime' field, and purge directive keys from results.
    """
    keys_to_delete: Set[str] = set()
    extracted_timestamp: Optional[int] = None

    # 1. Formatted dates: dmtime@YYYYMMDD, dmtime@DDMMYYYY, dmtime@MMDDYYYY (and regex equivalents)
    for k, v in list(results.items()):
        lower_k = k.lower()
        if lower_k in ('dmtime@yyyymmdd', 'dmtime_yyyymmdd'):
            keys_to_delete.add(k)
            ts = parse_formatted_date(v, 'yyyymmdd')
            if ts is not None:
                extracted_timestamp = ts
        elif lower_k in ('dmtime@ddmmyyyy', 'dmtime_ddmmyyyy'):
            keys_to_delete.add(k)
            ts = parse_formatted_date(v, 'ddmmyyyy')
            if ts is not None:
                extracted_timestamp = ts
        elif lower_k in ('dmtime@mmddyyyy', 'dmtime_mmddyyyy'):
            keys_to_delete.add(k)
            ts = parse_formatted_date(v, 'mmddyyyy')
            if ts is not None:
                extracted_timestamp = ts

    # 2. Split components: dmtime@year, dmtime@month, dmtime@day
    year_val = None
    month_val = None
    day_val = None
    for k, v in list(results.items()):
        lower_k = k.lower()
        if lower_k in ('dmtime@year', 'dmtime_year'):
            keys_to_delete.add(k)
            year_val = v
        elif lower_k in ('dmtime@month', 'dmtime_month'):
            keys_to_delete.add(k)
            month_val = v
        elif lower_k in ('dmtime@day', 'dmtime_day'):
            keys_to_delete.add(k)
            day_val = v

    if extracted_timestamp is None and year_val is not None:
        y = parse_year_value(year_val)
        m = parse_month_value(month_val) if month_val is not None else 1
        d = parse_day_value(day_val) if day_val is not None else 1
        if y is not None and m is not None and d is not None:
            ts = date_to_utc_epoch(y, m, d)
            if ts is not None:
                extracted_timestamp = ts

    # Purge any remaining dmtime@ directive keys
    for k in list(results.keys()):
        if k.lower().startswith('dmtime@'):
            keys_to_delete.add(k)

    for k in keys_to_delete:
        results.pop(k, None)

    if extracted_timestamp is not None:
        results['dmtime'] = str(extracted_timestamp)

    return results


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

    return process_date_directives(results)


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

        def add_field(raw_field: str):
            clean = sanitize_field_name(raw_field)
            if not clean:
                return
            clean_lower = clean.lower()
            if clean_lower.startswith('dmtime@') or clean_lower in (
                'dmtime_year', 'dmtime_month', 'dmtime_day',
                'dmtime_yyyymmdd', 'dmtime_ddmmyyyy', 'dmtime_mmddyyyy'
            ):
                fields.add('dmtime')
            else:
                fields.add(clean)

        for rule in data.get('rules', []):
            if not rule.get('enabled', True):
                continue
            rtype = rule.get('type')
            if rtype == 'depth':
                add_field(rule.get('field', ''))
            elif rtype == 'delimiter':
                for m in rule.get('mappings', []):
                    add_field(m.get('field', ''))
            elif rtype == 'regex':
                pattern = rule.get('pattern', '')
                try:
                    c = re.compile(pattern)
                    for k in c.groupindex.keys():
                        add_field(k)
                except Exception:
                    pass
        return sorted(fields)

    @classmethod
    def get_all_known_fields(cls, conf_dir: str) -> List[str]:
        """Return all standard document fields plus custom fields from metadata rules."""
        from recollweb.constants import DOCUMENT_FIELDS
        fields = set(DOCUMENT_FIELDS)
        fields.update(cls.get_extracted_fields(conf_dir))
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
        Standard document metadata fields like 'title' and 'dmtime' are excluded from
        synthetic XSFN prefixes to avoid corrupting Recoll's internal field indexers.
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
            # Filter out any corrupt synthetic XSFN prefixes for standard fields if previously written
            clean_prefixes = []
            for line in prefixes:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.split('=', 1)
                    k_clean = k.strip().lower()
                    v_clean = v.strip()
                    if k_clean in STANDARD_DOCUMENT_FIELDS and v_clean.startswith('XSFN'):
                        # Skip corrupt synthetic prefix for standard fields
                        continue
                clean_prefixes.append(line)
            sections["prefixes"] = clean_prefixes
            prefixes = clean_prefixes

            existing_prefix_keys = set()
            for line in prefixes:
                if '=' in line and not line.strip().startswith('#'):
                    k = line.split('=', 1)[0].strip().lower()
                    existing_prefix_keys.add(k)

            for f in custom_fields:
                f_lower = f.lower()
                if f_lower in STANDARD_DOCUMENT_FIELDS:
                    continue
                if f_lower not in existing_prefix_keys:
                    # Recoll prefix format: field = XSFNfield
                    prefixes.append(f"{f_lower} = XSFN{f.upper()}\n")

            # Ensure [stored]
            stored = sections.setdefault("stored", [])
            stored_content = "".join(stored)
            for f in custom_fields:
                f_lower = f.lower()
                if f_lower in STANDARD_DOCUMENT_FIELDS:
                    continue
                if f_lower not in stored_content:
                    stored.append(f"{f_lower} = \n")

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
