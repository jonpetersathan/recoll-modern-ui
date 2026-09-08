"""
Recoll search query compilation, database interaction, and result extraction.
"""

import datetime
import hashlib
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as urlquote
import bottle
from recoll import recoll, rclextract

from recollweb.config import ConfigManager
from recollweb.constants import DOCUMENT_FIELDS, SORT_OPTIONS
from recollweb.metadata import MetadataRulesManager
from recollweb.utils import format_mimetype_label, format_timestamp


class SearchQuery:
    """
    Parses search arguments from incoming HTTP request and formats Recoll query expressions.
    """

    @staticmethod
    def parse(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract query terms, date filters, directory scope, and pagination from request.
        """
        req = bottle.request.query
        def_sort_idx = config.get('defsortidx', 0) if config else 0
        raw_dir = (req.get('dir') or '<all>').strip()
        if raw_dir.startswith('/data/'):
            raw_dir = raw_dir[len('/data/'):]
        elif raw_dir.startswith('data/'):
            raw_dir = raw_dir[len('data/'):]
        elif raw_dir in ('/data', 'data'):
            raw_dir = '<all>'

        def safe_int(value: Any, default: int) -> int:
            try:
                return int(value or default)
            except (ValueError, TypeError):
                return default

        query_data = {
            'query': req.get('query', '').strip(),
            'before': req.get('before', '').strip(),
            'after': req.get('after', '').strip(),
            'dir': raw_dir,
            'sort': req.get('sort') or SORT_OPTIONS[def_sort_idx][0],
            'ascending': safe_int(req.get('ascending', 0), 0),
            'page': safe_int(req.get('page', 1), 1),
            'highlight': safe_int(req.get('highlight', 1), 1),
            'snippets': safe_int(req.get('snippets', 1), 1),
        }
        if req.get('rcludi'):
            query_data['rcludi'] = req.get('rcludi')
        return query_data

    @staticmethod
    def to_recoll_string(query_data: Dict[str, Any]) -> str:
        """
        Build Recoll query string from search query dictionary.
        """
        qs = query_data.get('query', '')
        after = query_data.get('after', '')
        before = query_data.get('before', '')
        if after or before:
            qs += f" date:{after}/{before}"
        scope_dir = query_data.get('dir', '<all>')
        if scope_dir != '<all>':
            qs += f' dir:"{scope_dir}" '
        return qs.strip()


class SnippetHighlighter:
    """
    Wraps matched search terms in glassmorphic glowing highlight spans.
    """

    def startMatch(self, idx: int) -> str:
        """Return opening HTML tag for highlighted match term."""
        return '<span class="search-result-highlight">'

    def endMatch(self) -> str:
        """Return closing HTML tag for highlighted match term."""
        return '</span>'


def extract_document_file(doc: Any) -> Tuple[Optional[str], str, bool]:
    """
    Extract a Recoll document to a file on disk for downloading, previewing, or archiving.
    Returns a tuple of (file_path, filename, is_temporary).
    If extraction produces a temporary file, is_temporary will be True.
    If falling back to the original local file, is_temporary will be False.
    """
    fname = getattr(doc, 'filename', None)
    extracted_path = None
    is_temporary = False

    # 1. Attempt extraction via Recoll extractor
    try:
        extractor = rclextract.Extractor(doc)
        extracted_path = extractor.idoctofile(doc.ipath, doc.mimetype)
        if extracted_path and os.path.isfile(extracted_path):
            is_temporary = True
            if not fname:
                fname = os.path.basename(extracted_path)
    except Exception:
        extracted_path = None

    # 2. Fallback to local file path if extractor did not produce a valid file
    if not extracted_path or not os.path.isfile(extracted_path):
        url = getattr(doc, 'url', '')
        if url.startswith('file://'):
            local_path = urllib.request.url2pathname(urllib.parse.urlparse(url).path)
            if os.path.isfile(local_path):
                extracted_path = local_path
                is_temporary = False
                if not fname:
                    fname = os.path.basename(local_path)

    if not fname:
        fname = os.path.basename(extracted_path) if extracted_path else "document"

    return extracted_path, fname, is_temporary


class RecollSearchEngine:
    """
    Manages Recoll database connection, query execution, pagination, and result formatting.
    """

    @staticmethod
    def execute_search(query_data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int, datetime.timedelta]:
        """
        Execute search query against Recoll database and return (results_list, total_count, elapsed_time).
        """
        start_time = datetime.datetime.now()
        results: List[Dict[str, Any]] = []

        qs = SearchQuery.to_recoll_string(query_data)
        if not qs.strip() and not query_data.get('rcludi'):
            return results, 0, datetime.datetime.now() - start_time

        query_obj, _ = RecollSearchEngine._init_query(query_data, config)
        total_count = query_obj.rowcount

        rcludi = query_data.get('rcludi')
        if rcludi:
            total_count = 1
            query_data['page'] = 1

        max_res = config.get('maxresults', 0)
        if max_res > 0 and total_count > max_res:
            total_count = max_res

        per_page = config.get('perpage', 25)
        if per_page == 0:
            per_page = total_count
        page = max(query_data.get('page', 1), 1)

        offset = (page - 1) * per_page

        if query_obj.rowcount > 0:
            if isinstance(query_obj.next, int):
                query_obj.next = offset
            else:
                query_obj.scroll(offset, mode='absolute')

        highlighter = SnippetHighlighter() if query_data.get('highlight', 1) else None

        conf_dir = config.get('confdir', '')
        custom_fields = MetadataRulesManager.get_extracted_fields(conf_dir) if conf_dir else []

        while len(results) < per_page:
            try:
                doc = query_obj.fetchone()
                if not doc:
                    break
                if rcludi and getattr(doc, 'rcludi', None) != rcludi:
                    continue
            except Exception:
                break

            item: Dict[str, Any] = {}
            for field in DOCUMENT_FIELDS:
                val = getattr(doc, field, '')
                item[field] = val if val is not None else ''

            # Extract custom metadata fields
            item['custom_metadata'] = {}
            for cf in custom_fields:
                val = getattr(doc, cf, None)
                if val is None and hasattr(doc, 'get'):
                    val = doc.get(cf)
                if val:
                    val_str = str(val).strip()
                    if val_str:
                        item[cf] = val_str
                        item['custom_metadata'][cf] = val_str

            if hasattr(doc, 'keys'):
                for k in doc.keys():
                    if k not in item and k not in ('abstract', 'text'):
                        val = getattr(doc, k, None)
                        if val:
                            val_str = str(val).strip()
                            if val_str:
                                item[k] = val_str
                                item['custom_metadata'][k] = val_str

            # Omit /data/ from search results so paths start directly with folders contained in /data
            if item.get('url', '').startswith('file:///data/'):
                item['url'] = 'file:///' + item['url'][len('file:///data/'):]
            elif item.get('url', '') == 'file:///data':
                item['url'] = 'file:///'

            # Handle PDF first-match page positioning
            if getattr(doc, 'mtype', '') == 'application/pdf' and item.get('url', '').startswith('file://'):
                try:
                    pagenum, term = query_obj.getfirstmatchpage(doc)
                    if pagenum > 0:
                        item['url'] += f"#page={pagenum}&search={urlquote(term)}"
                except Exception:
                    pass

            item['label'] = item.get('title') or item.get('filename') or '?'
            item['sha'] = hashlib.sha1(f"{item.get('url', '')}{item.get('ipath', '')}".encode('utf-8')).hexdigest()
            item['time'] = format_timestamp(str(item.get('mtime', 0)), config['timefmt'])
            item['rcludi'] = getattr(doc, 'rcludi', '')
            if not item.get('filename') and item.get('url'):
                item['filename'] = os.path.basename(item['url'].split('#')[0])
            item['mtype_label'] = format_mimetype_label(item.get('mtype', ''), item.get('filename', ''))

            # Snippet abstract generation
            if query_data.get('snippets', 1):
                if highlighter:
                    item['snippet'] = query_obj.makedocabstract(doc, methods=highlighter)
                else:
                    item['snippet'] = query_obj.makedocabstract(doc)
                if not item.get('snippet'):
                    item['snippet'] = getattr(doc, 'abstract', '')

            results.append(item)
            if rcludi:
                break

        elapsed = datetime.datetime.now() - start_time
        return results, total_count, elapsed

    @staticmethod
    def _init_query(query_data: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize Recoll database connection, apply extra databases, sort order, and execute query.
        """
        conf_dir = config['confdir']
        extra_dbs: List[bytes] = []

        scope_dir = query_data.get('dir', '<all>')
        if scope_dir == '<all>':
            if config.get('extraconfdirs'):
                extra_dbs.extend(config['extradbs'])
        else:
            matching_confs = [
                conf for d, conf in config['dirs'].items()
                if os.path.commonprefix([os.path.basename(d), scope_dir]) == os.path.basename(d)
                or d.rstrip('/') == '/data'
                or os.path.exists(os.path.join(d, scope_dir))
            ]
            if not matching_confs:
                conf_dir = config['confdir']
            else:
                conf_dir = matching_confs[0]
                if len(matching_confs) > 1:
                    extra_dbs.extend([ConfigManager.resolve_db_dir(c) for c in matching_confs[1:]])

        if config.get('extradbs'):
            extra_dbs.extend(config['extradbs'])

        db = recoll.connect(conf_dir, extra_dbs=extra_dbs)

        synonyms = config.get('synonyms')
        if synonyms and synonyms != 'None':
            try:
                db.setSynonymsFile(synonyms)
            except (AttributeError, OSError):
                pass

        db.setAbstractParams(config.get('maxchars', 500), config.get('context', 30))
        query_obj = db.query()
        query_obj.sortby(query_data['sort'], query_data['ascending'])

        qs = SearchQuery.to_recoll_string(query_data)
        if config.get('queryfrag'):
            qs += f" {config['queryfrag']}"

        query_obj.execute(
            qs,
            config.get('stem', 1),
            config.get('stemlang', 'english'),
            collapseduplicates=config.get('collapsedups', 0)
        )
        return query_obj, db
