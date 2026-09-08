"""
Helper utilities for MIME formatting, filename sanitization, timestamps, and JSON requests.
"""

import json
import mimetypes
import os
import time
from typing import Any, Dict, List
import bottle
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


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe HTTP attachment headers, stripping invalid characters.
    """
    return "".join(c if c in VALID_FILENAME_CHARS else "_" for c in filename)


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
    data = bottle.request.json
    if not data:
        raw_body = bottle.request.body.read().decode('utf-8')
        data = json.loads(raw_body) if raw_body else {}
    return data if isinstance(data, dict) else {}


def json_response(payload: Any, status: int = 200) -> str:
    """
    Format data as JSON string with application/json header and specified status code.
    """
    bottle.response.status = status
    bottle.response.content_type = 'application/json'
    return json.dumps(payload)


def json_error(message: str, status: int = 400) -> str:
    """
    Format standard JSON error response: {'success': False, 'error': message}.
    """
    return json_response({'success': False, 'error': message}, status=status)
