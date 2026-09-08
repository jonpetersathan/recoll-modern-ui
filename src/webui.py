#!/usr/bin/env python3
"""
Recoll Modern UI - Clean, Modern Document Search Interface
Full-featured Python 3 Bottle Application for Recoll Search Engine
"""

import csv
import datetime
import glob
import hashlib
import io
import json
import logging
import mimetypes
import os
import shlex
import string
import sys
import time
import uuid
import warnings
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as urlquote

# Suppress ResourceWarning noise from Waitress/asyncore socket and file wrappers
warnings.filterwarnings("ignore", category=ResourceWarning)

import bottle
from recoll import recoll, rclextract, rclconfig

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL_MAP: Dict[str, int] = {
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'AUDIT': logging.INFO,
    'DEBUG': logging.DEBUG,
}


def get_configured_log_level() -> int:
    """Resolve logging level from RECOLL_LOGLEVEL environment variable."""
    env_level = os.environ.get('RECOLL_LOGLEVEL', 'INFO').strip().upper()
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)


logging.basicConfig(
    level=get_configured_log_level(),
    format='%(asctime)s [%(levelname)s] [RecollWeb] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("recoll.webui")
logger.setLevel(get_configured_log_level())


def get_client_ip() -> str:
    """Extract client IP address from proxy headers or remote socket."""
    for header in ('X-Forwarded-For', 'X-Real-IP'):
        val = bottle.request.headers.get(header)
        if val:
            return val.split(',')[0].strip()
    return bottle.request.environ.get('REMOTE_ADDR') or '127.0.0.1'


# Register MIME types
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
VIEWS_DIR = os.path.join(BASE_DIR, 'views')

if VIEWS_DIR not in bottle.TEMPLATE_PATH:
    bottle.TEMPLATE_PATH.insert(0, VIEWS_DIR)

# Temporary directory for generated files
TEMP_DIR = os.getenv("RECOLL_TMPDIR") or os.getenv("TMPDIR") or "/tmp"

# Default configuration options
DEFAULT_CONFIG: Dict[str, Any] = {
    'context': 30,
    'stem': 1,
    'timefmt': '%c',
    'dirdepth': 2,
    'maxchars': 500,
    'maxresults': 0,
    'perpage': 25,
    'csvfields': 'filename title author size time mtype url',
    'title_link': 'download',
    'collapsedups': 0,
    'synonyms': '',
    'mounts': {},
    'noresultlinks': 0,
    'logquery': 0,
    'shortenpaths': 1,
    'permlinks': 0,
    'res_permlink': 0,
}

# Available sort criteria
SORT_OPTIONS: List[Tuple[str, str]] = [
    ('relevancyrating', 'Relevancy'),
    ('mtime', 'Date'),
    ('url', 'Path'),
    ('filename', 'Filename'),
    ('fbytes', 'Size'),
    ('author', 'Author'),
]

# Supported document fields
DOCUMENT_FIELDS: List[str] = [
    'abstract', 'author', 'collapsecount', 'dbytes', 'dmtime',
    'fbytes', 'filename', 'fmtime', 'ipath', 'keywords',
    'mtime', 'mtype', 'origcharset', 'relevancyrating', 'sig',
    'size', 'title', 'url', 'label', 'snippet', 'time',
]

VALID_FILENAME_CHARS = f"_-{string.ascii_letters}{string.digits}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe HTTP attachment headers."""
    return "".join(c if c in VALID_FILENAME_CHARS else "_" for c in filename)


def format_timestamp(timestamp_str: str, date_format: str) -> str:
    """Format unix timestamp string into human-readable date format."""
    cleaned = (timestamp_str or '0').strip(',').strip()
    try:
        seconds = int(cleaned) if cleaned else 0
    except ValueError:
        seconds = 0
    return time.strftime(date_format, time.localtime(seconds))


def extract_common_prefix(path_list: List[str]) -> str:
    """Compute common directory prefix across multiple paths."""
    if not path_list:
        return ""
    split_paths = [[segment for segment in p.split("/") if segment] for p in path_list]
    common = split_paths[0]
    for p in split_paths[1:]:
        matched = []
        for idx, segment in enumerate(p):
            if idx >= len(common) or segment != common[idx]:
                break
            matched.append(segment)
        common = matched
        if not common:
            return ""
    return "/" + "/".join(common) + "/" if common else ""


class ConfigManager:
    """Resolves and manages Recoll configuration, environment, and user cookies."""

    @staticmethod
    def get_config() -> Dict[str, Any]:
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
        config['commonprefix'] = extract_common_prefix(topdirs)

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
        for key, is_int in fetches:
            val = rcl_conf.getConfParam(f"webui_{key}")
            if val is not None:
                DEFAULT_CONFIG[key] = int(val) if is_int else val

        # Load user cookies with fallback to defaults
        for key, default_val in DEFAULT_CONFIG.items():
            cookie_val = bottle.request.get_cookie(key)
            if cookie_val is not None and cookie_val not in ("None", ""):
                try:
                    config[key] = type(default_val)(cookie_val)
                except (ValueError, TypeError):
                    config[key] = default_val
            else:
                config[key] = default_val

        # Filter valid CSV fields
        valid_csv = [f for f in config['csvfields'].split() if f in DOCUMENT_FIELDS]
        config['csvfields'] = " ".join(valid_csv)
        config['fields'] = " ".join(DOCUMENT_FIELDS)

        # Mountpoints for file links
        config['mounts'] = {}
        for d in config['dirs']:
            cookie_mount = bottle.request.get_cookie(f"mount_{urlquote(d, '')}")
            conf_mount = rcl_conf.getConfParam(f"webui_mount_{d}")
            config['mounts'][d] = cookie_mount or conf_mount or f"file://{d}"

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
        """Resolve database path as bytes for Recoll C-bindings."""
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
        """Scan directory tree up to max_depth for folder scope dropdown."""
        dir_list: List[str] = []
        for top in top_dirs:
            encoded_top = top.encode('utf-8', 'surrogateescape')
            found_dirs = [encoded_top]
            for depth in range(1, max_depth + 1):
                pattern = encoded_top + b'/*' * depth
                found_dirs.extend(glob.glob(pattern))
            valid_dirs = [d for d in found_dirs if os.path.isdir(d)]
            parent_path = encoded_top.rsplit(b'/', 1)[0]
            relative_dirs = [d.replace(parent_path + b'/', b'', 1) for d in valid_dirs]
            dir_list.extend([d.decode('utf-8', 'surrogateescape') for d in relative_dirs])
        return ['<all>'] + dir_list


DEFAULT_SEARCH_FORM: Dict[str, Any] = {
    "id": "default",
    "name": "Advanced",
    "description": "Comprehensive search form supporting all Recoll query language features",
    "readonly": True,
    "fields": [
        {
            "id": "all_terms",
            "label": "All of these words",
            "type": "text",
            "placeholder": "e.g. system performance index",
            "helper": "Matches documents containing all specified terms",
            "query_format": "{value}",
        },
        {
            "id": "exact_phrase",
            "label": "This exact phrase",
            "type": "text",
            "placeholder": "e.g. neural network architectures",
            "helper": "Matches the exact phrase enclosed in quotes",
            "query_format": '"{value}"',
        },
        {
            "id": "any_terms",
            "label": "Any of these words",
            "type": "text",
            "placeholder": "e.g. machine artificial synthetic",
            "helper": "Matches documents containing one or more of these terms",
            "query_format": "or_terms",
        },
        {
            "id": "none_terms",
            "label": "None of these words",
            "type": "text",
            "placeholder": "e.g. deprecated draft temp",
            "helper": "Excludes documents containing any of these terms (-term)",
            "query_format": "not_terms",
        },
        {
            "id": "proximity_terms",
            "label": "Proximity search",
            "type": "text",
            "placeholder": "e.g. database query",
            "helper": "Matches terms appearing within 4 words of each other (\"...\"p4)",
            "query_format": "proximity",
            "slack": 4,
        },
        {
            "id": "filename",
            "label": "File Name",
            "type": "text",
            "placeholder": "e.g. *.pdf, 000.*, report_*",
            "helper": "Matches document filename with wildcard pattern support",
            "query_format": "filename:{value}",
        },
        {
            "id": "title",
            "label": "Document Title",
            "type": "text",
            "placeholder": "e.g. Specification, Analysis",
            "helper": "Searches document title metadata",
            "query_format": "title:{value}",
        },
        {
            "id": "author",
            "label": "Author",
            "type": "text",
            "placeholder": "e.g. Alice Smith",
            "helper": "Searches author or creator field",
            "query_format": "author:{value}",
        },
        {
            "id": "filetype",
            "label": "File Format",
            "type": "select",
            "helper": "Filter documents by MIME type or file extension",
            "options": [
                {"label": "Any Format", "query": ""},
                {"label": "PDF Document (mime:application/pdf)", "query": "mime:application/pdf"},
                {"label": "Plain Text (mime:text/plain)", "query": "mime:text/plain"},
                {"label": "HTML Document (mime:text/html)", "query": "mime:text/html"},
                {"label": "Word Document (ext:doc OR ext:docx)", "query": "ext:doc OR ext:docx"},
                {"label": "Spreadsheet (ext:xls OR ext:xlsx)", "query": "ext:xls OR ext:xlsx"},
                {"label": "Audio / Media (mime:audio/*)", "query": "mime:audio/*"},
            ],
        },
        {
            "id": "size_min",
            "label": "Minimum Size",
            "type": "text",
            "placeholder": "e.g. 10k, 1m",
            "helper": "Only files larger than specified size (k, m, g)",
            "query_format": "size>{value}",
        },
        {
            "id": "size_max",
            "label": "Maximum Size",
            "type": "text",
            "placeholder": "e.g. 50m",
            "helper": "Only files smaller than specified size (k, m, g)",
            "query_format": "size<{value}",
        },
        {
            "id": "dir_scope",
            "label": "Directory",
            "type": "text",
            "placeholder": "e.g. /data",
            "helper": "Restrict search to files inside this directory tree",
            "query_format": 'dir:"{value}"',
        },
    ],
}

SAMPLE_CUSTOM_FORM: Dict[str, Any] = {
    "id": "document_types",
    "name": "Document Classification Search",
    "description": "Fast categorical search by Document Type and keywords without knowing Recoll syntax",
    "readonly": False,
    "fields": [
        {
            "id": "document_type",
            "label": "Document Type",
            "type": "select",
            "helper": "Select a document classification filter",
            "options": [
                {"label": "All Document Types", "query": ""},
                {"label": "Sample 000 Files (filename:*000*)", "query": "filename:*000*"},
                {"label": "Sample 001 Files (filename:*001*)", "query": "filename:*001*"},
                {"label": "Sample 003 Files (filename:*003*)", "query": "filename:*003*"},
                {"label": "PDF Documents (mime:pdf)", "query": "mime:application/pdf"},
            ],
        },
        {
            "id": "keywords",
            "label": "Search Keywords",
            "type": "text",
            "placeholder": "Enter search terms...",
            "helper": "Search text inside documents matching the selected type",
            "query_format": "{value}",
        },
        {
            "id": "doc_title",
            "label": "Title Keyword",
            "type": "text",
            "placeholder": "e.g. report",
            "helper": "Filter by word in title",
            "query_format": "title:{value}",
        },
    ],
}


class SearchFormsManager:
    """Manages search form presets, persistence in forms.json, and compilation."""

    FORMS_FILENAME = "forms.json"
    LEGACY_FORMS_FILENAME = "custom_search_forms.json"

    @classmethod
    def get_forms_path(cls, conf_dir: Optional[str] = None) -> str:
        base_dir = conf_dir or os.environ.get('RECOLL_CONFDIR', os.path.expanduser('~/.recoll'))
        try:
            os.makedirs(base_dir, exist_ok=True)
            return os.path.join(base_dir, cls.FORMS_FILENAME)
        except Exception:
            return os.path.join(TEMP_DIR, cls.FORMS_FILENAME)

    @classmethod
    def get_forms(cls, conf_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        path = cls.get_forms_path(conf_dir)
        forms: List[Dict[str, Any]] = []

        if not os.path.isfile(path):
            legacy_path = os.path.join(os.path.dirname(path), cls.LEGACY_FORMS_FILENAME)
            if os.path.isfile(legacy_path):
                try:
                    with open(legacy_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                except Exception as exc:
                    logger.warning("Could not migrate legacy forms file %s: %s", legacy_path, exc)

        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'forms' in data:
                        forms = data['forms']
                    elif isinstance(data, list):
                        forms = data
            except Exception as exc:
                logger.error("Failed to load forms from %s: %s", path, exc)

        has_default = False
        sanitized_forms: List[Dict[str, Any]] = []

        for form in forms:
            if not isinstance(form, dict):
                continue
            if form.get('id') == 'default':
                form_copy = dict(DEFAULT_SEARCH_FORM)
                sanitized_forms.insert(0, form_copy)
                has_default = True
            else:
                form['readonly'] = False
                sanitized_forms.append(form)

        if not has_default:
            sanitized_forms.insert(0, dict(DEFAULT_SEARCH_FORM))

        if len(sanitized_forms) == 1:
            sanitized_forms.append(dict(SAMPLE_CUSTOM_FORM))
            cls.save_forms(conf_dir, sanitized_forms)

        return sanitized_forms

    @classmethod
    def save_forms(cls, conf_dir: Optional[str], forms: List[Dict[str, Any]]) -> bool:
        path = cls.get_forms_path(conf_dir)
        try:
            clean_forms: List[Dict[str, Any]] = [dict(DEFAULT_SEARCH_FORM)]
            for form in forms:
                if not isinstance(form, dict) or form.get('id') == 'default':
                    continue
                form_copy = dict(form)
                form_copy['readonly'] = False
                clean_forms.append(form_copy)

            temp_path = f"{path}.tmp.{os.getpid()}"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump({'forms': clean_forms}, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, path)
            return True
        except Exception as exc:
            logger.error("Failed to save forms to %s: %s", path, exc)
            return False

    @classmethod
    def save_custom_form(cls, conf_dir: Optional[str], form_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(form_data, dict):
            raise ValueError("Invalid form payload")
        form_id = str(form_data.get('id', '')).strip()
        if form_id == 'default':
            raise ValueError("The default search form is read-only and cannot be modified.")

        form_name = str(form_data.get('name', '')).strip()
        if not form_name:
            raise ValueError("Form name is required.")

        fields = form_data.get('fields', [])
        if not isinstance(fields, list) or len(fields) == 0:
            raise ValueError("A form must have at least one field.")

        clean_fields = []
        for f in fields:
            if not isinstance(f, dict):
                continue
            fid = str(f.get('id', '')).strip() or f"f_{uuid.uuid4().hex[:8]}"
            flabel = str(f.get('label', '')).strip() or "Unnamed Field"
            ftype = str(f.get('type', 'text')).strip()
            clean_field: Dict[str, Any] = {
                'id': fid,
                'label': flabel,
                'type': ftype,
                'helper': str(f.get('helper', '')).strip(),
                'placeholder': str(f.get('placeholder', '')).strip(),
            }
            if ftype == 'select':
                raw_options = f.get('options', [])
                clean_options = []
                for opt in raw_options:
                    if isinstance(opt, dict):
                        clean_options.append({
                            'label': str(opt.get('label', '')).strip(),
                            'query': str(opt.get('query', '')).strip(),
                        })
                clean_field['options'] = clean_options
            elif ftype == 'checkbox':
                clean_field['query'] = str(f.get('query', '')).strip()
            else:
                clean_field['type'] = 'text'
                clean_field['query_format'] = str(f.get('query_format', '{value}')).strip()
                if clean_field['query_format'] == 'proximity':
                    try:
                        clean_field['slack'] = int(f.get('slack', 4))
                    except Exception:
                        clean_field['slack'] = 4
            clean_fields.append(clean_field)

        if not clean_fields:
            raise ValueError("Form must have valid fields.")

        if not form_id:
            form_id = f"custom_{uuid.uuid4().hex[:8]}"

        new_form: Dict[str, Any] = {
            'id': form_id,
            'name': form_name,
            'description': str(form_data.get('description', '')).strip(),
            'readonly': False,
            'fields': clean_fields,
        }

        existing_forms = cls.get_forms(conf_dir)
        updated = False
        for idx, f in enumerate(existing_forms):
            if f.get('id') == form_id:
                existing_forms[idx] = new_form
                updated = True
                break

        if not updated:
            existing_forms.append(new_form)

        if not cls.save_forms(conf_dir, existing_forms):
            raise IOError("Failed to persist custom search forms to disk.")

        return new_form

    @classmethod
    def delete_custom_form(cls, conf_dir: Optional[str], form_id: str) -> bool:
        if form_id == 'default':
            raise ValueError("The default search form is read-only and cannot be deleted.")

        existing_forms = cls.get_forms(conf_dir)
        filtered = [f for f in existing_forms if f.get('id') != form_id]

        if len(filtered) == len(existing_forms):
            raise ValueError(f"Form '{form_id}' not found.")

        if not cls.save_forms(conf_dir, filtered):
            raise IOError("Failed to update custom search forms on disk.")
        return True

    @staticmethod
    def compile_query(form_def: Dict[str, Any], values: Dict[str, Any]) -> str:
        clauses = []
        for field in form_def.get('fields', []):
            fid = field.get('id')
            val = values.get(fid)
            ftype = field.get('type', 'text')
            if val is None or val == '':
                continue
            if ftype == 'select':
                opt_query = ''
                for opt in field.get('options', []):
                    if opt.get('query') == val or opt.get('label') == val:
                        opt_query = opt.get('query', '')
                        break
                if not opt_query and isinstance(val, str) and val:
                    opt_query = val
                if opt_query.strip():
                    clauses.append(opt_query.strip())
            elif ftype == 'checkbox':
                if val in (True, 1, '1', 'true', 'on', 'yes'):
                    q = field.get('query', '').strip()
                    if q:
                        clauses.append(q)
            elif ftype == 'text':
                val_str = str(val).strip()
                if not val_str:
                    continue
                fmt = field.get('query_format', '{value}')
                if fmt == '{value}':
                    clauses.append(val_str)
                elif fmt == '"{value}"':
                    clean_val = val_str.replace('"', '')
                    clauses.append(f'"{clean_val}"')
                elif fmt == 'or_terms':
                    terms = val_str.split()
                    if len(terms) > 1:
                        clauses.append(f"({' OR '.join(terms)})")
                    elif terms:
                        clauses.append(terms[0])
                elif fmt == 'not_terms':
                    terms = val_str.split()
                    if terms:
                        clauses.append(" ".join(f"-{t}" for t in terms))
                elif fmt == 'proximity':
                    slack = field.get('slack', 4)
                    clean_words = val_str.replace('"', '').strip()
                    clauses.append(f'"{clean_words}"p{slack}')
                elif '{value}' in fmt:
                    if (' ' in val_str and not val_str.startswith('"') and not val_str.endswith('"')
                            and any(fmt.startswith(p) for p in ('filename:', 'title:', 'author:', 'dir:'))):
                        clauses.append(fmt.replace('{value}', f'"{val_str}"'))
                    else:
                        clauses.append(fmt.replace('{value}', val_str))
                else:
                    clauses.append(f"{fmt} {val_str}")
        return " ".join(clauses).strip()


class SearchQuery:
    """Parses and formats search parameters from HTTP request."""

    @staticmethod
    def parse(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        req = bottle.request.query
        def_sort_idx = config.get('defsortidx', 0) if config else 0
        query_data = {
            'query': req.get('query', '').strip(),
            'before': req.get('before', '').strip(),
            'after': req.get('after', '').strip(),
            'dir': req.get('dir') or '<all>',
            'sort': req.get('sort') or SORT_OPTIONS[def_sort_idx][0],
            'ascending': int(req.get('ascending', 0) or 0),
            'page': int(req.get('page', 1) or 1),
            'highlight': int(req.get('highlight', 1) or 1),
            'snippets': int(req.get('snippets', 1) or 1),
        }
        if req.get('rcludi'):
            query_data['rcludi'] = req.get('rcludi')
        return query_data

    @staticmethod
    def to_recoll_string(query_data: Dict[str, Any]) -> str:
        """Build Recoll query search expression."""
        qs = query_data.get('query', '')
        after = query_data.get('after', '')
        before = query_data.get('before', '')
        if after or before:
            qs += f" date:{after}/{before}"
        scope_dir = query_data.get('dir', '<all>')
        if scope_dir != '<all>':
            qs += f' dir:"{scope_dir}" '
        return qs.strip()


class SnippetHighlighter:
    """Wraps matched terms in glassmorphic glowing search highlight spans."""

    def startMatch(self, idx: int) -> str:
        return '<span class="search-result-highlight">'

    def endMatch(self) -> str:
        return '</span>'


class RecollSearchEngine:
    """Manages Recoll database connection, query execution, and result processing."""

    @staticmethod
    def execute_search(query_data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int, datetime.timedelta]:
        start_time = datetime.datetime.now()
        results: List[Dict[str, Any]] = []

        qs = SearchQuery.to_recoll_string(query_data)
        if not qs.strip() and not query_data.get('rcludi'):
            return results, 0, datetime.datetime.now() - start_time

        query_obj, db_obj = RecollSearchEngine._init_query(query_data, config)
        total_count = query_obj.rowcount

        rcludi = query_data.get('rcludi')
        if rcludi:
            total_count = 1
            query_data['page'] = 1

        max_res = config.get('maxresults', 0)
        if max_res > 0 and total_count > max_res:
            total_count = max_res

        per_page = config.get('perpage', 25)
        if per_page == 0:
            per_page = total_count
        page = max(query_data.get('page', 1), 1)

        offset = (page - 1) * per_page

        if query_obj.rowcount > 0:
            if isinstance(query_obj.next, int):
                query_obj.next = offset
            else:
                query_obj.scroll(offset, mode='absolute')

        highlighter = SnippetHighlighter() if query_data.get('highlight', 1) else None

        while len(results) < per_page:
            try:
                doc = query_obj.fetchone()
                if not doc:
                    break
                if rcludi and getattr(doc, 'rcludi', None) != rcludi:
                    continue
            except Exception:
                break

            item: Dict[str, Any] = {}
            for field in DOCUMENT_FIELDS:
                val = getattr(doc, field, '')
                item[field] = val if val is not None else ''

            # Handle PDF first-match page positioning
            if getattr(doc, 'mtype', '') == 'application/pdf' and item.get('url', '').startswith('file://'):
                try:
                    pagenum, term = query_obj.getfirstmatchpage(doc)
                    if pagenum > 0:
                        item['url'] += f"#page={pagenum}&search={urlquote(term)}"
                except Exception:
                    pass

            item['label'] = item.get('title') or item.get('filename') or '?'
            item['sha'] = hashlib.sha1(f"{item.get('url', '')}{item.get('ipath', '')}".encode('utf-8')).hexdigest()
            item['time'] = format_timestamp(str(item.get('mtime', 0)), config['timefmt'])
            item['rcludi'] = getattr(doc, 'rcludi', '')

            # Snippet abstract generation
            if query_data.get('snippets', 1):
                if highlighter:
                    item['snippet'] = query_obj.makedocabstract(doc, methods=highlighter)
                else:
                    item['snippet'] = query_obj.makedocabstract(doc)
                if not item.get('snippet'):
                    item['snippet'] = getattr(doc, 'abstract', '')

            results.append(item)
            if rcludi:
                break

        elapsed = datetime.datetime.now() - start_time
        return results, total_count, elapsed

    @staticmethod
    def _init_query(query_data: Dict[str, Any], config: Dict[str, Any]):
        conf_dir = config['confdir']
        extra_dbs: List[bytes] = []

        scope_dir = query_data.get('dir', '<all>')
        if scope_dir == '<all>':
            if config.get('extraconfdirs'):
                extra_dbs.extend(config['extradbs'])
        else:
            matching_confs = [
                conf for d, conf in config['dirs'].items()
                if os.path.commonprefix([os.path.basename(d), scope_dir]) == os.path.basename(d)
            ]
            if not matching_confs:
                bottle.abort(400, f"No matching database for search directory: {scope_dir}")
            conf_dir = matching_confs[0]
            if len(matching_confs) > 1:
                extra_dbs.extend([ConfigManager.resolve_db_dir(c) for c in matching_confs[1:]])

        if config.get('extradbs'):
            extra_dbs.extend(config['extradbs'])

        db = recoll.connect(conf_dir, extra_dbs=extra_dbs)

        synonyms = config.get('synonyms')
        if synonyms and synonyms != 'None':
            try:
                db.setSynonymsFile(synonyms)
            except Exception:
                pass

        db.setAbstractParams(config.get('maxchars', 500), config.get('context', 30))
        query_obj = db.query()
        query_obj.sortby(query_data['sort'], query_data['ascending'])

        qs = SearchQuery.to_recoll_string(query_data)
        if config.get('queryfrag'):
            qs += f" {config['queryfrag']}"

        query_obj.execute(
            qs,
            config.get('stem', 1),
            config.get('stemlang', 'english'),
            collapseduplicates=config.get('collapsedups', 0)
        )
        return query_obj, db


# ============================================================================
# Route Handlers
# ============================================================================

@bottle.route('/favicon.ico')
def serve_favicon():
    """Serve favicon image."""
    for fn in ('logo.svg', 'recoll.png'):
        path = os.path.join(STATIC_DIR, fn)
        if os.path.isfile(path):
            return bottle.static_file(fn, root=STATIC_DIR)
    bottle.abort(404, 'Favicon not found')


@bottle.route('/robots.txt')
def serve_robots():
    """Serve basic robots.txt."""
    bottle.response.content_type = 'text/plain'
    return "User-agent: *\nDisallow: /\n"


@bottle.route('/static/<path:path>')
@bottle.route('/static/:path#.+#')
def serve_static(path: str):
    """Serve static CSS, JS, SVG, and image assets."""
    return bottle.static_file(path, root=STATIC_DIR)


@bottle.route('/staticdoc/:path#.+#')
def serve_staticdoc(path: str):
    """Serve temporary document files (e.g. PDF first match views)."""
    if not TEMP_DIR:
        return ""
    filename = os.path.basename(path)
    if not filename.startswith("rcltmp"):
        bottle.abort(401, 'Bad temporary file name')
    return bottle.static_file(path, root=TEMP_DIR)


@bottle.route('/')
def main_page():
    """Render main search homepage."""
    config = ConfigManager.get_config()
    dirs = ConfigManager.get_directory_tree(list(config['dirs'].keys()), config['dirdepth'])
    query_data = SearchQuery.parse(config)
    forms = SearchFormsManager.get_forms(config['confdir'])
    bottle.response.headers['Vary'] = 'Cookie'
    return bottle.template(
        'main',
        dirs=dirs,
        query=query_data,
        sorts=SORT_OPTIONS,
        config=config,
        forms=forms,
        forms_json=json.dumps(forms),
    )


@bottle.route('/results')
def search_results():
    """Execute query and render results page."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    qs = SearchQuery.to_recoll_string(query_data)
    client_ip = get_client_ip()

    try:
        res, total_count, elapsed = RecollSearchEngine.execute_search(query_data, config)
        logger.info(
            "SEARCH: terms='%s' [dir='%s', sort='%s', page=%d] -> %d results (%.3fs) from %s",
            query_data.get('query', ''),
            query_data.get('dir', '<all>'),
            query_data.get('sort', 'relevancyrating'),
            query_data.get('page', 1),
            total_count,
            elapsed.total_seconds(),
            client_ip,
        )
    except Exception as exc:
        exc_msg = str(exc)
        logger.error("SEARCH_ERROR: query='%s' failed: %s (Client: %s)", qs, exc_msg, client_ip, exc_info=True)
        bottle.response.status = 500
        if "Can't open index" in exc_msg or "xapiandb" in exc_msg:
            return render_error_page(
                code=500,
                title="Search Index Unavailable",
                desc="Recoll could not open the search index at the configured location (/root/.recoll/xapiandb). Ensure the index has been built (e.g. running 'recollindex') or that the configuration volume is mounted.",
                details=exc_msg,
                is_warning=False,
            )
        return render_error_page(
            code=500,
            title="Search Execution Error",
            desc="An unexpected error occurred while executing the search query.",
            details=exc_msg,
            is_warning=False,
        )

    dirs = ConfigManager.get_directory_tree(list(config['dirs'].keys()), config['dirdepth'])
    forms = SearchFormsManager.get_forms(config['confdir'])
    bottle.response.headers['Vary'] = 'Cookie'
    bottle.response.headers['No-Vary-Search'] = 'key-order'

    return bottle.template(
        'results',
        res=res,
        time=elapsed,
        query=query_data,
        dirs=dirs,
        qs=qs,
        sorts=SORT_OPTIONS,
        config=config,
        query_string=bottle.request.query_string,
        nres=total_count,
        forms=forms,
        forms_json=json.dumps(forms),
    )


@bottle.route('/preview/<resnum:int>')
def preview_document(resnum: int):
    """Extract document text and render preview with highlighting."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    client_ip = get_client_ip()

    try:
        query_obj, db_obj = RecollSearchEngine._init_query(query_data, config)
    except Exception as exc:
        logger.error("PREVIEW_ERROR: Init query failed for doc #%d: %s (Client: %s)", resnum, exc, client_ip)
        bottle.response.status = 500
        return render_error_page(
            code=500,
            title="Search Index Unavailable",
            desc="Recoll could not open the search index for preview.",
            details=str(exc),
            is_warning=False,
        )

    rcludi = query_data.get('rcludi')
    if rcludi:
        doc = db_obj.getDoc(rcludi)
    else:
        if resnum >= query_obj.rowcount:
            logger.warning("PREVIEW_WARN: Doc #%d not found (total: %d) (Client: %s)", resnum, query_obj.rowcount, client_ip)
            bottle.response.status = 404
            return render_error_page(
                code=404,
                title="Result Not Found",
                desc=f"The requested result index {resnum} does not exist.",
                is_warning=True,
            )
        query_obj.scroll(resnum)
        doc = query_obj.fetchone()

    doc_label = getattr(doc, 'title', None) or getattr(doc, 'filename', None) or '?'
    doc_url = getattr(doc, 'url', '')
    logger.info("PREVIEW: doc #%d - '%s' [url: %s] (Client: %s)", resnum, doc_label, doc_url, client_ip)

    extractor = rclextract.Extractor(doc)
    extracted_doc = extractor.textextract(doc.ipath)

    is_html = 1 if extracted_doc.mimetype == 'text/html' else 0
    bottle.response.content_type = 'text/html; charset=utf-8' if is_html else 'text/plain; charset=utf-8'

    if query_data.get('highlight', 1):
        highlighter = SnippetHighlighter()
        highlighted_text = query_obj.highlight(extracted_doc.text, ishtml=is_html, methods=highlighter)
        head_pos = highlighted_text.find('<head>')
        css_ref = '<link rel="stylesheet" type="text/css" href="/static/style.css">'
        if head_pos >= 0:
            final_html = highlighted_text[:head_pos + 6] + css_ref + highlighted_text[head_pos + 6:]
        else:
            final_html = (
                f'<html><head>{css_ref}'
                '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body>'
                f'{highlighted_text}</body></html>'
            )
        bottle.response.content_type = 'text/html; charset=utf-8'
        return final_html

    bottle.response.headers['Vary'] = 'Cookie'
    return extracted_doc.text


@bottle.route('/download/<resnum:int>')
def download_document(resnum: int):
    """Download original document or open matched PDF page."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    client_ip = get_client_ip()

    try:
        query_obj, db_obj = RecollSearchEngine._init_query(query_data, config)
    except Exception as exc:
        logger.error("DOWNLOAD_ERROR: Init query failed for doc #%d: %s (Client: %s)", resnum, exc, client_ip)
        bottle.response.status = 500
        return render_error_page(
            code=500,
            title="Search Index Unavailable",
            desc="Recoll could not open the search index for download.",
            details=str(exc),
            is_warning=False,
        )

    rcludi = query_data.get('rcludi')
    if rcludi:
        doc = db_obj.getDoc(rcludi)
    else:
        if resnum >= query_obj.rowcount:
            logger.warning("DOWNLOAD_WARN: Doc #%d not found (total: %d) (Client: %s)", resnum, query_obj.rowcount, client_ip)
            bottle.response.status = 404
            return render_error_page(
                code=404,
                title="Result Not Found",
                desc=f"The requested result index {resnum} does not exist.",
                is_warning=True,
            )
        query_obj.scroll(resnum)
        doc = query_obj.fetchone()

    extractor = rclextract.Extractor(doc)
    doc_path = extractor.idoctofile(doc.ipath, doc.mimetype)
    filename = getattr(doc, 'filename', None) or os.path.basename(doc_path)
    file_size = os.stat(doc_path).st_size

    logger.info("DOWNLOAD: doc #%d - '%s' [size: %d bytes, url: %s] (Client: %s)", resnum, filename, file_size, getattr(doc, 'url', ''), client_ip)

    pagenum = -1
    term = ""
    try:
        pagenum, term = query_obj.getfirstmatchpage(doc)
    except Exception:
        pass

    if config.get('rclc_pdfposition') and pagenum != -1 and getattr(doc, 'mimetype', '') == 'application/pdf':
        tmp_fn = f"rcltmp{os.getpid()}_{os.path.basename(doc_path)}"
        tmp_dest = os.path.join(TEMP_DIR, tmp_fn)
        with open(doc_path, 'rb') as src, open(tmp_dest, 'wb') as dst:
            dst.write(src.read())
        pdf_url = f"/staticdoc/{tmp_fn}#page={pagenum}&search={urlquote(term)}"
        return f'<html><head></head><body><script>window.location.replace("{pdf_url}");</script></body></html>'

    bottle.response.content_type = doc.mimetype
    bottle.response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    bottle.response.headers['Content-Length'] = file_size
    file_handle = open(doc_path, 'rb')
    try:
        os.unlink(doc_path)
    except Exception:
        pass
    bottle.response.headers['Vary'] = 'Cookie'
    return file_handle


@bottle.route('/open/<resnum:int>')
def open_document(resnum: int):
    """Open original document inline in browser."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    client_ip = get_client_ip()

    try:
        query_obj, db_obj = RecollSearchEngine._init_query(query_data, config)
    except Exception as exc:
        logger.error("OPEN_ERROR: Init query failed for doc #%d: %s (Client: %s)", resnum, exc, client_ip)
        bottle.response.status = 500
        return render_error_page(
            code=500,
            title="Search Index Unavailable",
            desc="Recoll could not open the search index for document view.",
            details=str(exc),
            is_warning=False,
        )

    rcludi = query_data.get('rcludi')
    if rcludi:
        doc = db_obj.getDoc(rcludi)
    else:
        if resnum >= query_obj.rowcount:
            logger.warning("OPEN_WARN: Doc #%d not found (total: %d) (Client: %s)", resnum, query_obj.rowcount, client_ip)
            bottle.response.status = 404
            return render_error_page(
                code=404,
                title="Result Not Found",
                desc=f"The requested result index {resnum} does not exist.",
                is_warning=True,
            )
        query_obj.scroll(resnum)
        doc = query_obj.fetchone()

    extractor = rclextract.Extractor(doc)
    doc_path = extractor.idoctofile(doc.ipath, doc.mimetype)
    filename = getattr(doc, 'filename', None) or os.path.basename(doc_path)
    file_size = os.stat(doc_path).st_size

    logger.info("OPEN: doc #%d - '%s' [size: %d bytes, url: %s] (Client: %s)", resnum, filename, file_size, getattr(doc, 'url', ''), client_ip)

    bottle.response.content_type = doc.mimetype
    bottle.response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    bottle.response.headers['Content-Length'] = file_size
    file_handle = open(doc_path, 'rb')
    try:
        os.unlink(doc_path)
    except Exception:
        pass
    bottle.response.headers['Vary'] = 'Cookie'
    return file_handle


@bottle.route('/json')
def export_json():
    """Export search results in JSON format."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    qs = SearchQuery.to_recoll_string(query_data)
    client_ip = get_client_ip()

    res, total_count, _ = RecollSearchEngine.execute_search(query_data, config)
    logger.info("EXPORT_JSON: query='%s' (terms='%s') -> %d records exported to %s", qs, query_data.get('query', ''), total_count, client_ip)

    bottle.response.headers['Content-Type'] = 'application/json'
    bottle.response.headers['Content-Disposition'] = f'attachment; filename="recoll-{sanitize_filename(qs)}.json"'

    import json
    return json.dumps({'query': query_data, 'results': res, 'total': total_count})


@bottle.route('/csv')
def export_csv():
    """Export document metadata matching query to CSV."""
    config = ConfigManager.get_config()
    query_data = SearchQuery.parse(config)
    query_data['page'] = 0
    query_data['snippets'] = 0
    qs = SearchQuery.to_recoll_string(query_data)
    client_ip = get_client_ip()

    res, _, _ = RecollSearchEngine.execute_search(query_data, config)
    logger.info("EXPORT_CSV: query='%s' (terms='%s') -> %d records exported to %s", qs, query_data.get('query', ''), len(res), client_ip)

    bottle.response.headers['Content-Type'] = 'text/csv'
    bottle.response.headers['Content-Disposition'] = f'attachment; filename="recoll-{sanitize_filename(qs)}.csv"'

    string_io = io.StringIO()
    writer = csv.writer(string_io)
    fields = config['csvfields'].split()
    writer.writerow(fields)
    for doc in res:
        writer.writerow([doc.get(f, '') for f in fields])
    return string_io.getvalue().strip("\r\n")


@bottle.route('/settings')
def settings_page():
    """Render configuration and preferences dashboard."""
    config = ConfigManager.get_config()
    forms = SearchFormsManager.get_forms(config['confdir'])
    settings_vars = dict(config)
    settings_vars['forms'] = forms
    settings_vars['forms_json'] = json.dumps(forms)
    return bottle.template('settings', **settings_vars)


@bottle.route('/api/forms', method=['GET'])
def api_get_forms():
    """Get all available search forms."""
    config = ConfigManager.get_config()
    forms = SearchFormsManager.get_forms(config['confdir'])
    bottle.response.content_type = 'application/json'
    return json.dumps({'forms': forms})


@bottle.route('/api/forms', method=['POST'])
def api_save_form():
    """Create or update a custom search form."""
    config = ConfigManager.get_config()
    try:
        data = bottle.request.json
        if not data:
            raw_body = bottle.request.body.read().decode('utf-8')
            data = json.loads(raw_body) if raw_body else {}
        saved_form = SearchFormsManager.save_custom_form(config['confdir'], data)
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': True, 'form': saved_form})
    except ValueError as val_err:
        bottle.response.status = 400
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': False, 'error': str(val_err)})
    except Exception as exc:
        bottle.response.status = 500
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': False, 'error': str(exc)})


@bottle.route('/api/forms/delete', method=['POST'])
def api_delete_form():
    """Delete a custom search form."""
    config = ConfigManager.get_config()
    try:
        data = bottle.request.json
        if not data:
            raw_body = bottle.request.body.read().decode('utf-8')
            data = json.loads(raw_body) if raw_body else {}
        form_id = data.get('id') if isinstance(data, dict) else None
        if not form_id:
            bottle.response.status = 400
            bottle.response.content_type = 'application/json'
            return json.dumps({'success': False, 'error': 'Missing form ID'})
        SearchFormsManager.delete_custom_form(config['confdir'], form_id)
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': True})
    except ValueError as val_err:
        bottle.response.status = 400
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': False, 'error': str(val_err)})
    except Exception as exc:
        bottle.response.status = 500
        bottle.response.content_type = 'application/json'
        return json.dumps({'success': False, 'error': str(exc)})


@bottle.route('/set')
def save_settings():
    """Save user preferences as browser cookies."""
    config = ConfigManager.get_config()
    for key in DEFAULT_CONFIG.keys():
        val = bottle.request.query.get(key)
        if val is not None:
            bottle.response.set_cookie(key, str(val), max_age=315360000, expires=315360000)
    for d in config['dirs']:
        cookie_name = f"mount_{urlquote(d, '')}"
        mount_val = bottle.request.query.get(cookie_name)
        if mount_val is not None:
            bottle.response.set_cookie(cookie_name, str(mount_val), max_age=315360000, expires=315360000)
    bottle.redirect('./')


@bottle.route('/osd.xml')
def opensearch_manifest():
    """Serve OpenSearch XML description."""
    parts = bottle.request.urlparts
    return bottle.template('osd', url=f"{parts.scheme}://{parts.netloc}")


# ============================================================================
# Error Handlers
# ============================================================================

def render_error_page(code: Any = 500, title: Optional[str] = None, desc: Optional[str] = None,
                      details: Optional[str] = None, is_warning: Optional[bool] = None) -> str:
    """Render custom dark glassmorphic error card matching proxy theme."""
    error_defaults = {
        400: ('Bad Request', 'The request could not be understood by the server.', True),
        401: ('Unauthorized', 'Authentication is required to access this resource.', True),
        403: ('Access Forbidden', 'You do not have permission to access the requested resource.', True),
        404: ('Page Not Found', 'The requested page or document could not be found. Check the URL for spelling errors.', True),
        500: ('Internal Server Error', 'An error occurred while processing your search request.', False),
        502: ('Bad Gateway', 'The search backend service is unavailable or restarting.', False),
        503: ('Service Unavailable', 'The search service is temporarily overloaded or down for maintenance.', False),
        504: ('Gateway Timeout', 'The upstream service took too long to respond to the request.', False),
    }
    numeric_code = int(code) if str(code).isdigit() else 500
    def_title, def_desc, def_warn = error_defaults.get(numeric_code, ('Unexpected Error', 'An unexpected error occurred.', False))

    return bottle.template(
        'error',
        code=code,
        title=title or def_title,
        desc=desc or def_desc,
        details=details,
        is_warning=is_warning if is_warning is not None else def_warn,
    )


@bottle.error(400)
@bottle.error(401)
@bottle.error(403)
@bottle.error(404)
@bottle.error(500)
@bottle.error(502)
@bottle.error(503)
@bottle.error(504)
def custom_error_handler(error):
    code = getattr(error, 'status_code', 500)
    details = getattr(error, 'body', None) or getattr(error, 'exception', None)
    details_str = str(details) if details else None
    client_ip = get_client_ip()

    if code >= 500:
        logger.error("HTTP %d Error: %s (Path: %s, Client: %s)", code, details_str or 'Internal Error', bottle.request.path, client_ip)
        if getattr(error, 'exception', None):
            exc_str = str(error.exception)
            if "Can't open index" in exc_str or "xapiandb" in exc_str:
                return render_error_page(
                    code=500,
                    title="Search Index Unavailable",
                    desc="Recoll could not open the search index at the configured location. Ensure that indexing has been run (e.g. 'recollindex') or that the configuration volume is mounted.",
                    details=exc_str,
                    is_warning=False,
                )
    elif bottle.request.path not in ('/favicon.ico', '/robots.txt'):
        logger.warning("HTTP %d Warning: %s (Path: %s, Client: %s)", code, details_str or 'Client Error', bottle.request.path, client_ip)

    return render_error_page(code=code, details=details_str if (getattr(error, 'exception', None) and bottle.DEBUG) else None)


def custom_default_error_handler(res):
    code = getattr(res, 'status_code', 500)
    details = getattr(res, 'body', None) or getattr(res, 'exception', None)
    details_str = str(details) if details else None
    client_ip = get_client_ip()

    if code >= 500:
        logger.error("HTTP %d Error: %s (Path: %s, Client: %s)", code, details_str or 'Internal Error', bottle.request.path, client_ip)
        if getattr(res, 'exception', None):
            exc_str = str(res.exception)
            if "Can't open index" in exc_str or "xapiandb" in exc_str:
                return render_error_page(
                    code=500,
                    title="Search Index Unavailable",
                    desc="Recoll could not open the search index at the configured location. Ensure that indexing has been run (e.g. 'recollindex') or that the configuration volume is mounted.",
                    details=exc_str,
                    is_warning=False,
                )
    elif bottle.request.path not in ('/favicon.ico', '/robots.txt'):
        logger.warning("HTTP %d Warning: %s (Path: %s, Client: %s)", code, details_str or 'Client Error', bottle.request.path, client_ip)

    return render_error_page(code=code, details=details_str if (getattr(res, 'exception', None) and bottle.DEBUG) else None)


bottle.default_app().default_error_handler = custom_default_error_handler

# For WSGI deployments
app = application = bottle.default_app()
