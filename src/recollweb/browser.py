"""
Read-only file and folder browser subsystem for Recoll Modern UI.
Provides secure path resolution, directory traversal, metadata extraction,
and protected file downloads within configured topdirs.
"""

import mimetypes
import os
from typing import Any, Dict, List, Optional, Tuple

from recollweb.config import ConfigManager
from recollweb.constants import BASE_DIR, MIME_LABELS
from recollweb.logging import logger
from recollweb.utils import format_mimetype_label, format_timestamp

# Additional MIME type overrides for extensions common in Recoll repositories
EXTRA_EXTENSIONS: Dict[str, str] = {
    '.gz': 'application/gzip',
    '.tgz': 'application/gzip',
    '.tar': 'application/x-tar',
    '.zip': 'application/zip',
    '.7z': 'application/x-7z-compressed',
    '.rar': 'application/x-rar-compressed',
    '.dbase3': 'application/x-dbf',
    '.dbf': 'application/x-dbf',
    '.wp': 'application/vnd.wordperfect',
    '.wpd': 'application/vnd.wordperfect',
    '.f': 'text/x-fortran',
    '.for': 'text/x-fortran',
    '.f90': 'text/x-fortran',
    '.swf': 'application/x-shockwave-flash',
    '.json': 'application/json',
    '.md': 'text/markdown',
    '.log': 'text/plain',
    '.unk': 'application/octet-stream',
}


class BrowserManager:
    """
    Manages read-only browsing, metadata extraction, and safe downloading of files
    and directories constrained strictly to Recoll topdirs.
    """

    @classmethod
    def get_allowed_roots(cls, confdir: Optional[str] = None) -> List[str]:
        """
        Resolve allowed root directories from Recoll configuration topdirs.
        Ensures all paths are canonical real paths (dereferenced symlinks).
        """
        resolved: List[str] = []
        try:
            config = ConfigManager.get_config()
            raw_dirs = list(config.get('dirs', {}).keys())
        except Exception as exc:
            logger.warning("BROWSER_GET_ROOTS: Failed to read recoll config: %s", exc)
            raw_dirs = []

        if not raw_dirs:
            raw_dirs = ['/data']

        for d in raw_dirs:
            if d:
                expanded = os.path.expanduser(d.strip())
                try:
                    rp = os.path.realpath(expanded)
                    if rp not in resolved:
                        resolved.append(rp)
                except Exception:
                    pass

        # If /data exists in filesystem, ensure it is always recognized
        if os.path.isdir('/data'):
            real_data = os.path.realpath('/data')
            if real_data not in resolved:
                resolved.append(real_data)

        # In local host test environments, include repo's test/data if present
        repo_test_data = os.path.abspath(os.path.join(BASE_DIR, '..', 'test', 'data'))
        if os.path.isdir(repo_test_data):
            real_test_data = os.path.realpath(repo_test_data)
            if real_test_data not in resolved:
                resolved.append(real_test_data)

        return resolved

    @classmethod
    def is_path_allowed(
        cls,
        target_path: str,
        allowed_roots: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that target_path resides within one of the allowed directory roots.
        Prevents directory traversal attacks by resolving canonical real paths and
        testing common path prefix containment.
        Returns (is_allowed, canonical_path).
        """
        if not target_path or not isinstance(target_path, str):
            return False, None

        if allowed_roots is None:
            allowed_roots = cls.get_allowed_roots()

        if not allowed_roots:
            return False, None

        try:
            clean_path = os.path.expanduser(target_path.strip())
            real_target = os.path.realpath(clean_path)

            for root in allowed_roots:
                real_root = os.path.realpath(root)
                try:
                    cp = os.path.commonpath([real_target, real_root])
                    if cp == real_root:
                        return True, real_target
                except ValueError:
                    # Occurs on Windows if paths reside on different drive letters
                    continue
        except Exception as exc:
            logger.warning("BROWSER_SECURITY_CHECK_ERROR: %s (Path: %s)", exc, target_path)
            return False, None

        return False, None

    @staticmethod
    def format_size_human(size_bytes: int) -> str:
        """
        Format byte count into human-readable representation (e.g. 12.5 KB, 1.2 MB).
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        num = float(size_bytes)
        for unit in ['KB', 'MB', 'GB', 'TB']:
            num /= 1024.0
            if num < 1024.0:
                return f"{num:.1f} {unit}"
        return f"{num:.1f} PB"

    @classmethod
    def build_breadcrumbs(cls, current_path: str, allowed_roots: List[str]) -> List[Dict[str, str]]:
        """
        Build a list of breadcrumb objects [{name: ..., path: ...}] from root to current path.
        """
        matching_root = None
        longest_match = -1
        for r in allowed_roots:
            real_r = os.path.realpath(r)
            try:
                if os.path.commonpath([current_path, real_r]) == real_r:
                    if len(real_r) > longest_match:
                        longest_match = len(real_r)
                        matching_root = real_r
            except ValueError:
                continue

        if not matching_root:
            matching_root = allowed_roots[0] if allowed_roots else current_path

        root_name = os.path.basename(matching_root) or matching_root
        crumbs = [{"name": root_name, "path": matching_root}]

        if current_path != matching_root:
            try:
                rel = os.path.relpath(current_path, matching_root)
                if rel and rel != '.':
                    accum = matching_root
                    for segment in rel.split(os.sep):
                        if segment and segment != '.':
                            accum = os.path.join(accum, segment)
                            crumbs.append({"name": segment, "path": accum})
            except Exception:
                pass

        return crumbs

    @classmethod
    def list_directory(cls, requested_path: Optional[str] = None) -> Dict[str, Any]:
        """
        List files and folders within requested_path.
        Enforces path containment within allowed roots and returns metadata entries.
        """
        allowed_roots = cls.get_allowed_roots()
        if not allowed_roots:
            raise PermissionError("No allowed directory roots configured.")

        if not requested_path or not requested_path.strip():
            target_path = allowed_roots[0]
        else:
            target_path = requested_path.strip()

        allowed, real_path = cls.is_path_allowed(target_path, allowed_roots)
        if not allowed or not real_path:
            raise PermissionError(f"Access denied: Path '{target_path}' is outside allowed directories.")

        if not os.path.exists(real_path):
            raise FileNotFoundError(f"Directory not found: '{target_path}'.")

        if not os.path.isdir(real_path):
            raise NotADirectoryError(f"Path is not a directory: '{target_path}'.")

        breadcrumbs = cls.build_breadcrumbs(real_path, allowed_roots)

        try:
            with os.scandir(real_path) as it:
                raw_entries = list(it)
        except OSError as err:
            raise PermissionError(f"Cannot read directory: {err}")

        dirs = []
        files = []
        for item in raw_entries:
            try:
                stat_res = item.stat()
                is_dir = item.is_dir(follow_symlinks=True)
                mtime = int(stat_res.st_mtime)
                mtime_human = format_timestamp(str(mtime), "%Y-%m-%d %H:%M")
                entry_path = os.path.join(real_path, item.name)

                if is_dir:
                    dirs.append({
                        "name": item.name,
                        "path": entry_path,
                        "is_dir": True,
                        "size": 0,
                        "size_human": "-",
                        "mtime": mtime,
                        "mtime_human": mtime_human,
                        "mimetype": "inode/directory",
                        "mimetype_label": "Directory",
                    })
                else:
                    size = stat_res.st_size
                    ext = os.path.splitext(item.name)[1].lower()
                    mimetype = EXTRA_EXTENSIONS.get(ext)
                    if not mimetype:
                        mimetype, _ = mimetypes.guess_type(item.name)
                    if not mimetype:
                        mimetype = "application/octet-stream"

                    mimetype_label = format_mimetype_label(mimetype, filename=item.name)

                    files.append({
                        "name": item.name,
                        "path": entry_path,
                        "is_dir": False,
                        "size": size,
                        "size_human": cls.format_size_human(size),
                        "mtime": mtime,
                        "mtime_human": mtime_human,
                        "mimetype": mimetype,
                        "mimetype_label": mimetype_label,
                    })
            except OSError:
                continue

        dirs.sort(key=lambda x: x["name"].lower())
        files.sort(key=lambda x: x["name"].lower())
        entries = dirs + files

        return {
            "success": True,
            "current_path": real_path,
            "breadcrumbs": breadcrumbs,
            "entries": entries,
            "total_entries": len(entries),
            "total_dirs": len(dirs),
            "total_files": len(files),
        }
