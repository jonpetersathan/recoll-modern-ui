"""
Constants and default configuration parameters for Recoll Modern UI.
"""

import os
import string
from typing import Any, Dict, List, Tuple

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
VIEWS_DIR = os.path.join(BASE_DIR, 'views')

# Temporary and export directories
TEMP_DIR = os.getenv("RECOLL_TMPDIR") or os.getenv("TMPDIR") or "/tmp"

# Export directory for ZIP archives
_default_export_dir = os.getenv("RECOLL_EXPORT_DIR") or "/export"
try:
    os.makedirs(_default_export_dir, exist_ok=True)
    EXPORT_DIR = _default_export_dir
except Exception:
    EXPORT_DIR = os.path.join(TEMP_DIR, "export")
    os.makedirs(EXPORT_DIR, exist_ok=True)

# Metadata rules configuration filename
METADATA_RULES_FILENAME = "metadata_rules.json"

# Default configuration settings
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

# Available sort criteria for Recoll query execution
SORT_OPTIONS: List[Tuple[str, str]] = [
    ('relevancyrating', 'Relevancy'),
    ('mtime', 'Date'),
    ('url', 'Path'),
    ('filename', 'Filename'),
    ('fbytes', 'Size'),
    ('author', 'Author'),
]

# Supported document metadata fields
DOCUMENT_FIELDS: List[str] = [
    'abstract', 'author', 'collapsecount', 'dbytes', 'dmtime',
    'fbytes', 'filename', 'fmtime', 'ipath', 'keywords',
    'mtime', 'mtype', 'mtype_label', 'origcharset', 'relevancyrating', 'sig',
    'size', 'title', 'url', 'label', 'snippet', 'time',
]

VALID_FILENAME_CHARS = f"_-{string.ascii_letters}{string.digits}"

CUSTOM_LOGO_FILENAMES: Tuple[str, ...] = ('logo.png', 'logo.jpg', 'logo.jpeg', 'logo.svg')

# Map of standard MIME types to user-friendly descriptive labels
MIME_LABELS: Dict[str, str] = {
    # Documents
    'application/pdf': 'PDF Document',
    'text/plain': 'Plain Text',
    'text/html': 'HTML Document',
    'application/msword': 'Word Document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word Document',
    'application/vnd.wordperfect': 'WordPerfect Document',
    'text/rtf': 'Rich Text',
    'application/rtf': 'Rich Text',
    'application/vnd.oasis.opendocument.text': 'OpenDocument Text',
    'application/vnd.oasis.opendocument.spreadsheet': 'Spreadsheet',
    'application/vnd.oasis.opendocument.presentation': 'Presentation',

    # Spreadsheets & Databases
    'application/vnd.ms-excel': 'Spreadsheet',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Spreadsheet',
    'text/x-csv': 'CSV File',
    'text/csv': 'CSV File',
    'application/x-dbf': 'Database File',

    # Emails & Messaging
    'message/rfc822': 'Email',
    'application/vnd.ms-outlook': 'Email',

    # Presentations
    'application/vnd.ms-powerpoint': 'Presentation',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'Presentation',

    # Source code & Data
    'text/x-python': 'Python Source',
    'text/x-java': 'Java Source',
    'text/x-c': 'C Source',
    'text/x-c++': 'C++ Source',
    'text/x-fortran': 'Fortran Source',
    'text/x-shellscript': 'Shell Script',
    'text/xml': 'XML Document',
    'application/xml': 'XML Document',
    'application/json': 'JSON Document',
    'application/javascript': 'JavaScript Source',
    'text/javascript': 'JavaScript Source',
    'text/markdown': 'Markdown Document',

    # Archives
    'application/zip': 'Archive',
    'application/x-tar': 'Archive',
    'application/gzip': 'Archive',
    'application/x-bzip2': 'Archive',
    'application/x-7z-compressed': 'Archive',
    'application/x-rar-compressed': 'Archive',

    # Media & Images
    'application/postscript': 'PostScript Document',
    'application/x-shockwave-flash': 'Flash File',
    'image/fits': 'FITS Image',
    'image/jpeg': 'JPEG Image',
    'image/png': 'PNG Image',
    'image/gif': 'GIF Image',
    'image/svg+xml': 'SVG Image',
    'image/webp': 'WebP Image',
    'image/tiff': 'TIFF Image',
    'audio/mpeg': 'Audio / Media',
    'audio/x-wav': 'Audio / Media',
    'audio/ogg': 'Audio / Media',
    'audio/flac': 'Audio / Media',
    'video/mp4': 'Video / Media',
    'video/quicktime': 'Video / Media',

    # Generic
    'inode/directory': 'Directory',
    'application/octet-stream': 'Binary Data',
}

# Default comprehensive advanced search form schema (read-only)
DEFAULT_SEARCH_FORM: Dict[str, Any] = {
    "id": "default",
    "name": "Advanced Search",
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
            "helper": "Excludes documents containing any of these terms",
            "query_format": "not_terms",
        },
        {
            "id": "proximity_terms",
            "label": "Proximity search",
            "type": "text",
            "placeholder": "e.g. database query",
            "helper": "Matches terms appearing within 4 words of each other",
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
            "multiple": True,
            "helper": "Filter documents by MIME type or file extension",
            "options": [
                {"label": "Any Format", "query": ""},
                {"label": "PDF Document (mime:application/pdf)", "query": "mime:application/pdf"},
                {"label": "Plain Text (mime:text/plain)", "query": "mime:text/plain"},
                {"label": "HTML Document (mime:text/html)", "query": "mime:text/html"},
                {"label": "Word Document (ext:doc OR ext:docx)", "query": "ext:doc OR ext:docx"},
                {"label": "Spreadsheet (ext:xls OR ext:xlsx)", "query": "ext:xls OR ext:xlsx"},
                {"label": "CSV File (ext:csv)", "query": "ext:csv"},
                {"label": "Email (ext:eml OR ext:msg)", "query": "ext:eml OR ext:msg"},
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

