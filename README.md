# Recoll Modern UI

Modern, production-ready Web UI and REST API for the [Recoll](https://www.lesbonscomptes.com/recoll/) full-text search engine, packaged with Podman/Docker.

---

## Features

- **Modern Glassmorphic Interface**: Dark theme with glow accents, real-time search result highlights, and responsive controls.
- **Modular Python Architecture**: Clean package structure (`src/recollweb/`) with separated concerns for configuration, search, archiving, forms, and routes.
- **Advanced Search Forms**: Customizable search form schemas with JSON persistence (`forms.json`), static query filters, toggle switches, and metadata fields.
- **Bulk File Archiving**: Asynchronous background ZIP packaging and direct downloads of search result document sets.
- **Multiple Deployment Modes**: Standalone waitress server, WSGI application entrypoint, or containerized daemon.
- **Branding Customization**: Automatic discovery and serving of custom logos (`logo.png`, `logo.svg`, `logo.jpg`) from configuration directories.

---

## Architecture Overview

The application codebase is structured into modular Python components:

```
src/
├── recollweb/                  # Core package
│   ├── __init__.py             # Package exports and application factory (create_app)
│   ├── constants.py            # Configuration defaults, MIME types, field names, and default forms
│   ├── logging.py              # Centralized logging configuration and client IP extraction
│   ├── utils.py                # MIME labels, filename sanitization, timestamp formatting, JSON helpers
│   ├── config.py               # ConfigManager, directory trees, mount points, logo detection
│   ├── forms.py                # SearchFormsManager schema CRUD, validation, forms.json persistence
│   ├── search.py               # RecollSearchEngine, SearchQuery, SnippetHighlighter, document extraction
│   ├── archive.py              # ArchiveManager and background ZIP worker thread
│   ├── errors.py               # Glassmorphic error pages and HTTP error handlers
│   └── routes.py               # REST API endpoints, static assets, and search UI routes
├── static/                     # CSS stylesheets, JavaScript helpers, and default branding assets
├── views/                      # Bottle template views (main, results, search, settings, etc.)
├── webui.py                    # Backwards-compatible facade and direct runner
├── webui-standalone.py         # Production standalone CLI server runner
└── webui-wsgi.py               # WSGI application entrypoint
```

---

## Quick Start

### Build Container Image
```bash
make build
```

### Run Container
Starts the container with default port `8080` and mounts test data/configuration:
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
5. Modular architecture & subsystems unit tests (14 unit tests)
6. Advanced search, form builder, and endpoints integration tests (23 integration tests)

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

## Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RECOLL_CONFDIR` | `/root/.recoll` | Path to Recoll configuration directory containing `recoll.conf` and `xapiandb`. |
| `RECOLL_LOGLEVEL` | `INFO` | Application log level (`ERROR`, `WARN`, `INFO`, `DEBUG`). |
| `RECOLL_TMPDIR` | `/tmp` | Directory for temporary extracted files and preview caches. |
| `RECOLL_EXPORT_DIR` | `/export` | Target directory for generated ZIP archive exports. |
| `RECOLL_EXTRACONFDIRS` | *None* | Space-separated list of extra configuration directories for external index databases. |

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

## Manual Indexing

To trigger a manual index update within the container:
```bash
podman exec recoll recollindex
```