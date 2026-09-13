"""
Helper utilities for MIME formatting, filename sanitization, timestamps, and JSON requests.
"""

import datetime
import hashlib
import json
import mimetypes
import os
import time
from typing import Any, Dict, Iterable, List, Optional

try:
    import bottle
except ImportError:
    bottle = None

from recollweb.constants import MIME_LABELS, VALID_FILENAME_CHARS


def format_mimetype_label(mtype: str, filename: str = '') -> str:
    """
    Format MIME type into a human-readable descriptive label (e.g. 'PDF Document', 'Word Document').
    Falls back to file extension or guessed MIME type if unassigned.
    """
    clean = (mtype or '').strip()
    if (not clean or clean == 'application/octet-stream') and filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            clean = guessed

    if not clean:
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        return f"{ext.upper()} File" if ext else "Unknown File"

    if clean in MIME_LABELS:
        return MIME_LABELS[clean]

    if clean.startswith('audio/'):
        return "Audio / Media"
    if clean.startswith('video/'):
        return "Video / Media"
    if clean.startswith('image/'):
        subtype = clean.split('/', 1)[1].replace('x-', '').replace('-', ' ').title()
        return f"{subtype} Image"
    if clean.startswith('text/'):
        subtype = clean.split('/', 1)[1].replace('x-', '').replace('-', ' ').title()
        return subtype if subtype.endswith('Text') else f"{subtype} Text"
    if '/' in clean:
        _, minor = clean.split('/', 1)
        clean_sub = minor.replace('vnd.', '').replace('x-', '').replace('-', ' ').title()
        return f"{clean_sub} Document"

    return clean.title() if clean else "Unknown File"


def format_size_human(size: Any) -> str:
    """
    Format byte count into human-readable representation (e.g. 500 B, 12.5 KB, 1.2 MB).
    Accepts int, float, or numeric string. Returns empty string if invalid or None.
    """
    if size is None or size == '':
        return ''
    try:
        size_bytes = float(size)
    except (ValueError, TypeError):
        return ''
    if size_bytes < 0:
        return ''
    if size_bytes < 1024:
        return f"{int(size_bytes)} B"
    num = size_bytes
    for unit in ['KB', 'MB', 'GB', 'TB']:
        num /= 1024.0
        if num < 1024.0 or unit == 'TB':
            return f"{num:.1f} {unit}"
    return f"{num:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe HTTP attachment headers, stripping invalid characters.
    """
    return "".join(c if c in VALID_FILENAME_CHARS else "_" for c in filename)


def compute_export_hash(query_str: str, selected_ids: Optional[Iterable[str]] = None) -> str:
    """
    Compute deterministic SHA-256 hash of search query string and selected records.
    Returns the first 16 hexadecimal characters of the hash.
    """
    parts = [str(query_str or '').strip()]
    if selected_ids:
        sorted_ids = sorted(str(s).strip() for s in selected_ids if s and str(s).strip())
        if sorted_ids:
            parts.append(",".join(sorted_ids))
    raw_content = ":".join(parts)
    return hashlib.sha256(raw_content.encode('utf-8')).hexdigest()[:16]


def generate_export_filename(
    config: Dict[str, Any],
    query_str: str = "",
    selected_ids: Optional[Iterable[str]] = None,
    ext: str = "zip",
    custom_filename: Optional[str] = None,
    now: Optional[datetime.datetime] = None
) -> str:
    """
    Generate the export filename according to the user's configured mode or custom input:
    - Custom override (if custom_filename provided): sanitized custom filename with extension.
    - Timestamp (default): recoll_YYYYMMDD_hhmmss.<ext>
    - Ask every time: prompted in UI; uses pattern as default value.
    - Query hash: <hash16>.<ext>
    - Custom: pattern replacing @HASH, @YYYY, @MM, @DD, @hh, @mm, @ss.
    """
    clean_ext = ext.lstrip('.').lower()

    if custom_filename and str(custom_filename).strip():
        base = str(custom_filename).strip()
        if base.lower().endswith(f".{clean_ext}"):
            base = base[:-len(f".{clean_ext}")]
        safe_base = "".join(c if c in (VALID_FILENAME_CHARS + ".-") else "_" for c in base).strip("._")
        if not safe_base:
            safe_base = "export"
        return f"{safe_base}.{clean_ext}"

    if now is None:
        now = datetime.datetime.now()

    mode = str(config.get('export_filename_mode') or 'timestamp').lower().strip()

    if mode == 'query_hash':
        h = compute_export_hash(query_str, selected_ids)
        return f"{h}.{clean_ext}"

    if mode in ('custom', 'ask'):
        pattern = str(config.get('export_filename_pattern') or 'recoll_@YYYY@MM@DD_@hh@mm@ss')
        h = compute_export_hash(query_str, selected_ids)

        # Keyword substitutions
        # @MM = 2-digit month, @mm = 2-digit minute
        pattern = pattern.replace('@HASH', h).replace('@hash', h)
        pattern = pattern.replace('@YYYY', now.strftime('%Y')).replace('@yyyy', now.strftime('%Y'))
        pattern = pattern.replace('@MM', now.strftime('%m'))
        pattern = pattern.replace('@DD', now.strftime('%d')).replace('@dd', now.strftime('%d'))
        pattern = pattern.replace('@hh', now.strftime('%H')).replace('@HH', now.strftime('%H'))
        pattern = pattern.replace('@mm', now.strftime('%M'))
        pattern = pattern.replace('@ss', now.strftime('%S')).replace('@SS', now.strftime('%S'))

        if pattern.lower().endswith(f".{clean_ext}"):
            pattern = pattern[:-len(f".{clean_ext}")]

        safe_base = "".join(c if c in (VALID_FILENAME_CHARS + ".-") else "_" for c in pattern).strip("._")
        if not safe_base:
            safe_base = f"recoll_{now.strftime('%Y%m%d_%H%M%S')}"
        return f"{safe_base}.{clean_ext}"

    # Default / 'timestamp' fallback
    ts = now.strftime("%Y%m%d_%H%M%S")
    return f"recoll_{ts}.{clean_ext}"


def format_timestamp(timestamp_str: str, date_format: str) -> str:
    """
    Format unix timestamp string into human-readable date format string.
    """
    cleaned = (timestamp_str or '0').strip(',').strip()
    try:
        seconds = int(cleaned) if cleaned else 0
    except ValueError:
        seconds = 0
    return time.strftime(date_format, time.localtime(seconds))


def extract_common_prefix(path_list: List[str]) -> str:
    """
    Compute common directory prefix across multiple paths.
    Returns path with trailing slash if non-empty.
    """
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


def parse_json_request() -> Dict[str, Any]:
    """
    Safely extract JSON body from current Bottle request.
    Handles both direct JSON body and raw body stream.
    """
    if not bottle or not hasattr(bottle, 'request'):
        return {}
    data = bottle.request.json
    if not data:
        raw_body = bottle.request.body.read().decode('utf-8')
        data = json.loads(raw_body) if raw_body else {}
    return data if isinstance(data, dict) else {}


def json_response(payload: Any, status: int = 200) -> str:
    """
    Format data as JSON string with application/json header and specified status code.
    """
    if bottle and hasattr(bottle, 'response'):
        bottle.response.status = status
        bottle.response.content_type = 'application/json'
    return json.dumps(payload)


def json_error(message: str, status: int = 400) -> str:
    """
    Format standard JSON error response: {'success': False, 'error': message}.
    """
    return json_response({'success': False, 'error': message}, status=status)
