"""
Recoll Modern UI - Clean, Modern Document Search Interface
Full-featured Python Bottle Application for Recoll Search Engine
"""

import mimetypes
import warnings

try:
    import bottle
except ImportError:
    bottle = None

from recollweb.constants import (
    BASE_DIR,
    DEFAULT_CONFIG,
    DEFAULT_SEARCH_FORM,
    DOCUMENT_FIELDS,
    EXPORT_DIR,
    MIME_LABELS,
    SAMPLE_CUSTOM_FORM,
    SORT_OPTIONS,
    STATIC_DIR,
    TEMP_DIR,
    VALID_FILENAME_CHARS,
    VIEWS_DIR,
)
from recollweb.logging import (
    LOG_LEVEL_MAP,
    get_client_ip,
    get_configured_log_level,
    logger,
    setup_logging,
)
from recollweb.utils import (
    extract_common_prefix,
    format_mimetype_label,
    format_timestamp,
    json_error,
    json_response,
    parse_json_request,
    sanitize_filename,
)
try:
    from recollweb.config import (
        ConfigManager,
        find_custom_logo,
        get_config_dir,
    )
    from recollweb.forms import (
        SearchFormsManager,
    )
    from recollweb.search import (
        RecollSearchEngine,
        SearchQuery,
        SnippetHighlighter,
        extract_document_file,
    )
    from recollweb.archive import (
        ArchiveManager,
        _run_archive_worker,
    )
    from recollweb.errors import (
        custom_default_error_handler,
        custom_error_handler,
        register_error_handlers,
        render_error_page,
    )
    from recollweb.indexer import IndexManager
    from recollweb.browser import BrowserManager
except ImportError:
    pass

from recollweb.metadata import MetadataRulesManager

try:
    from recollweb.routes import (
        register_routes,
        serve_logo_file,
    )
except ImportError:
    register_routes = None
    serve_logo_file = None

__version__ = "0.9.0"

# Suppress ResourceWarning noise from Waitress/asyncore socket and file wrappers
warnings.filterwarnings("ignore", category=ResourceWarning)

# Register custom MIME types
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

# Ensure views directory is in Bottle template search path
if bottle and VIEWS_DIR not in bottle.TEMPLATE_PATH:
    bottle.TEMPLATE_PATH.insert(0, VIEWS_DIR)


def create_app(custom_app=None):
    """
    Application factory for Recoll Modern UI.
    Initializes error handlers, registers routes, and configures templates.
    """
    if not bottle:
        raise RuntimeError("Bottle is not installed in the current environment.")
    web_app = custom_app or bottle.default_app()
    register_error_handlers(web_app)
    register_routes(web_app)
    return web_app


# Initialize default application instance if bottle is available
app = application = create_app(bottle.default_app()) if bottle else None
