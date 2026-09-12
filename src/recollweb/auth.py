"""
User authentication and authorization based on reverse auth proxy headers and permissions.conf.

Supports the following environment variables:
- RECOLL_AUTH_PROXY_ENABLED: Enable or disable proxy header authentication (true/false)
- RECOLL_AUTH_PROXY_HEADER_NAME: Header name to inspect (default: X-WEBAUTH-USER)
- RECOLL_AUTH_PROXY_HEADER_PROPERTY: Header property to extract (default: username)
- RECOLL_AUTH_PROXY_WHITELIST: Allowed proxy IP addresses or CIDR ranges (comma-separated)
"""

import fnmatch
import ipaddress
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import unquote

try:
    import bottle
except ImportError:
    bottle = None

from recollweb.logging import logger


def resolve_config_dir(conf_dir: Optional[str] = None) -> str:
    """
    Safely resolve Recoll configuration directory without circular imports.
    """
    if conf_dir and os.path.isdir(conf_dir):
        return conf_dir
    env_dir = os.environ.get("RECOLL_CONFDIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    try:
        from recollweb.config import get_config_dir
        return get_config_dir()
    except Exception:
        return os.path.expanduser("~/.recoll")


def is_auth_proxy_enabled() -> bool:
    """
    Check whether reverse auth proxy mode is enabled via RECOLL_AUTH_PROXY_ENABLED.
    Accepts: '1', 'true', 'yes', 'on' (case-insensitive).
    """
    val = os.environ.get("RECOLL_AUTH_PROXY_ENABLED", "").strip().lower()
    return val in ("1", "true", "yes", "on")


def get_auth_proxy_header_name() -> str:
    """
    Resolve HTTP header name used for proxy authentication.
    Defaults to 'X-WEBAUTH-USER'.
    """
    val = os.environ.get("RECOLL_AUTH_PROXY_HEADER_NAME", "").strip()
    return val if val else "X-WEBAUTH-USER"


def get_auth_proxy_header_property() -> str:
    """
    Resolve property name to extract from proxy authentication header.
    Defaults to 'username'.
    """
    val = os.environ.get("RECOLL_AUTH_PROXY_HEADER_PROPERTY", "").strip()
    return val if val else "username"


def get_auth_proxy_whitelist() -> List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
    """
    Parse RECOLL_AUTH_PROXY_WHITELIST into a list of IP networks (IPv4/IPv6).
    Supports comma, semicolon, or whitespace separated IPs and CIDR ranges.
    Returns empty list if not configured.
    """
    raw = os.environ.get("RECOLL_AUTH_PROXY_WHITELIST", "").strip().strip("\"'")
    if not raw:
        return []

    networks: List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]] = []
    tokens = [t.strip().strip("\"'") for t in re.split(r"[,;]+", raw) if t.strip().strip("\"'")]
    for tok in tokens:
        try:
            net = ipaddress.ip_network(tok, strict=False)
            networks.append(net)
        except ValueError as exc:
            logger.warning("Invalid IP or CIDR in RECOLL_AUTH_PROXY_WHITELIST: '%s' (%s)", tok, exc)
    return networks


def is_ip_whitelisted(
    ip_str: Optional[str],
    whitelist: Optional[List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]] = None,
) -> bool:
    """
    Validate whether an IP address belongs to the auth proxy whitelist.
    If whitelist is empty, returns True (no IP restriction).
    Supports IPv4, IPv6, and IPv6-mapped IPv4 addresses (::ffff:x.x.x.x).
    """
    wl = whitelist if whitelist is not None else get_auth_proxy_whitelist()
    if not wl:
        return True

    if not ip_str:
        return False

    clean_ip = ip_str.split(",")[0].strip().strip("\"'")
    try:
        ip_obj = ipaddress.ip_address(clean_ip)
    except ValueError:
        logger.warning("Failed to parse client IP address: '%s'", clean_ip)
        return False

    candidate_ips = [ip_obj]
    if isinstance(ip_obj, ipaddress.IPv6Address) and getattr(ip_obj, "ipv4_mapped", None):
        candidate_ips.append(ip_obj.ipv4_mapped)

    for net in wl:
        for candidate in candidate_ips:
            try:
                if candidate in net:
                    return True
            except TypeError:
                pass

    return False


def extract_user_from_header_value(header_value: str, header_property: str = "username") -> Optional[str]:
    """
    Extract user identity from raw header string based on header_property.
    Supports:
    1. JSON dictionaries: extracts key matching header_property (exact or case-insensitive)
    2. Key-value pairs (e.g., 'username=alice, email=alice@example.com')
    3. Plain string / email
    """
    if not header_value:
        return None

    raw = header_value.strip()
    if not raw:
        return None

    # Attempt JSON decode if payload resembles JSON object
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                prop_target = header_property.strip().lower()
                # Direct match
                if header_property in data:
                    res = str(data[header_property]).strip()
                    if res:
                        return res
                # Case-insensitive match on keys
                for k, v in data.items():
                    if str(k).strip().lower() == prop_target:
                        res = str(v).strip()
                        if res:
                            return res
                # Fallback to common identity properties
                for fallback_key in ("username", "user", "preferred_username", "sub", "email"):
                    for k, v in data.items():
                        if str(k).strip().lower() == fallback_key:
                            res = str(v).strip()
                            if res:
                                return res
        except Exception:
            pass

    # Attempt Key-Value format: e.g. "username=alice; email=alice@example.com"
    if "=" in raw and not raw.startswith("http"):
        prop_target = header_property.strip().lower()
        parts = re.split(r"[;,]+", raw)
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                if k.strip().lower() == prop_target:
                    clean_v = v.strip().strip("\"'")
                    if clean_v:
                        return clean_v

    # Fallback to plain string
    clean_val = unquote(raw).strip().strip("\"'")
    return clean_val if clean_val else None


def get_remote_addr(req: Optional[Any] = None) -> str:
    """
    Extract direct socket peer IP (REMOTE_ADDR) from request context or Bottle environment.
    """
    if req is not None:
        if hasattr(req, "environ") and isinstance(req.environ, dict) and req.environ.get("REMOTE_ADDR"):
            return str(req.environ["REMOTE_ADDR"]).strip()
        if isinstance(req, dict) and req.get("REMOTE_ADDR"):
            return str(req["REMOTE_ADDR"]).strip()
        if hasattr(req, "remote_addr") and req.remote_addr:
            return str(req.remote_addr).strip()
    elif bottle and hasattr(bottle, "request") and bottle.request:
        try:
            if hasattr(bottle.request, "environ") and bottle.request.environ.get("REMOTE_ADDR"):
                return str(bottle.request.environ["REMOTE_ADDR"]).strip()
            if bottle.request.remote_addr:
                return str(bottle.request.remote_addr).strip()
        except Exception:
            pass
    return "127.0.0.1"


def extract_header_value(req: Optional[Any], header_name: str) -> Optional[str]:
    """
    Extract raw header value from request headers or WSGI environment variables.
    """
    if req is None:
        return None

    header_val = None
    if hasattr(req, "headers") and req.headers:
        header_val = req.headers.get(header_name)
    elif isinstance(req, dict) and "headers" in req:
        header_val = req["headers"].get(header_name)

    if header_val is None and hasattr(req, "environ") and isinstance(req.environ, dict):
        wsgi_key = "HTTP_" + header_name.upper().replace("-", "_")
        header_val = req.environ.get(wsgi_key) or req.environ.get(header_name)
    elif header_val is None and isinstance(req, dict):
        wsgi_key = "HTTP_" + header_name.upper().replace("-", "_")
        header_val = req.get(wsgi_key) or req.get(header_name)

    if header_val is not None:
        res = str(header_val).strip()
        if res:
            return res
    return None


def validate_auth_proxy_request(req: Optional[Any] = None) -> Tuple[bool, int, str]:
    """
    Validate incoming request against auth proxy security requirements:
    1. If RECOLL_AUTH_PROXY_WHITELIST is configured, verify remote IP is whitelisted.
    2. Verify that the configured proxy auth header is present and non-empty.
    3. Verify that a valid user identity can be extracted from the header.

    Returns:
        (is_valid, status_code, error_message)
    """
    if not is_auth_proxy_enabled():
        return True, 200, ""

    request_obj = req
    if request_obj is None and bottle and hasattr(bottle, "request") and bottle.request:
        try:
            request_obj = bottle.request
        except Exception:
            request_obj = None

    if request_obj is None:
        return False, 403, "Access Forbidden: No request context found."

    remote_ip = get_remote_addr(request_obj)
    whitelist = get_auth_proxy_whitelist()
    if whitelist and not is_ip_whitelisted(remote_ip, whitelist):
        logger.warning(
            "Auth proxy rejected: client IP '%s' is not in RECOLL_AUTH_PROXY_WHITELIST",
            remote_ip,
        )
        return False, 403, f"Access Forbidden: Direct connection from IP '{remote_ip}' is not permitted (not in RECOLL_AUTH_PROXY_WHITELIST)."

    header_name = get_auth_proxy_header_name()
    header_val = extract_header_value(request_obj, header_name)
    if not header_val:
        return False, 403, f"Access Forbidden: Missing required reverse proxy authentication header '{header_name}'."

    prop = get_auth_proxy_header_property()
    user = extract_user_from_header_value(header_val, prop)
    if not user:
        return False, 403, f"Access Forbidden: Unable to extract valid user identity from header '{header_name}' using property '{prop}'."

    return True, 200, ""


def get_current_username(request: Optional[Any] = None) -> str:
    """
    Extract username according to auth proxy configuration:
    - If RECOLL_AUTH_PROXY_ENABLED is false/unset -> returns 'default'
    - If RECOLL_AUTH_PROXY_ENABLED is true:
        - Validates request (whitelist + header + user extraction)
        - Returns extracted username, or 'default' if validation fails
    """
    if not is_auth_proxy_enabled():
        return "default"

    req = request
    if req is None and bottle and hasattr(bottle, "request") and bottle.request:
        try:
            req = bottle.request
        except Exception:
            req = None

    if req is None:
        return "default"

    is_valid, _, _ = validate_auth_proxy_request(req)
    if not is_valid:
        return "default"

    header_name = get_auth_proxy_header_name()
    header_val = extract_header_value(req, header_name)
    if header_val is not None:
        prop = get_auth_proxy_header_property()
        user = extract_user_from_header_value(header_val, prop)
        if user:
            return user

    return "default"


# Alias for backward compatibility and template references
get_current_user = get_current_username


def get_admin_patterns(conf_dir: Optional[str] = None) -> List[str]:
    """
    Parse permissions.conf from conf_dir.
    Supports list of full usernames (e.g. 'jonathan', 'admin') and wildcard expressions ('adm_*').
    Defaults to ['admin'] if file does not exist or has no patterns.
    """
    target_conf = resolve_config_dir(conf_dir)
    conf_path = os.path.join(target_conf, "permissions.conf")
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


def is_admin_user(username: str, conf_dir: Optional[str] = None) -> bool:
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


def get_user_role(username: str, conf_dir: Optional[str] = None) -> str:
    """Return 'admin' or 'user'."""
    return "admin" if is_admin_user(username, conf_dir) else "user"
