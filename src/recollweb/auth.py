"""
User authentication and authorization based on X-WEBAUTH-USER and permissions.conf.
"""

import fnmatch
import os
from typing import List, Optional
import bottle


def get_current_username(request: Optional[bottle.Request] = None) -> str:
    """
    Extract username from X-WEBAUTH-USER header.
    Defaults to 'default' if header is not present or empty.
    """
    req = request or bottle.request
    val = (
        req.headers.get("X-WEBAUTH-USER")
        or req.headers.get("X-Webauth-User")
        or req.environ.get("HTTP_X_WEBAUTH_USER")
    )
    if val is not None:
        user = str(val).strip()
        if user:
            return user
    return "default"


def get_admin_patterns(conf_dir: str) -> List[str]:
    """
    Parse permissions.conf from conf_dir.
    Supports list of full usernames (e.g. 'jonathan', 'admin') and wildcard expressions ('adm_*').
    Defaults to ['admin'] if file does not exist or has no patterns.
    """
    conf_path = os.path.join(conf_dir, "permissions.conf")
    if not os.path.isfile(conf_path):
        return ["admin"]

    patterns: List[str] = []
    try:
        with open(conf_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                # Handle ini section header [admins]
                if line.startswith("[") and line.endswith("]"):
                    continue
                # Handle key = val style (e.g. users = jonathan, admin, adm_*)
                if "=" in line:
                    _, val = line.split("=", 1)
                    for item in val.split(","):
                        tok = item.strip().strip("\"'")
                        if tok:
                            patterns.append(tok)
                else:
                    # Line-separated items or comma-separated
                    for item in line.split(","):
                        tok = item.strip().strip("\"'")
                        if tok:
                            patterns.append(tok)
    except Exception:
        return ["admin"]

    return patterns if patterns else ["admin"]


def is_admin_user(username: str, conf_dir: str) -> bool:
    """
    Check whether given username satisfies any admin pattern in permissions.conf.
    Case-insensitive matching via fnmatch.
    """
    if not username:
        return False
    user_lower = username.lower().strip()
    patterns = get_admin_patterns(conf_dir)
    for p in patterns:
        p_clean = p.lower().strip()
        if fnmatch.fnmatch(user_lower, p_clean):
            return True
    return False


def get_user_role(username: str, conf_dir: str) -> str:
    """Return 'admin' or 'user'."""
    return "admin" if is_admin_user(username, conf_dir) else "user"
