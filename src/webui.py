#!/usr/bin/env python3
"""
Recoll Modern UI - Clean, Modern Document Search Interface
Full-featured Python 3 Bottle Application for Recoll Search Engine

This module provides the primary entry point and backward-compatible facade
for Recoll Modern UI. Core logic is modularized under the `recollweb` package.
"""

import sys
import os

# Ensure package directory is in sys.path when invoked directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import bottle
import recollweb
from recollweb import (
    # Application & Logging
    app,
    application,
    logger,
    setup_logging,
    get_client_ip,
    get_configured_log_level,
    # Configuration & Directories
    ConfigManager,
    get_config_dir,
    find_custom_logo,
    DEFAULT_CONFIG,
    SORT_OPTIONS,
    DOCUMENT_FIELDS,
    BASE_DIR,
    STATIC_DIR,
    VIEWS_DIR,
    TEMP_DIR,
    EXPORT_DIR,
    # Forms & Schemas
    SearchFormsManager,
    DEFAULT_SEARCH_FORM,
    SAMPLE_CUSTOM_FORM,
    # Search Engine & Queries
    RecollSearchEngine,
    SearchQuery,
    SnippetHighlighter,
    extract_document_file,
    # Archiving & ZIP Manager
    ArchiveManager,
    # File & Folder Browser
    BrowserManager,
    # Error Handlers & Utilities
    render_error_page,
    custom_error_handler,
    custom_default_error_handler,
    format_mimetype_label,
    sanitize_filename,
    format_timestamp,
    extract_common_prefix,
    __version__,
)

__all__ = [
    'app',
    'application',
    'bottle',
    'logger',
    'ConfigManager',
    'SearchFormsManager',
    'RecollSearchEngine',
    'SearchQuery',
    'SnippetHighlighter',
    'ArchiveManager',
    'BrowserManager',
    'DEFAULT_CONFIG',
    'SORT_OPTIONS',
    'DOCUMENT_FIELDS',
    'DEFAULT_SEARCH_FORM',
    'SAMPLE_CUSTOM_FORM',
    'render_error_page',
    'format_mimetype_label',
    'sanitize_filename',
    'format_timestamp',
    'get_config_dir',
    'find_custom_logo',
    '__version__',
]


if __name__ == '__main__':
    # When executed directly, start standalone development server
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '127.0.0.1')
    logger.info("Starting Recoll Modern UI directly on http://%s:%d", host, port)
    bottle.run(app=app, host=host, port=port, server='waitress')
