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

from recollweb.constants import (
    CUSTOM_LOGO_FILENAMES,
    DEFAULT_CONFIG,
    DOCUMENT_FIELDS,
    SORT_OPTIONS,
)
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

        # Load user cookies with fallback to defaults
        for key, default_val in defaults.items():
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
