# Recoll Modern UI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-0.9.5-purple.svg)](Makefile)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Container](https://img.shields.io/badge/Container-Podman%20%7C%20Docker-brightgreen.svg)](Dockerfile)

Modern, production-ready Web UI and REST API for the [Recoll](https://www.lesbonscomptes.com/recoll/) full-text search engine, packaged with Podman/Docker.

---

## Features

- **Modern Glassmorphic Interface**: Dark theme with glow accents, real-time search term highlighting, responsive controls, and accessible layout.
- **Modular Python Architecture**: Clean package structure (`src/recollweb/`) with separated concerns for configuration, search, archiving, forms, indexing, metadata, and routing.
- **SQLite Configuration Persistence**: Relational storage (`recoll-web.db`) for user settings, global defaults, custom form schemas, and user state tracking with WAL mode.
- **Advanced Search Forms**: Customizable search form schemas with JSON/DB persistence, static query filters, proximity searches, toggle switches, and metadata fields.
- **File & Folder Browser**: Secure, read-only file tree browser (`/browser`) with topdirs containment, directory traversal guards, breadcrumbs, and direct downloads.
- **Index Management & Monitoring**: Administrative control center (`/index-manager`) to inspect document count, database disk size, trigger incremental or full re-indexing (`recollindex`), and purge databases.
- **Dynamic Metadata Extraction Engine**: High-performance compiled Rust extractor (`recoll-metadata-extractor`) with pure-Python fallback (`extractor_cli.py`) supporting depth, delimiter, regex named captures, and date directive parsing (`dmtime`).
- **Bulk File Archiving**: Asynchronous background ZIP packaging and direct downloads of filtered search result document sets.
- **Reverse Auth Proxy & RBAC**: Header-based authentication (`X-WEBAUTH-USER`), CIDR network whitelisting, and role-based permissions (`permissions.conf`) with administrative delegation.
- **Multiple Deployment Modes**: Standalone waitress server, WSGI application entrypoint, or containerized daemon.
- **Branding Customization**: Automatic discovery and serving of custom logos (`logo.png`, `logo.svg`, `logo.jpg`) from configuration directories.

---

## Architecture Overview

The application codebase is structured into modular Python components:

```
src/
├── recollweb/                  # Core package
│   ├── __init__.py             # Public package exports and application factory (create_app)
│   ├── archive.py              # ArchiveManager and background ZIP worker thread
│   ├── auth.py                 # Reverse auth proxy validation, IP whitelisting, permissions.conf RBAC
│   ├── browser.py              # Secure read-only filesystem browser and path containment guards
│   ├── config.py               # ConfigManager, recoll.conf atomic parser/serializer, logo detection
│   ├── constants.py            # Configuration defaults, MIME types, field names, and default forms
│   ├── db.py                   # SQLite relational persistence (recoll-web.db) with WAL mode
│   ├── errors.py               # Dark glassmorphic error pages and HTTP error handlers
│   ├── extractor_cli.py        # Standalone Python CLI metadata extractor (Rust fallback)
│   ├── forms.py                # SearchFormsManager schema CRUD, validation, forms.json sync
│   ├── indexer.py              # IndexManager, background recollindex subprocess, status reporting
│   ├── logging.py              # Centralized logging configuration and client IP extraction
│   ├── metadata.py             # MetadataRulesManager, in-memory rule engine, recoll.conf/fields sync
│   ├── routes.py               # REST API endpoints, static assets, and search UI routes
│   ├── search.py               # RecollSearchEngine, SearchQuery, SnippetHighlighter, document extraction
│   └── utils.py                # MIME labels, filename sanitization, timestamp formatting, JSON helpers
├── static/                     # CSS stylesheets, JavaScript helpers, and branding assets
├── views/                      # Bottle template views (main, results, search, browser, settings, index)
├── webui.py                    # Backwards-compatible facade and direct development runner
├── webui-standalone.py         # Production standalone CLI server runner (Waitress)
└── webui-wsgi.py               # WSGI application entrypoint (Gunicorn, uWSGI, etc.)
```

---

## Quick Start

### Build Container Image
```bash
make build
```

### Run Container
Starts the container on port `8180` and mounts test data and configuration:
```bash
make run
```

### Run Automated Tests
Executes the comprehensive automated verification test suite against the running container:
```bash
make test
```
The test suite validates:
1. Web UI readiness probe
2. Root HTML endpoint delivery
3. Static assets delivery (CSS/JS/SVG)
4. JSON search query endpoint
5. Modular architecture & subsystems unit tests (24 unit tests)
6. Advanced search, form builder, and endpoints integration tests (35 integration tests)
7. Metadata rules engine, index manager, and extractor CLI tests (13 tests)

### Stop Container
Stops and removes the running container:
```bash
make stop
```

### Clean Images
Removes locally built container images:
```bash
make clean
```

---

## REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web UI search interface |
| `GET` | `/results` | Search results page with pagination and detail view |
| `GET`, `POST` | `/json` | JSON search query API returning structured document results |
| `GET`, `POST` | `/csv` | CSV export API returning search results as downloadable CSV |
| `GET` | `/download/<resnum>` | Download original document file as an attachment |
| `GET` | `/open/<resnum>` | Open original document inline in browser |
| `GET` | `/preview/<resnum>` | Text extraction preview with search term highlights |
| `POST`, `GET` | `/api/archive/start` | Start asynchronous ZIP packaging of matching search results |
| `GET` | `/api/archive/status/<id>` | Poll progress percentage and status of background ZIP job |
| `GET` | `/api/archive/download/<id>`| Download generated ZIP archive |
| `POST`, `GET` | `/api/archive/cancel/<id>`| Cancel running archiving job |
| `GET` | `/browser` | Web UI file and folder browser |
| `GET` | `/api/browser/list` | JSON listing of directory entries with metadata |
| `GET` | `/api/browser/download` | Safe file download within allowed topdirs |
| `GET` | `/index-manager` | Administrative index status and metadata rules UI |
| `GET` | `/api/index/status` | Real-time index health, size, and document count |
| `POST` | `/api/index/reindex` | Trigger background re-indexing (`incremental` or `full`) |
| `POST` | `/api/index/purge` | Purge search database (`xapiandb`) |
| `GET`, `POST` | `/api/index/config` | Read or update managed parameters in `recoll.conf` |
| `GET`, `POST` | `/api/metadata/rules` | Read or save custom metadata extraction rules |
| `POST` | `/api/metadata/test` | Test candidate extraction rules against sample file paths |
| `GET` | `/api/metadata/fields` | Retrieve list of all known standard and custom fields |
| `GET`, `POST` | `/api/forms` | List or create custom search form schemas |
| `POST` | `/api/forms/delete` | Delete custom search form by ID |
| `POST` | `/api/forms/toggle` | Enable or disable form for current user |
| `GET` | `/settings` | User preferences and global defaults configuration UI |
| `POST` | `/api/settings/restore` | Reset user setting override to global default |
| `POST`, `GET` | `/set` | Save preferences with user or global scope |

---

## Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RECOLL_CONFDIR` | `/root/.recoll` | Path to Recoll configuration directory containing `recoll.conf`, `xapiandb`, and `recoll-web.db`. |
| `RECOLL_LOGLEVEL` | `INFO` | Application log level (`ERROR`, `WARN`, `INFO`, `DEBUG`). |
| `RECOLL_TMPDIR` | `/tmp` | Directory for temporary extracted files and preview caches. |
| `RECOLL_EXPORT_DIR` | `/export` | Target directory for generated ZIP archive exports. |
| `RECOLL_EXTRACONFDIRS` | *None* | Space-separated list of extra configuration directories for external index databases. |
| `RECOLL_AUTH_PROXY_ENABLED` | `false` | Enable reverse auth proxy user extraction (`true`/`false`). |
| `RECOLL_AUTH_PROXY_HEADER_NAME` | `X-WEBAUTH-USER` | HTTP header name containing authenticated user identity. |
| `RECOLL_AUTH_PROXY_HEADER_PROPERTY` | `username` | Property to extract from header value (e.g. `username`, `email`, or JSON key). |
| `RECOLL_AUTH_PROXY_WHITELIST` | *None* | Comma-separated list of allowed proxy IP addresses or CIDRs (e.g. `127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16`). |
| `RECOLL_METADATA_EXTRACTOR` | `/usr/local/bin/recoll-metadata-extractor` | Path to executable metadata extractor binary or CLI. |
| `PYTHONPATH` | `/app/src` | Python module search path. |

---

## Example Config File (`recoll.conf`)

```conf
topdirs = /data
loglevel = 1
dbdir = /root/.recoll/xapiandb
defaultcharset = UTF-8

skippedNames = *.vmdk *.vdi *.mp4 *.mov *.stl *.psd *.alp *.avi \
*.mp3 *.exe *.EXE *.DLL *.MP3 *.dll *.iso *.msi *.flv *.IMG *.STL \
*.MOV *.MP4 *.vwx *.dxf *.SLDPRT *.SLDASM *.rar *.mid *.midi *.chm \
*.jpg *.psd *.png *.tif *.tiff *.jpeg *.JPG *.JPEG *.TIF *.TIFF *.PSD \
*.indd *.idml *.ai *.svg *.JPG *.PNG *.AI *.stl *.DXF *.skp *.skb *.fxg \
*.tga *.rm *.TGA *.jar *.JAR *.class *.CLASS *.NEF *.wav *.aiff *.WAV *.aif \
*.CR2 *.gif *.GIF *.3dm *.aep *.prproj *.eps *.EPS *.ttf *.woff *.otf @eadir \
.DS_Store *.dae *.DAE *.pyc *.asd *.adg *.adv *.als *.agr *.amxd *.blend *.TTF \
*.WOFF *.eot *.EOT *.PFM *.pfm *.pfb *.PFB *.ogg

indexallfilenames = true
```

---

## Role-Based Access Control (`permissions.conf`)

Define administrative users in `permissions.conf` located inside `RECOLL_CONFDIR`:

```ini
[admins]
users = admin, jonathan, adm_*
```

Administrators have access to:
- Index lifecycle operations (`/index-manager`)
- Global setting overrides affecting all users
- Global search form templates
- Search database purging and re-indexing

Regular users can:
- Execute queries, browse files, and download documents
- Customize personal preferences and form presets
- Export result sets as ZIP archives, JSON, or CSV

---

## Manual Indexing CLI

To trigger a manual index update within the running container:
```bash
podman exec recoll recollindex
```
To trigger a full rebuild from scratch:
```bash
podman exec recoll recollindex -z
```