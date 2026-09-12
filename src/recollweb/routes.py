"""
HTTP route definitions and request dispatchers for Recoll Modern UI.
"""

import csv
import io
import json
import os
import threading
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote as urlquote
import bottle
from recoll import rclextract

from recollweb.archive import ArchiveManager, _run_archive_worker
from recollweb.auth import is_auth_proxy_enabled, validate_auth_proxy_request
from recollweb.browser import BrowserManager
from recollweb.config import ConfigManager, find_custom_logo
from recollweb.constants import (
    DEFAULT_CONFIG,
    EXPORT_DIR,
    SORT_OPTIONS,
    STATIC_DIR,
    TEMP_DIR,
)
from recollweb.db import (
    delete_user_setting,
    get_all_settings_bundle,
    get_global_setting,
    set_global_setting,
    set_user_setting,
)
from recollweb.errors import render_error_page
from recollweb.forms import SearchFormsManager
from recollweb.indexer import IndexManager
from recollweb.logging import get_client_ip, logger
from recollweb.metadata import MetadataRulesManager
from recollweb.search import RecollSearchEngine, SearchQuery, SnippetHighlighter, extract_document_file
from recollweb.utils import (
    json_error,
    json_response,
    parse_json_request,
    sanitize_filename,
)


def serve_logo_file(fallback_to_default: bool = True):
    """
    Serve custom logo from configuration directory if present,
    otherwise serve default SVG logo.
    """
    custom = find_custom_logo()
    if custom:
        fn, fp = custom
        bottle.response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        return bottle.static_file(fn, root=os.path.dirname(fp))
    if fallback_to_default:
        return bottle.static_file('logo.svg', root=STATIC_DIR)
    return None


def register_routes(app: bottle.Bottle):
    """
    Register all HTTP endpoints on the provided Bottle application instance.
    """

    # ------------------------------------------------------------------------
    # Reverse Auth Proxy Guard
    # ------------------------------------------------------------------------

    @app.hook('before_request')
    def enforce_auth_proxy():
        if is_auth_proxy_enabled():
            is_valid, status_code, err_msg = validate_auth_proxy_request(bottle.request)
            if not is_valid:
                is_json = (
                    bottle.request.path.startswith('/api/')
                    or bottle.request.path.startswith('/json')
                    or bottle.request.params.get('ajax') == '1'
                    or 'application/json' in bottle.request.headers.get('Accept', '')
                    or bottle.request.is_xhr
                )
                if is_json:
                    raise bottle.HTTPResponse(
                        status=status_code,
                        body=json.dumps({"error": err_msg, "status": status_code}),
                        headers={"Content-Type": "application/json"}
                    )
                raise bottle.HTTPError(
                    status_code,
                    body=render_error_page(
                        code=status_code,
                        title="Access Forbidden",
                        desc="Direct connections bypassing reverse proxy authentication are not permitted.",
                        details=err_msg,
                        is_warning=True,
                    )
                )

    # ------------------------------------------------------------------------
    # Static Assets & Logos
    # ------------------------------------------------------------------------

    @app.route('/logo')
    @app.route('/logo.<ext:re:(svg|png|jpe?g)>')
    def serve_logo(ext=None):
        return serve_logo_file(fallback_to_default=True)

    @app.route('/favicon.ico')
    def serve_favicon():
        custom_logo = serve_logo_file(fallback_to_default=False)
        if custom_logo:
            return custom_logo
        for fn in ('logo.svg', 'recoll.png'):
            path = os.path.join(STATIC_DIR, fn)
            if os.path.isfile(path):
                return bottle.static_file(fn, root=STATIC_DIR)
        bottle.abort(404, 'Favicon not found')

    @app.route('/robots.txt')
    def serve_robots():
        bottle.response.content_type = 'text/plain'
        return "User-agent: *\nDisallow: /\n"

    @app.route('/static/<path:path>')
    def serve_static(path: str):
        if path in ('logo.svg', 'logo.png', 'logo.jpg', 'logo.jpeg'):
            custom_logo = serve_logo_file(fallback_to_default=False)
            if custom_logo:
                return custom_logo
        return bottle.static_file(path, root=STATIC_DIR)

    @app.route('/staticdoc/<path:path>')
    def serve_staticdoc(path: str):
        if not TEMP_DIR:
            return ""
        filename = os.path.basename(path)
        if not filename.startswith("rcltmp"):
            bottle.abort(401, 'Bad temporary file name')
        return bottle.static_file(path, root=TEMP_DIR)

    # ------------------------------------------------------------------------
    # Main Search UI
    # ------------------------------------------------------------------------

    @app.route('/')
    def main_page():
        config = ConfigManager.get_config()
        dirs = ConfigManager.get_directory_tree(list(config['dirs'].keys()), config['dirdepth'])
        query_data = SearchQuery.parse(config)
        forms = SearchFormsManager.get_forms(config['confdir'], username=config.get('current_user', 'default'))
        bottle.response.headers['Vary'] = 'Cookie'
        return bottle.template(
            'main',
            dirs=dirs,
            query=query_data,
            sorts=SORT_OPTIONS,
            config=config,
            forms=forms,
            forms_json=json.dumps(forms),
        )

    @app.route('/results')
    def search_results():
        config = ConfigManager.get_config()
        query_data = SearchQuery.parse(config)
        qs = SearchQuery.to_recoll_string(query_data)
        client_ip = get_client_ip()

        try:
            res, total_count, elapsed = RecollSearchEngine.execute_search(query_data, config)
            logger.info(
                "SEARCH: terms='%s' [dir='%s', sort='%s', page=%d] -> %d results (%.3fs) from %s",
                query_data.get('query', ''),
                query_data.get('dir', '<all>'),
                query_data.get('sort', 'relevancyrating'),
                query_data.get('page', 1),
                total_count,
                elapsed.total_seconds(),
                client_ip,
            )
        except Exception as exc:
            exc_msg = str(exc)
            logger.error("SEARCH_ERROR: query='%s' failed: %s (Client: %s)", qs, exc_msg, client_ip, exc_info=True)
            bottle.response.status = 500
            if "Can't open index" in exc_msg or "xapiandb" in exc_msg:
                return render_error_page(
                    code=500,
                    title="Search Index Unavailable",
                    desc="Recoll could not open the search index at the configured location (/root/.recoll/xapiandb). Ensure the index has been built (e.g. running 'recollindex') or that the configuration volume is mounted.",
                    details=exc_msg,
                    is_warning=False,
                )
            return render_error_page(
                code=500,
                title="Search Execution Error",
                desc="An unexpected error occurred while executing the search query.",
                details=exc_msg,
                is_warning=False,
            )

        dirs = ConfigManager.get_directory_tree(list(config['dirs'].keys()), config['dirdepth'])
        forms = SearchFormsManager.get_forms(config['confdir'], username=config.get('current_user', 'default'))
        bottle.response.headers['Vary'] = 'Cookie'
        bottle.response.headers['No-Vary-Search'] = 'key-order'

        view_mode = bottle.request.query.get('view') or bottle.request.get_cookie('recoll_search_view_mode', default='detail')
        if view_mode not in ('simple', 'detail'):
            view_mode = 'detail'

        return bottle.template(
            'results',
            res=res,
            time=elapsed,
            query=query_data,
            dirs=dirs,
            qs=qs,
            sorts=SORT_OPTIONS,
            config=config,
            query_string=bottle.request.query_string,
            nres=total_count,
            forms=forms,
            forms_json=json.dumps(forms),
            view_mode=view_mode,
        )

    # ------------------------------------------------------------------------
    # Document Preview, Download & Inline Viewing
    # ------------------------------------------------------------------------

    def _resolve_document(resnum: int, operation: str):
        """
        Shared helper for preview/download/open: initializes query, bounds-checks, fetches doc.
        Returns (query_obj, doc, query_data, config, client_ip) on success,
        or a rendered error page string on failure.
        """
        config = ConfigManager.get_config()
        query_data = SearchQuery.parse(config)
        client_ip = get_client_ip()

        try:
            query_obj, db_obj = RecollSearchEngine._init_query(query_data, config)
        except Exception as exc:
            logger.error("%s_ERROR: Init query failed for doc #%d: %s (Client: %s)", operation, resnum, exc, client_ip)
            bottle.response.status = 500
            return render_error_page(
                code=500,
                title="Search Index Unavailable",
                desc=f"Recoll could not open the search index for {operation.lower()}.",
                details=str(exc),
                is_warning=False,
            )

        rcludi = query_data.get('rcludi')
        if rcludi:
            doc = db_obj.getDoc(rcludi)
        else:
            if resnum >= query_obj.rowcount:
                logger.warning("%s_WARN: Doc #%d not found (total: %d) (Client: %s)", operation, resnum, query_obj.rowcount, client_ip)
                bottle.response.status = 404
                return render_error_page(
                    code=404,
                    title="Result Not Found",
                    desc=f"The requested result index {resnum} does not exist.",
                    is_warning=True,
                )
            query_obj.scroll(resnum)
            doc = query_obj.fetchone()

        return query_obj, doc, query_data, config, client_ip

    def _stream_document(resnum: int, operation: str, disposition: str):
        """
        Consolidated streaming logic for downloading or opening a document inline.
        Eliminates duplicate extraction and response header code.
        """
        result = _resolve_document(resnum, operation)
        if isinstance(result, str):
            return result
        query_obj, doc, query_data, config, client_ip = result

        extracted_path, filename, is_temp = extract_document_file(doc)
        if not extracted_path or not os.path.isfile(extracted_path):
            bottle.response.status = 404
            return render_error_page(code=404, title="File Not Found", desc="The requested document file could not be extracted or located.")

        file_size = os.stat(extracted_path).st_size
        logger.info("%s: doc #%d - '%s' [size: %d bytes, url: %s] (Client: %s)", operation, resnum, filename, file_size, getattr(doc, 'url', ''), client_ip)

        # PDF first-match page positioning redirect for downloads
        if disposition == 'attachment' and config.get('rclc_pdfposition') and getattr(doc, 'mimetype', '') == 'application/pdf':
            pagenum = -1
            term = ""
            try:
                pagenum, term = query_obj.getfirstmatchpage(doc)
            except Exception:
                pass
            if pagenum != -1:
                tmp_fn = f"rcltmp{uuid.uuid4().hex}_{os.path.basename(extracted_path)}"
                tmp_dest = os.path.join(TEMP_DIR, tmp_fn)
                with open(extracted_path, 'rb') as src, open(tmp_dest, 'wb') as dst:
                    dst.write(src.read())
                if is_temp:
                    try:
                        os.unlink(extracted_path)
                    except OSError:
                        pass
                pdf_url = f"/staticdoc/{tmp_fn}#page={pagenum}&search={urlquote(term)}"
                safe_url = json.dumps(pdf_url)
                return f'<html><head></head><body><script>window.location.replace({safe_url});</script></body></html>'

        bottle.response.content_type = getattr(doc, 'mimetype', 'application/octet-stream')
        bottle.response.headers['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        bottle.response.headers['Content-Length'] = file_size
        bottle.response.headers['Vary'] = 'Cookie'

        file_handle = open(extracted_path, 'rb')
        if is_temp:
            try:
                os.unlink(extracted_path)
            except OSError:
                pass
        return file_handle

    @app.route('/download/<resnum:int>')
    def download_document(resnum: int):
        return _stream_document(resnum, "DOWNLOAD", disposition="attachment")

    @app.route('/open/<resnum:int>')
    def open_document(resnum: int):
        return _stream_document(resnum, "OPEN", disposition="inline")

    @app.route('/preview/<resnum:int>')
    def preview_document(resnum: int):
        result = _resolve_document(resnum, "PREVIEW")
        if isinstance(result, str):
            return result
        query_obj, doc, query_data, config, client_ip = result

        doc_label = getattr(doc, 'title', None) or getattr(doc, 'filename', None) or '?'
        doc_url = getattr(doc, 'url', '')
        logger.info("PREVIEW: doc #%d - '%s' [url: %s] (Client: %s)", resnum, doc_label, doc_url, client_ip)

        extractor = rclextract.Extractor(doc)
        extracted_doc = extractor.textextract(doc.ipath)

        is_html = 1 if extracted_doc.mimetype == 'text/html' else 0
        bottle.response.content_type = 'text/html; charset=utf-8' if is_html else 'text/plain; charset=utf-8'

        if query_data.get('highlight', 1):
            highlighter = SnippetHighlighter()
            highlighted_text = query_obj.highlight(extracted_doc.text, ishtml=is_html, methods=highlighter)
            head_pos = highlighted_text.find('<head>')
            css_ref = '<link rel="stylesheet" type="text/css" href="/static/style.css">'
            if head_pos >= 0:
                final_html = highlighted_text[:head_pos + 6] + css_ref + highlighted_text[head_pos + 6:]
            else:
                final_html = (
                    f'<html><head>{css_ref}'
                    '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body>'
                    f'{highlighted_text}</body></html>'
                )
            bottle.response.content_type = 'text/html; charset=utf-8'
            return final_html

        bottle.response.headers['Vary'] = 'Cookie'
        return extracted_doc.text

    def _parse_selected_param() -> Set[str]:
        """Extract selected document identifiers from GET query or POST form/JSON body."""
        selected_ids: Set[str] = set()
        raw: List[Any] = []
        if bottle.request.method == 'POST':
            if bottle.request.json and isinstance(bottle.request.json, dict):
                sel = bottle.request.json.get('selected')
                if isinstance(sel, list):
                    raw.extend(sel)
                elif isinstance(sel, str):
                    raw.append(sel)
            forms_sel = bottle.request.forms.getall('selected')
            if forms_sel:
                raw.extend(forms_sel)
        query_sel = bottle.request.query.getall('selected')
        if query_sel:
            raw.extend(query_sel)

        for item in raw:
            if not item:
                continue
            if isinstance(item, list):
                for sub in item:
                    if sub and str(sub).strip():
                        selected_ids.add(str(sub).strip())
            elif ',' in item and not item.startswith('file://'):
                for sub in item.split(','):
                    if sub and sub.strip():
                        selected_ids.add(sub.strip())
            else:
                selected_ids.add(str(item).strip())
        return selected_ids

    def _is_doc_dict_selected(doc: Dict[str, Any], selected_ids: Set[str]) -> bool:
        """Check if a result item dict matches selected identifiers."""
        if not selected_ids:
            return True
        rcludi = str(doc.get('rcludi', '') or '')
        url = str(doc.get('url', '') or '')
        if rcludi in selected_ids or url in selected_ids:
            return True
        if rcludi:
            if rcludi.rstrip('|') in selected_ids:
                return True
            r_stripped = rcludi.replace('/data/', '/').lstrip('/')
            if r_stripped in selected_ids or r_stripped.rstrip('|') in selected_ids:
                return True
        if url:
            u_stripped = url.replace('file:///data/', 'file:///').replace('/data/', '/')
            if u_stripped in selected_ids:
                return True
            raw_url = url.replace('file://', '')
            if raw_url in selected_ids or raw_url.replace('/data/', '/') in selected_ids:
                return True
        return False

    # ------------------------------------------------------------------------
    # Export Endpoints (JSON / CSV / Archive)
    # ------------------------------------------------------------------------

    @app.route('/json', method=['GET', 'POST'])
    def export_json():
        config = ConfigManager.get_config()
        query_data = SearchQuery.parse(config)
        query_data['page'] = 1
        config['perpage'] = 0  # Export all results, not just one page
        qs = SearchQuery.to_recoll_string(query_data)
        client_ip = get_client_ip()
        selected_ids = _parse_selected_param()

        try:
            res, total_count, _ = RecollSearchEngine.execute_search(query_data, config)
            if selected_ids:
                res = [d for d in res if _is_doc_dict_selected(d, selected_ids)]
                total_count = len(res)
        except Exception as exc:
            logger.warning("EXPORT_JSON_WARNING: Search index unavailable or query error: %s (Client: %s)", exc, client_ip)
            bottle.response.headers['Content-Type'] = 'application/json'
            bottle.response.headers['Content-Disposition'] = f'attachment; filename="recoll-{sanitize_filename(qs)}.json"'
            return json.dumps({'query': query_data, 'results': [], 'total': 0})

        logger.info("EXPORT_JSON: query='%s' (terms='%s', selected=%d) -> %d records exported to %s", qs, query_data.get('query', ''), len(selected_ids), total_count, client_ip)

        bottle.response.headers['Content-Type'] = 'application/json'
        bottle.response.headers['Content-Disposition'] = f'attachment; filename="recoll-{sanitize_filename(qs)}.json"'

        return json.dumps({'query': query_data, 'results': res, 'total': total_count})

    @app.route('/csv', method=['GET', 'POST'])
    def export_csv():
        config = ConfigManager.get_config()
        query_data = SearchQuery.parse(config)
        query_data['page'] = 1
        query_data['snippets'] = 0
        config['perpage'] = 0  # Export all results, not just one page
        qs = SearchQuery.to_recoll_string(query_data)
        client_ip = get_client_ip()
        selected_ids = _parse_selected_param()

        try:
            res, _, _ = RecollSearchEngine.execute_search(query_data, config)
            if selected_ids:
                res = [d for d in res if _is_doc_dict_selected(d, selected_ids)]
        except Exception as exc:
            logger.warning("EXPORT_CSV_WARNING: Search index unavailable or query error: %s (Client: %s)", exc, client_ip)
            res = []
        logger.info("EXPORT_CSV: query='%s' (terms='%s', selected=%d) -> %d records exported to %s", qs, query_data.get('query', ''), len(selected_ids), len(res), client_ip)

        bottle.response.headers['Content-Type'] = 'text/csv'
        bottle.response.headers['Content-Disposition'] = f'attachment; filename="recoll-{sanitize_filename(qs)}.csv"'

        string_io = io.StringIO()
        writer = csv.writer(string_io)
        fields = config['csvfields'].split()
        writer.writerow(fields)
        for doc in res:
            writer.writerow([doc.get(f, '') for f in fields])
        return string_io.getvalue().strip("\r\n")

    @app.route('/export/<filename:path>')
    def serve_exported_file(filename: str):
        return bottle.static_file(filename, root=EXPORT_DIR, download=True)

    # ------------------------------------------------------------------------
    # Archiving API Endpoints
    # ------------------------------------------------------------------------

    @app.route('/api/archive/start', method=['GET', 'POST'])
    def api_archive_start():
        config = ConfigManager.get_config()
        query_data = SearchQuery.parse(config)
        query_data['page'] = 0
        query_data['snippets'] = 0
        selected_ids = _parse_selected_param()

        bottle.response.content_type = 'application/json'
        try:
            query_obj, _ = RecollSearchEngine._init_query(query_data, config)
            total_count = query_obj.rowcount
        except Exception as exc:
            logger.error("ARCHIVE_START_ERROR: %s", exc)
            return json_error(f"Failed to initialize search: {exc}", status=500)

        effective_total = len(selected_ids) if selected_ids else total_count

        if effective_total <= 0:
            return json_response({"single_file": False, "total": 0, "error": "No matching files found."})

        if not selected_ids and total_count == 1:
            return json_response({
                "single_file": True,
                "total": 1,
                "download_url": f"./download/0?{bottle.request.query_string}"
            })

        job_id = ArchiveManager.create_job(total=effective_total)
        thread = threading.Thread(target=_run_archive_worker, args=(job_id, query_data, config, selected_ids), daemon=True)
        thread.start()

        return json_response({
            "single_file": False,
            "total": effective_total,
            "job_id": job_id
        })

    @app.route('/api/archive/status/<job_id>')
    def api_archive_status(job_id: str):
        job = ArchiveManager.get_job(job_id)
        if not job:
            return json_error("Job not found", status=404)

        total = max(job.get('total', 1), 1)
        processed = min(job.get('processed', 0), total)
        status = job.get('status', 'zipping')
        percent = 100.0 if status == 'ready' else round((processed / total) * 100, 1)

        return json_response({
            "status": status,
            "processed": processed,
            "total": total,
            "percent": percent,
            "current_file": job.get('current_file', ''),
            "download_url": job.get('download_url'),
            "filename": job.get('filename'),
            "error": job.get('error')
        })

    @app.route('/api/archive/download/<job_id>')
    def api_archive_download(job_id: str):
        job = ArchiveManager.get_job(job_id)
        if not job or job.get('status') != 'ready':
            bottle.response.status = 404
            return "Archive is not ready or does not exist."

        zip_path = job.get('zip_path')
        if not zip_path or not os.path.isfile(zip_path):
            bottle.response.status = 404
            return "Archive file missing from storage."

        filename = job.get('filename') or os.path.basename(zip_path)
        file_size = os.path.getsize(zip_path)

        bottle.response.content_type = 'application/zip'
        bottle.response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        bottle.response.headers['Content-Length'] = str(file_size)
        bottle.response.headers['Vary'] = 'Cookie'

        return open(zip_path, 'rb')

    @app.route('/api/archive/cancel/<job_id>', method=['POST', 'GET'])
    def api_archive_cancel(job_id: str):
        ArchiveManager.cancel_job(job_id)
        return json_response({"status": "cancelled", "cancelled": True})

    # ------------------------------------------------------------------------
    # Search Forms REST API
    # ------------------------------------------------------------------------

    @app.route('/api/forms', method=['GET'])
    def api_get_forms():
        config = ConfigManager.get_config()
        forms = SearchFormsManager.get_forms(config['confdir'], username=config.get('current_user', 'default'))
        return json_response({'forms': forms})

    @app.route('/api/forms', method=['POST'])
    def api_save_form():
        config = ConfigManager.get_config()
        current_user = config.get('current_user', 'default')
        try:
            data = parse_json_request()
            if 'forms' in data and isinstance(data['forms'], list):
                SearchFormsManager.save_forms(config['confdir'], data['forms'], username=current_user)
                return json_response({'success': True, 'forms': SearchFormsManager.get_forms(config['confdir'], username=current_user)})
            saved_form = SearchFormsManager.save_custom_form(config['confdir'], data, username=current_user)
            return json_response({'success': True, 'form': saved_form})
        except ValueError as val_err:
            return json_error(str(val_err), status=400)
        except Exception as exc:
            return json_error(str(exc), status=500)

    @app.route('/api/forms/delete', method=['POST'])
    def api_delete_form():
        config = ConfigManager.get_config()
        current_user = config.get('current_user', 'default')
        is_admin = config.get('is_admin', False)
        try:
            data = parse_json_request()
            form_id = data.get('id')
            if not form_id:
                return json_error("Missing form ID", status=400)
            SearchFormsManager.delete_custom_form(config['confdir'], form_id, username=current_user, is_admin=is_admin)
            return json_response({'success': True})
        except ValueError as val_err:
            return json_error(str(val_err), status=400)
        except Exception as exc:
            return json_error(str(exc), status=500)

    @app.route('/api/forms/toggle', method=['POST'])
    def api_toggle_form():
        config = ConfigManager.get_config()
        current_user = config.get('current_user', 'default')
        try:
            data = parse_json_request()
            form_id = data.get('id')
            enabled = bool(data.get('enabled', True))
            if not form_id:
                return json_error("Missing form ID", status=400)
            updated_form = SearchFormsManager.toggle_form(config['confdir'], form_id, enabled, username=current_user)
            return json_response({'success': True, 'form': updated_form})
        except ValueError as val_err:
            return json_error(str(val_err), status=400)
        except Exception as exc:
            return json_error(str(exc), status=500)

    # ------------------------------------------------------------------------
    # Index Management & Metadata Rules API Endpoints
    # ------------------------------------------------------------------------

    @app.route('/index-manager')
    def index_manager_page():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return render_error_page(code=403, title="Access Forbidden", desc="Administrator privileges are required to access the Index Management interface.")

        conf_dir = config['confdir']
        status_info = IndexManager.get_status(conf_dir)
        rules_data = MetadataRulesManager.get_rules(conf_dir)
        index_config = IndexManager.get_index_config(conf_dir)

        view_vars = dict(status_info)
        view_vars['rules'] = rules_data.get('rules', [])
        view_vars['rules_json'] = json.dumps(rules_data)
        view_vars['extractor_path'] = rules_data.get('extractor_path', '')
        view_vars['index_config'] = index_config
        view_vars['index_config_json'] = json.dumps(index_config)
        return bottle.template('index_manager', **view_vars)

    @app.route('/api/index/config', method=['GET'])
    def api_get_index_config():
        """
        Return the 10 managed index configuration parameters as JSON.
        """
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        try:
            conf_data = IndexManager.get_index_config(config['confdir'])
            return json_response({'success': True, 'config': conf_data})
        except Exception as exc:
            logger.error("API_INDEX_CONFIG_GET_ERROR: %s", exc)
            return json_error(f"Failed to load index configuration: {exc}", status=500)

    @app.route('/api/index/config', method=['POST'])
    def api_save_index_config():
        """
        Validate, deduplicate, and update index configuration parameters in recoll.conf.
        """
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        try:
            data = parse_json_request()
            if not data or not isinstance(data, dict):
                return json_error("Empty or invalid JSON payload.", status=400)

            updated_config = IndexManager.update_index_config(config['confdir'], data)
            return json_response({'success': True, 'config': updated_config})
        except ValueError as val_err:
            return json_error(str(val_err), status=400)
        except Exception as exc:
            logger.error("API_INDEX_CONFIG_POST_ERROR: %s", exc)
            return json_error(f"Failed to save index configuration: {exc}", status=500)

    @app.route('/api/index/status', method=['GET'])
    def api_index_status():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        status_info = IndexManager.get_status(config['confdir'])
        return json_response(status_info)

    @app.route('/api/index/reindex', method=['POST'])
    def api_index_reindex():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        data = parse_json_request()
        full = bool(data.get('full', False))
        res = IndexManager.start_indexing(config['confdir'], full=full)
        if not res.get('success'):
            return json_error(res.get('error', 'Failed to start indexing'), status=400)
        return json_response(res)

    @app.route('/api/index/purge', method=['POST'])
    def api_index_purge():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        res = IndexManager.purge_index(config['confdir'])
        if not res.get('success'):
            return json_error(res.get('error', 'Failed to purge index'), status=500)
        return json_response(res)

    @app.route('/api/metadata/rules', method=['GET'])
    def api_get_metadata_rules():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        rules_data = MetadataRulesManager.get_rules(config['confdir'])
        return json_response(rules_data)

    @app.route('/api/metadata/rules', method=['POST'])
    def api_save_metadata_rules():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        try:
            data = parse_json_request()
            saved = MetadataRulesManager.save_rules(config['confdir'], data)
            return json_response({'success': True, 'data': saved})
        except ValueError as val_err:
            return json_error(str(val_err), status=400)
        except Exception as exc:
            logger.error("API_METADATA_SAVE_ERROR: %s", exc)
            return json_error(str(exc), status=500)

    @app.route('/api/metadata/test', method=['POST'])
    def api_test_metadata_rules():
        config = ConfigManager.get_config()
        if not config.get('is_admin', False):
            return json_error("Forbidden: Administrator privileges required.", status=403)
        try:
            data = parse_json_request()
            sample_path = data.get('sample_path', '')
            rules = data.get('rules', [])
            extracted = MetadataRulesManager.test_sample_path(sample_path, rules)
            return json_response({'success': True, 'metadata': extracted})
        except Exception as exc:
            return json_error(str(exc), status=400)

    @app.route('/api/metadata/fields', method=['GET'])
    def api_get_metadata_fields():
        """
        Return list of unique field names extracted by current rules.
        """
        try:
            config = ConfigManager.get_config()
            fields = MetadataRulesManager.get_extracted_fields(config['confdir'])
            return json_response({'success': True, 'fields': fields})
        except Exception as exc:
            logger.error("API_METADATA_FIELDS_ERROR: %s", exc)
            return json_error(str(exc), status=500)

    # ------------------------------------------------------------------------
    # Read-Only File & Folder Browser Endpoints
    # ------------------------------------------------------------------------

    @app.route('/browser')
    @app.route('/browser/')
    def browser_page():
        path = bottle.request.params.get('path', '').strip()
        try:
            data = BrowserManager.list_directory(path if path else None)
        except Exception as exc:
            logger.warning("BROWSER_PAGE_FALLBACK: Failed to load '%s': %s", path, exc)
            try:
                data = BrowserManager.list_directory(None)
                data['warning'] = f"Could not load requested path: {exc}"
            except Exception as root_exc:
                logger.error("BROWSER_PAGE_ROOT_ERROR: %s", root_exc)
                data = {
                    "success": False,
                    "current_path": "/data",
                    "breadcrumbs": [{"name": "data", "path": "/data"}],
                    "entries": [],
                    "total_entries": 0,
                    "total_dirs": 0,
                    "total_files": 0,
                    "error": str(root_exc),
                }

        config = ConfigManager.get_config()
        view_vars = dict(data)
        view_vars['title'] = " / Browser"
        view_vars['active_tab'] = "browser"
        view_vars['config'] = config
        view_vars['current_user'] = config.get('current_user', 'default')
        view_vars['is_admin'] = config.get('is_admin', False)
        view_vars['user_role'] = config.get('user_role', 'user')
        view_vars['initial_data_json'] = json.dumps(data)
        return bottle.template('browser', **view_vars)

    @app.route('/api/browser/list', method=['GET'])
    def api_browser_list():
        path = bottle.request.params.get('path', '').strip()
        try:
            res = BrowserManager.list_directory(path if path else None)
            return json_response(res)
        except PermissionError as perm_err:
            return json_error(str(perm_err), status=403)
        except FileNotFoundError as fnf_err:
            return json_error(str(fnf_err), status=404)
        except NotADirectoryError as nad_err:
            return json_error(str(nad_err), status=400)
        except Exception as exc:
            logger.error("API_BROWSER_LIST_ERROR: %s", exc)
            return json_error(str(exc), status=500)

    @app.route('/api/browser/download', method=['GET'])
    def api_browser_download():
        path = bottle.request.params.get('path', '').strip()
        is_json = 'application/json' in bottle.request.headers.get('Accept', '')

        if not path:
            if is_json:
                return json_error("The 'path' parameter is required for file download.", status=400)
            bottle.abort(400, "Missing path parameter")

        allowed, real_path = BrowserManager.is_path_allowed(path)
        if not allowed or not real_path:
            if is_json:
                return json_error("Access denied: Path is outside allowed directories.", status=403)
            bottle.abort(403, "Access denied: Path is outside allowed directories.")

        if not os.path.exists(real_path):
            if is_json:
                return json_error("The requested file does not exist.", status=404)
            bottle.abort(404, "File not found.")

        if not os.path.isfile(real_path):
            if is_json:
                return json_error("Directories cannot be downloaded directly.", status=400)
            bottle.abort(400, "Cannot download a directory.")

        filename = os.path.basename(real_path)
        return bottle.static_file(
            filename,
            root=os.path.dirname(real_path),
            download=filename,
        )

    # ------------------------------------------------------------------------
    # Settings & OpenSearch Manifest
    # ------------------------------------------------------------------------

    @app.route('/settings')
    def settings_page():
        config = ConfigManager.get_config()
        conf_dir = config['confdir']
        current_user = config.get('current_user', 'default')
        is_admin = config.get('is_admin', False)

        forms = SearchFormsManager.get_forms(conf_dir, username=current_user)
        bundle = get_all_settings_bundle(conf_dir, current_user, DEFAULT_CONFIG)

        settings_vars = dict(config)
        settings_vars['dirs'] = [d for d in config['dirs'] if d.rstrip('/') != '/data']
        settings_vars['forms'] = forms
        settings_vars['forms_json'] = json.dumps(forms)
        settings_vars['settings_bundle'] = bundle
        settings_vars['settings_bundle_json'] = json.dumps(bundle)
        settings_vars['field_status'] = bundle.get('status', {})
        settings_vars['active_tab'] = 'settings'
        return bottle.template('settings', **settings_vars)

    @app.route('/api/settings/restore', method=['POST'])
    def api_restore_setting():
        config = ConfigManager.get_config()
        conf_dir = config['confdir']
        current_user = config.get('current_user', 'default')
        data = parse_json_request()
        key = data.get('key')
        if not key:
            return json_error("Missing setting key", status=400)
        delete_user_setting(conf_dir, current_user, key)
        glob_val = get_global_setting(conf_dir, key, DEFAULT_CONFIG.get(key))
        return json_response({'success': True, 'key': key, 'global_value': glob_val})

    @app.route('/set', method=['GET', 'POST'])
    def save_settings():
        config = ConfigManager.get_config()
        conf_dir = config['confdir']
        current_user = config.get('current_user', 'default')
        is_admin = config.get('is_admin', False)

        forms_param = bottle.request.params.get('forms_json')
        if forms_param:
            try:
                parsed_forms = json.loads(forms_param)
                if isinstance(parsed_forms, list):
                    SearchFormsManager.save_forms(conf_dir, parsed_forms, username=current_user)
            except Exception as exc:
                logger.error("Error saving staged forms in /set: %s", exc)

        for key in DEFAULT_CONFIG.keys():
            val = bottle.request.params.get(key)
            scope = bottle.request.params.get(f'scope_{key}', 'user')
            restore = bottle.request.params.get(f'restore_{key}')

            if restore == '1':
                delete_user_setting(conf_dir, current_user, key)
                continue

            if val is not None:
                if key == 'csvfields':
                    from recollweb.metadata import MetadataRulesManager
                    available_keywords = set(MetadataRulesManager.get_all_known_fields(conf_dir))
                    filtered_csv = [f for f in str(val).split() if f in available_keywords]
                    val = " ".join(filtered_csv) if filtered_csv else " ".join([f for f in DEFAULT_CONFIG['csvfields'].split() if f in available_keywords])

                if is_admin and scope == 'global':
                    set_global_setting(conf_dir, key, val)
                else:
                    set_user_setting(conf_dir, current_user, key, val)

        for d in config['dirs']:
            if d.rstrip('/') == '/data':
                continue
            mount_key = f"mount_{urlquote(d, '')}"
            mount_val = bottle.request.params.get(mount_key)
            mount_scope = bottle.request.params.get(f'scope_{mount_key}', 'user')
            mount_restore = bottle.request.params.get(f'restore_{mount_key}')

            if mount_restore == '1':
                delete_user_setting(conf_dir, current_user, mount_key)
                continue

            if mount_val is not None:
                if is_admin and mount_scope == 'global':
                    set_global_setting(conf_dir, mount_key, mount_val)
                else:
                    set_user_setting(conf_dir, current_user, mount_key, mount_val)

        is_ajax = bottle.request.params.get('ajax') == '1' or 'application/json' in bottle.request.headers.get('Accept', '') or bottle.request.is_xhr
        if is_ajax:
            return json_response({'success': True})

        redirect_target = bottle.request.params.get('redirect', './settings')
        bottle.redirect(redirect_target)

    @app.route('/osd.xml')
    def opensearch_manifest():
        parts = bottle.request.urlparts
        return bottle.template('osd', url=f"{parts.scheme}://{parts.netloc}")
