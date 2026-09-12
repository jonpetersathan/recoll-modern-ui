"""
Error handling and custom error page rendering for Recoll Modern UI.
"""

from typing import Any, Optional
import bottle
from recollweb.logging import get_client_ip, logger


def render_error_page(code: Any = 500, title: Optional[str] = None, desc: Optional[str] = None,
                      details: Optional[str] = None, is_warning: Optional[bool] = None) -> str:
    """
    Render custom dark glassmorphic error card matching the application theme.
    """
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
    try:
        bottle.response.status = numeric_code
    except Exception:
        pass

    return bottle.template(
        'error',
        code=code,
        title=title or def_title,
        desc=desc or def_desc,
        details=details,
        is_warning=is_warning if is_warning is not None else def_warn,
    )


def custom_error_handler(error: Any) -> str:
    """
    Handle HTTP errors with logging and context-specific error messages.
    """
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


def custom_default_error_handler(res: Any) -> str:
    """
    Default fallback error handler for all unhandled HTTP statuses.
    """
    return custom_error_handler(res)


def register_error_handlers(app: bottle.Bottle):
    """
    Register custom error handlers on the provided Bottle application instance.
    """
    for code in (400, 401, 403, 404, 500, 502, 503, 504):
        app.error(code)(custom_error_handler)
    app.default_error_handler = custom_default_error_handler
