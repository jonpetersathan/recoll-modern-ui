"""
Recoll configuration resolution, user settings, cookies, and directory trees.
"""

import glob
import os
import shlex
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as urlquote
import bottle
from recoll import rclconfig

from recollweb.auth import get_current_username, is_admin_user, get_user_role
from recollweb.constants import (
    CUSTOM_LOGO_FILENAMES,
    DEFAULT_CONFIG,
    DOCUMENT_FIELDS,
    SORT_OPTIONS,
)
from recollweb.db import get_setting, init_db
from recollweb.logging import logger
from recollweb.utils import extract_common_prefix


def get_config_dir() -> str:
    """
    Resolve Recoll configuration directory from environment or user home.
    """
    conf_dir = os.environ.get('RECOLL_CONFDIR')
    if conf_dir and os.path.isdir(conf_dir):
        return conf_dir
    try:
        rcl_conf = rclconfig.RclConfig(conf_dir)
        cd = rcl_conf.getConfDir()
        if cd and os.path.isdir(cd):
            return cd
    except Exception:
        pass
    return os.path.expanduser('~/.recoll')


def find_custom_logo(conf_dir: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Search configuration directory for a custom logo file (logo.png, logo.jpg, logo.svg).
    Returns (filename, absolute_path) if found, else None.
    If multiple candidate files are present, the most recently modified file is chosen.
    """
    target_dir = conf_dir or get_config_dir()
    if not target_dir or not os.path.isdir(target_dir):
        return None

    found: List[Tuple[float, str, str]] = []
    for fn in CUSTOM_LOGO_FILENAMES:
        fp = os.path.join(target_dir, fn)
        if os.path.isfile(fp):
            try:
                mtime = os.path.getmtime(fp)
            except OSError:
                mtime = 0
            found.append((mtime, fn, fp))

    if not found:
        return None

    found.sort(key=lambda x: x[0], reverse=True)
    return found[0][1], found[0][2]


class ConfigManager:
    """
    Resolves Recoll configuration, merges user cookies, and provides directory tree listings.
    """

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Build active configuration dictionary combining recoll.conf parameters and user cookies.
        """
        for env_var in ("RECOLL_CONFDIR", "RECOLL_EXTRACONFDIRS"):
            if env_var in bottle.request.environ:
                os.environ[env_var] = bottle.request.environ[env_var]

        conf_dir = os.environ.get('RECOLL_CONFDIR')
        rcl_conf = rclconfig.RclConfig(conf_dir)
        config: Dict[str, Any] = {'confdir': rcl_conf.getConfDir()}

        # Top directories
        raw_topdirs = rcl_conf.getConfParam('topdirs') or ""
        topdirs = [os.path.expanduser(d) for d in shlex.split(raw_topdirs)]
        config['dirs'] = dict.fromkeys(topdirs, config['confdir'])
        raw_prefix = extract_common_prefix(topdirs)
        if raw_prefix == '/data/':
            config['commonprefix'] = ''
        elif raw_prefix.startswith('/data/'):
            config['commonprefix'] = raw_prefix[len('/data/'):]
        else:
            config['commonprefix'] = raw_prefix

        # Extra configuration directories
        extra_dirs_env = os.environ.get('RECOLL_EXTRACONFDIRS')
        if extra_dirs_env:
            config['extraconfdirs'] = shlex.split(extra_dirs_env)
            for extra_dir in config['extraconfdirs']:
                extra_rcl = rclconfig.RclConfig(extra_dir)
                extra_top = extra_rcl.getConfParam('topdirs') or ""
                for d in shlex.split(extra_top):
                    config['dirs'][os.path.expanduser(d)] = extra_dir
            config['extradbs'] = [ConfigManager.resolve_db_dir(e) for e in config['extraconfdirs']]
        else:
            config['extraconfdirs'] = None
            config['extradbs'] = None

        config['stemlang'] = rcl_conf.getConfParam('indexstemminglanguages')

        # Load webui overrides from recoll.conf
        fetches = [
            ("context", 1), ("stem", 1), ("timefmt", 0), ("dirdepth", 1),
            ("maxchars", 1), ("maxresults", 1), ("perpage", 1), ("csvfields", 0),
            ("title_link", 0), ("collapsedups", 1), ("synonyms", 0),
            ("noresultlinks", 1), ("logquery", 1), ("shortenpaths", 1),
            ("permlinks", 1), ("res_permlink", 1), ("queryfrag", 0),
        ]
        defaults = dict(DEFAULT_CONFIG)
        for key, is_int in fetches:
            val = rcl_conf.getConfParam(f"webui_{key}")
            if val is not None:
                defaults[key] = int(val) if is_int else val

        current_user = get_current_username()
        config['current_user'] = current_user
        config['is_admin'] = is_admin_user(current_user, config['confdir'])
        config['user_role'] = get_user_role(current_user, config['confdir'])

        # Initialize SQLite database if needed
        init_db(config['confdir'])

        # Load user settings from SQLite database (recoll-web.db) with fallback to global settings, cookies, and defaults
        for key, default_val in defaults.items():
            db_val = get_setting(config['confdir'], current_user, key)
            if db_val is not None and db_val != "":
                try:
                    config[key] = type(default_val)(db_val)
                except (ValueError, TypeError):
                    config[key] = default_val
            else:
                cookie_val = bottle.request.get_cookie(key) if hasattr(bottle, 'request') else None
                if cookie_val is not None and cookie_val not in ("None", ""):
                    try:
                        config[key] = type(default_val)(cookie_val)
                    except (ValueError, TypeError):
                        config[key] = default_val
                else:
                    config[key] = default_val

        # Filter valid JSON/CSV fields: only support available keywords (including metadata extraction rule tags)
        try:
            from recollweb.metadata import MetadataRulesManager
            available_keywords = set(MetadataRulesManager.get_all_known_fields(config['confdir']))
        except Exception:
            available_keywords = set(DOCUMENT_FIELDS)

        valid_csv = [f for f in str(config['csvfields']).split() if f in available_keywords]
        config['csvfields'] = " ".join(valid_csv) if valid_csv else " ".join([f for f in DEFAULT_CONFIG['csvfields'].split() if f in available_keywords])
        config['fields'] = " ".join(sorted(available_keywords))

        # Mountpoints for file links
        config['mounts'] = {}
        for d in config['dirs']:
            mount_key = f"mount_{urlquote(d, '')}"
            db_mount = get_setting(config['confdir'], current_user, mount_key)
            cookie_mount = bottle.request.get_cookie(mount_key) if hasattr(bottle, 'request') else None
            conf_mount = rcl_conf.getConfParam(f"webui_mount_{d}")
            config['mounts'][d] = db_mount or cookie_mount or conf_mount or f"file://{d}"

        # Server-enforced settings
        no_json_csv = rcl_conf.getConfParam('webui_nojsoncsv')
        config['rclc_nojsoncsv'] = int(no_json_csv) if no_json_csv is not None else 0

        max_per_page = rcl_conf.getConfParam('webui_maxperpage')
        if max_per_page:
            max_p = int(max_per_page)
            if config['perpage'] == 0 or config['perpage'] > max_p:
                config['perpage'] = max_p

        no_settings = rcl_conf.getConfParam('webui_nosettings')
        config['rclc_nosettings'] = int(no_settings) if no_settings is not None else 0

        pdf_pos = rcl_conf.getConfParam('webui_pdfposition')
        config['rclc_pdfposition'] = int(pdf_pos) if pdf_pos is not None else 0

        default_sort = str(rcl_conf.getConfParam('webui_defaultsort') or '')
        config['defsortidx'] = 0
        for idx, (sort_val, sort_label) in enumerate(SORT_OPTIONS):
            if default_sort in (sort_val, sort_label):
                config['defsortidx'] = idx
                break

        return config

    @staticmethod
    def resolve_db_dir(conf_dir: str) -> bytes:
        """
        Resolve database path as bytes for Recoll C-bindings.
        """
        expanded = os.path.expanduser(conf_dir)
        rcl_conf = rclconfig.RclConfig(expanded)
        try:
            db_dir = rcl_conf.getDbDir()
        except Exception:
            db_dir = rcl_conf.getConfParam('dbdir') or 'xapiandb'
            if not os.path.isabs(db_dir):
                cache_dir = rcl_conf.getConfParam('cachedir') or expanded
                db_dir = os.path.join(cache_dir, db_dir)
        return os.path.normpath(db_dir).encode(sys.getfilesystemencoding())

    @staticmethod
    def get_directory_tree(top_dirs: List[str], max_depth: int) -> List[str]:
        """
        Scan directory tree up to max_depth for folder scope dropdown.
        Omits /data/ root prefix when scanning top-level /data.
        """
        dir_list: List[str] = []
        for top in top_dirs:
            encoded_top = top.encode('utf-8', 'surrogateescape')
            is_data_root = top.rstrip('/') == '/data'
            found_dirs = [] if is_data_root else [encoded_top]
            for depth in range(1, max_depth + 1):
                pattern = encoded_top.rstrip(b'/') + b'/*' * depth
                found_dirs.extend(glob.glob(pattern))
            valid_dirs = [d for d in found_dirs if os.path.isdir(d)]
            if is_data_root:
                prefix = encoded_top.rstrip(b'/') + b'/'
                relative_dirs = [d[len(prefix):] for d in valid_dirs if d.startswith(prefix)]
            else:
                parent_path = encoded_top.rsplit(b'/', 1)[0]
                relative_dirs = [d.replace(parent_path + b'/', b'', 1) for d in valid_dirs]
            dir_list.extend([d.decode('utf-8', 'surrogateescape') for d in relative_dirs])
        return ['<all>'] + dir_list


MANAGED_INDEX_PARAMS: Dict[str, Dict[str, Any]] = {
    "skippedNames": {
        "type": list,
        "default": [],
        "description": "List of wildcard patterns for skipped files/directories",
    },
    "indexallfilenames": {
        "type": bool,
        "default": True,
        "description": "Index filenames of unprocessed/unsupported files",
    },
    "thrQSlices": {
        "type": str,
        "default": "1",
        "description": "Thread queue slice configuration",
    },
    "idxthreads": {
        "type": int,
        "default": 2,
        "description": "Number of indexing threads",
    },
    "pdfocrmode": {
        "type": str,
        "default": "off",
        "allowed": ["off", "auto", "always"],
        "description": "PDF OCR processing policy",
    },
    "noaspell": {
        "type": bool,
        "default": False,
        "description": "Disable aspell dictionary generation",
    },
    "indexstemmingpositions": {
        "type": bool,
        "default": True,
        "description": "Index word positions for stemmed terms",
    },
    "idxflushmb": {
        "type": int,
        "default": 50,
        "description": "Index flush threshold in megabytes",
    },
    "idxabsml": {
        "type": int,
        "default": 250,
        "description": "Maximum stored abstract length in bytes",
    },
}

CANONICAL_PARAM_MAP: Dict[str, str] = {
    "skippednames": "skippedNames",
    "indexallfilenames": "indexallfilenames",
    "thrqslices": "thrQSlices",
    "idxthreads": "idxthreads",
    "pdfocrmode": "pdfocrmode",
    "noaspell": "noaspell",
    "indexstemmingpositions": "indexstemmingpositions",
    "idxflushmb": "idxflushmb",
    "idxabsml": "idxabsml",
    "idxabsmlen": "idxabsml",
}


def deduplicate_patterns(patterns: Any) -> List[str]:
    """
    Deduplicate list of wildcard patterns while strictly preserving insertion order.
    Whitespace is stripped, and empty strings or items containing '/' are dropped.
    """
    if isinstance(patterns, str):
        try:
            raw_items = shlex.split(patterns)
        except Exception:
            raw_items = patterns.split()
    elif isinstance(patterns, (list, tuple)):
        raw_items = patterns
    else:
        return []

    seen = set()
    unique: List[str] = []
    for item in raw_items:
        clean = str(item).strip()
        if clean and '/' not in clean and clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return unique


class RecollConfManager:
    """
    Parser, validator, and atomic serializer for recoll.conf configuration parameters.
    """

    @classmethod
    def get_config_path(cls, conf_dir: Optional[str] = None) -> str:
        target_dir = conf_dir or get_config_dir()
        return os.path.join(target_dir, "recoll.conf")

    @classmethod
    def get_index_config(cls, conf_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse and return the 9 managed index configuration parameters from recoll.conf.
        Missing parameters fall back to their system defaults.
        """
        config_path = cls.get_config_path(conf_dir)
        config: Dict[str, Any] = {k: v["default"] for k, v in MANAGED_INDEX_PARAMS.items()}

        if not os.path.isfile(config_path):
            return config

        try:
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as exc:
            logger.error("RECOLL_CONF_READ_ERROR: %s", exc)
            return config

        i = 0
        n = len(lines)
        current_section: Optional[str] = None

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Detect section header
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1].strip()
                i += 1
                continue

            # Only parse global section parameters
            if current_section is not None or stripped.startswith("#") or not stripped:
                i += 1
                continue

            if "=" in stripped:
                raw_key, raw_val = stripped.split("=", 1)
                key_lower = raw_key.strip().lower()
                canonical_key = CANONICAL_PARAM_MAP.get(key_lower)

                # Collect line continuations
                raw_parts = [raw_val.rstrip("\r\n").rstrip().rstrip("\\").strip()]
                cur_line = line
                while cur_line.rstrip("\r\n").rstrip().endswith("\\") and i + 1 < n:
                    i += 1
                    cur_line = lines[i]
                    raw_parts.append(cur_line.rstrip("\r\n").rstrip().rstrip("\\").strip())

                if canonical_key in MANAGED_INDEX_PARAMS:
                    full_val = " ".join(p for p in raw_parts if p)
                    spec = MANAGED_INDEX_PARAMS[canonical_key]

                    if canonical_key == "skippedNames":
                        config[canonical_key] = deduplicate_patterns(full_val)
                    elif spec["type"] is bool:
                        clean_val = full_val.split("#", 1)[0].strip().lower()
                        config[canonical_key] = clean_val in ("1", "true", "yes", "on")
                    elif spec["type"] is int:
                        clean_val = full_val.split("#", 1)[0].strip()
                        try:
                            config[canonical_key] = int(clean_val)
                        except ValueError:
                            pass
                    else:  # str
                        clean_val = full_val.split("#", 1)[0].strip()
                        if canonical_key == "pdfocrmode":
                            clean_val = clean_val.lower()
                            if clean_val in spec.get("allowed", []):
                                config[canonical_key] = clean_val
                        else:
                            config[canonical_key] = clean_val
            i += 1

        return config

    @classmethod
    def _serialize_param(cls, key: str, value: Any) -> List[str]:
        """
        Format a configuration parameter into line(s) for recoll.conf.
        skippedNames is wrapped across lines using trailing backslashes.
        """
        if key == "skippedNames":
            unique = deduplicate_patterns(value)
            if not unique:
                return ["skippedNames =\n"]
            lines = []
            prefix = "skippedNames = "
            current_line = prefix
            for item in unique:
                pat_str = f'"{item}"' if (" " in item and not (item.startswith('"') and item.endswith('"'))) else item
                if len(current_line) + len(pat_str) + 1 > 80 and current_line != prefix:
                    lines.append(current_line + "  \\\n")
                    current_line = "  " + pat_str
                else:
                    if current_line == prefix or current_line.endswith(" "):
                        current_line += pat_str
                    else:
                        current_line += " " + pat_str
            lines.append(current_line + "\n")
            return lines

        elif key in ("indexallfilenames", "noaspell", "indexstemmingpositions"):
            bool_str = "true" if bool(value) else "false"
            return [f"{key} = {bool_str}\n"]

        else:
            return [f"{key} = {value}\n"]

    @classmethod
    def update_index_config(cls, conf_dir: Optional[str], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate updates, apply changes in-place preserving unmanaged settings and comments,
        and atomically write recoll.conf via a temporary file replacement.
        """
        if not isinstance(updates, dict):
            raise ValueError("Configuration payload must be a JSON dictionary.")

        validated_updates: Dict[str, Any] = {}
        for raw_k, raw_v in updates.items():
            k_lower = str(raw_k).strip().lower()
            if k_lower not in CANONICAL_PARAM_MAP:
                continue  # Ignore unmanaged keys
            canonical_k = CANONICAL_PARAM_MAP[k_lower]
            spec = MANAGED_INDEX_PARAMS[canonical_k]

            if canonical_k == "skippedNames":
                if not isinstance(raw_v, (list, tuple, str)):
                    raise ValueError("skippedNames must be a list of wildcard strings.")
                if isinstance(raw_v, str):
                    try:
                        raw_items = shlex.split(raw_v)
                    except Exception:
                        raw_items = raw_v.split()
                else:
                    raw_items = list(raw_v)

                for item in raw_items:
                    clean = str(item).strip()
                    if "/" in clean:
                        raise ValueError(f"Pattern '{clean}' contains invalid path separator '/'. Patterns must be filenames or simple wildcards.")

                validated_updates[canonical_k] = deduplicate_patterns(raw_items)

            elif spec["type"] is bool:
                if isinstance(raw_v, bool):
                    validated_updates[canonical_k] = raw_v
                elif isinstance(raw_v, (int, str)):
                    str_v = str(raw_v).strip().lower()
                    if str_v in ("1", "true", "yes", "on"):
                        validated_updates[canonical_k] = True
                    elif str_v in ("0", "false", "no", "off"):
                        validated_updates[canonical_k] = False
                    else:
                        raise ValueError(f"{canonical_k} must be a boolean.")
                else:
                    raise ValueError(f"{canonical_k} must be a boolean.")

            elif spec["type"] is int:
                try:
                    int_val = int(raw_v)
                except (ValueError, TypeError):
                    raise ValueError(f"{canonical_k} must be a valid integer.")
                if canonical_k == "idxflushmb" and int_val <= 0:
                    raise ValueError("idxflushmb must be a positive integer in megabytes.")
                if canonical_k in ("idxthreads", "idxabsml") and int_val < 0:
                    raise ValueError(f"{canonical_k} must be a non-negative integer.")
                validated_updates[canonical_k] = int_val

            elif canonical_k == "pdfocrmode":
                str_v = str(raw_v).strip().lower()
                if str_v not in spec["allowed"]:
                    raise ValueError(f"pdfocrmode must be one of: {', '.join(spec['allowed'])}")
                validated_updates[canonical_k] = str_v

            else:  # thrQSlices
                str_v = str(raw_v).strip()
                if not str_v:
                    raise ValueError("thrQSlices must not be empty.")
                try:
                    int_slice = int(str_v)
                    if int_slice < 1:
                        raise ValueError("thrQSlices must be at least 1.")
                except (ValueError, TypeError):
                    raise ValueError("thrQSlices must be a valid integer.")
                validated_updates[canonical_k] = str_v

        config_path = cls.get_config_path(conf_dir)
        original_lines: List[str] = []
        if os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                original_lines = f.readlines()

        # Scan original lines to locate section headers and existing managed parameter spans
        param_spans: Dict[str, Tuple[int, int]] = {}
        first_section_idx: Optional[int] = None
        i = 0
        n = len(original_lines)

        while i < n:
            line = original_lines[i]
            stripped = line.strip()

            if stripped.startswith("[") and stripped.endswith("]"):
                if first_section_idx is None:
                    first_section_idx = i
                i += 1
                continue

            if first_section_idx is not None or stripped.startswith("#") or not stripped:
                i += 1
                continue

            if "=" in stripped:
                raw_k = stripped.split("=", 1)[0].strip().lower()
                canonical_k = CANONICAL_PARAM_MAP.get(raw_k)
                start_idx = i
                end_idx = i
                cur_line = original_lines[end_idx]
                while cur_line.rstrip("\r\n").rstrip().endswith("\\") and end_idx + 1 < n:
                    end_idx += 1
                    cur_line = original_lines[end_idx]

                if canonical_k in MANAGED_INDEX_PARAMS:
                    param_spans[canonical_k] = (start_idx, end_idx)
                i = end_idx + 1
                continue
            i += 1

        # Determine keys needing insertion (keys updated but not present in file)
        keys_to_insert = [k for k in validated_updates if k not in param_spans]

        # Reconstruct updated lines
        new_lines: List[str] = []
        inserted_new = False
        i = 0

        while i < n:
            # Insert missing parameters before the first section header
            if first_section_idx is not None and i == first_section_idx and not inserted_new:
                for k in keys_to_insert:
                    new_lines.extend(cls._serialize_param(k, validated_updates[k]))
                inserted_new = True

            matched_key: Optional[str] = None
            span_end = i
            for k, (s, e) in param_spans.items():
                if i == s:
                    matched_key = k
                    span_end = e
                    break

            if matched_key is not None:
                if matched_key in validated_updates:
                    new_lines.extend(cls._serialize_param(matched_key, validated_updates[matched_key]))
                else:
                    new_lines.extend(original_lines[i:span_end + 1])
                i = span_end + 1
            else:
                new_lines.append(original_lines[i])
                i += 1

        # If no section header was present, append new parameters at end of file
        if not inserted_new and keys_to_insert:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            for k in keys_to_insert:
                new_lines.extend(cls._serialize_param(k, validated_updates[k]))

        # Atomic write via temporary file
        target_dir = os.path.dirname(os.path.abspath(config_path))
        os.makedirs(target_dir, exist_ok=True)
        tmp_path = f"{config_path}.tmp.{os.getpid()}"

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
                f.flush()
                os.fsync(f.fileno())

            # Preserve file mode if original file exists
            if os.path.isfile(config_path):
                st = os.stat(config_path)
                try:
                    os.chmod(tmp_path, st.st_mode)
                except OSError:
                    pass

            os.replace(tmp_path, config_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return cls.get_index_config(conf_dir)
