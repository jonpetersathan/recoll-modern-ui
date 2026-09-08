%import shlex, unicodedata, os, sys
%from urllib.parse import quote as urlquote
%number = (query['page'] - 1) * config['perpage'] + i + 1
%if config.get("permlinks", False):
    %if query_string.find("&rcludi=") == -1:
        %query_string += "&rcludi=" + urlquote(d.get("rcludi", ""))
    %end
%end
%url = d['url'].replace('file://', '')
%for dr, prefix in config.get('mounts', {}).items():
    %url = url.replace(dr, prefix)
%end
<div class="app-card search-result" onmousemove="updateGlow(event, this)">
    <div class="card-glow"></div>
    <div class="card-header-row">
        <div class="card-title-group">
            <div class="app-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
            <div class="card-meta-main">
                <div class="title-line">
                    <span class="result-index">#{{number}}</span>
                    <h2 class="app-title" id="r{{d['sha']}}" title="{{d.get('abstract', '')}}">
                    %if 'title_link' in config and config['title_link'] != 'download':
                        %if config['title_link'] == 'open':
                            <a href="{{url}}">{{d['label']}}</a>
                        %elif config['title_link'] == 'preview':
                            <a href="preview/{{number-1}}?{{query_string}}">{{d['label']}}</a>
                        %end
                    %else:
                        <a href="download/{{number-1}}?{{query_string}}">{{d['label']}}</a>
                    %end
                    </h2>
                    %if len(d.get('ipath', '')) > 0:
                        <span class="tag tag-ipath" title="Internal Document Path">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                            {{d['ipath']}}
                        </span>
                    %end
                    %if d.get("collapsecount", 0):
                        <span class="tag tag-dups" title="Duplicate items collapsed">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                            {{d["collapsecount"]}} duplicates
                        </span>
                    %end
                </div>
                <div class="search-result-url">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    %raw_path = d['url'].replace('file://', '')
                    %if raw_path.startswith('/data/'):
                        %raw_path = raw_path[6:]
                    %elif raw_path.startswith('/'):
                        %raw_path = raw_path[1:]
                    %end
                    %if config.get('shortenpaths', 0) and len(config.get('commonprefix', '')) > 0:
                        %if raw_path.startswith(config['commonprefix']):
                            %raw_path = raw_path[len(config['commonprefix']):].lstrip('/')
                        %end
                    %end
                    %urldir = os.path.dirname(raw_path)
                    %if len(urldir) == 0 or urldir == '.':
                        %urllabel = '/'
                    %else:
                        %urllabel = urldir
                    %end
                    <a href="{{os.path.dirname(url)}}" title="{{d['url']}}">{{urllabel}}</a>
                </div>
            </div>
        </div>

        <div class="card-header-badges">
            <div class="status-badge" title="Document Modified Date">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <span>{{d['time']}}</span>
            </div>
            %if d.get('author') and len(d['author']) > 0:
                <div class="tag" title="Author">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    <span>{{d['author']}}</span>
                </div>
            %end
        </div>
    </div>

    <div class="search-result-snippet">
        {{!d['snippet']}}
    </div>

    %if not config.get("noresultlinks", False):
    <div class="card-actions-row">
        <div class="action-buttons">
            <a href="open/{{number-1}}?{{query_string}}" target="_blank" class="action-btn" title="Open file inline in browser">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
                <span>Open</span>
            </a>
            <a href="download/{{number-1}}?{{query_string}}" class="action-btn" title="Download copy">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>Download</span>
            </a>
            <a href="preview/{{number-1}}?{{query_string}}" target="_blank" class="action-btn" title="Preview document text">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <span>Preview</span>
            </a>
            %if config.get("permlinks", False) and config.get("res_permlink", False):
                <a href="results?{{query_string}}" class="action-btn" title="Permanent direct search link">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                    </svg>
                    <span>Permlink</span>
                </a>
            %end
        </div>
    </div>
    %end
</div>
